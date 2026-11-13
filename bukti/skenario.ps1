<#
  Skenario P10: logging terstruktur + health check.

  Jalankan dari folder root repo:
      powershell -ExecutionPolicy Bypass -File .\bukti\skenario.ps1

  Setiap langkah:
    - menampilkan perintah + output di layar
    - menyimpan output ke bukti\NN-nama.txt
    - berhenti "Tekan Enter" supaya sempat screenshot

  Pakai -NoPause untuk jalan tanpa jeda.
  Token login hanya disimpan di variabel, TIDAK pernah ditulis ke file bukti.
#>
param([switch]$NoPause)

$ErrorActionPreference = 'Continue'
$Root  = Split-Path -Parent $PSScriptRoot
$Bukti = $PSScriptRoot
$Base  = 'http://localhost:8000'
Set-Location $Root
[Console]::OutputEncoding = [Text.Encoding]::UTF8

function Header($text) {
    Write-Host ''
    Write-Host ('=' * 70) -ForegroundColor DarkGray
    Write-Host "  $text" -ForegroundColor Cyan
    Write-Host ('=' * 70) -ForegroundColor DarkGray
}

function Pause-Step($text) {
    if ($NoPause) { return }
    Write-Host ''
    Read-Host ">> $text Silakan screenshot, lalu tekan Enter untuk lanjut" | Out-Null
}

# Menjalankan perintah lewat cmd supaya stdout+stderr tertangkap rapi,
# menampilkan di layar, dan menyimpannya ke file bukti.
function Run($file, $cmd, [switch]$Append) {
    $line = "PS> $cmd"
    Write-Host $line -ForegroundColor Yellow
    $out = cmd /c "$cmd 2>&1"
    $out | ForEach-Object { Write-Host $_ }
    $text = @($line) + $out + ''
    if ($Append) { $text | Out-File -FilePath (Join-Path $Bukti $file) -Encoding utf8 -Append }
    else         { $text | Out-File -FilePath (Join-Path $Bukti $file) -Encoding utf8 }
}

function Note($file, $text) {
    Write-Host $text -ForegroundColor Green
    $text | Out-File -FilePath (Join-Path $Bukti $file) -Encoding utf8 -Append
}

function Wait-Health($service, $target, $maxSeconds = 180) {
    $name = (cmd /c "docker compose ps -q $service").Trim()
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt $maxSeconds) {
        $s = (cmd /c "docker inspect -f {{.State.Health.Status}} $name 2>nul").Trim()
        Write-Host ("  [{0,3}s] {1}: {2}" -f [int]$sw.Elapsed.TotalSeconds, $service, $s)
        if ($s -eq $target) { return [int]$sw.Elapsed.TotalSeconds }
        Start-Sleep -Seconds 3
    }
    Write-Host "  Timeout menunggu $service menjadi $target" -ForegroundColor Red
    return -1
}

# Kirim request JSON, kembalikan status code + body (tanpa melempar exception)
function Send($method, $path, $body = $null, $token = $null) {
    $headers = @{ Accept = 'application/json' }
    if ($token) { $headers.Authorization = "Bearer $token" }
    $params = @{ Uri = "$Base$path"; Method = $method; Headers = $headers; UseBasicParsing = $true }
    if ($body) { $params.Body = ($body | ConvertTo-Json); $params.ContentType = 'application/json' }
    try {
        $r = Invoke-WebRequest @params
        return @{ Code = [int]$r.StatusCode; Body = $r.Content }
    } catch {
        $resp = $_.Exception.Response
        if ($resp) {
            $reader = New-Object IO.StreamReader($resp.GetResponseStream())
            return @{ Code = [int]$resp.StatusCode; Body = $reader.ReadToEnd() }
        }
        return @{ Code = 0; Body = $_.Exception.Message }
    }
}

# ------------------------------------------------------------------
Header '1. docker compose up -d --build'
Run '01-up-build.txt' 'docker compose up -d --build'
Note '01-up-build.txt' 'Menunggu service app menjadi healthy...'
$t = Wait-Health 'app' 'healthy'
Note '01-up-build.txt' "app healthy setelah ~$t detik"
Wait-Health 'frontend' 'healthy' | Out-Null

Header '2. docker compose ps (semua healthy)'
Run '02-ps-sehat.txt' 'docker compose ps'
Pause-Step 'Langkah 2: semua service (healthy).'

Header '2b. Bukti log tidak ditulis ke file di container'
Run '02b-log-ke-stderr.txt' 'docker compose exec -T app printenv LOG_CHANNEL LOG_STDERR_FORMATTER'
Run '02b-log-ke-stderr.txt' 'docker compose exec -T app ls -la storage/logs /var/log/apache2' -Append

Header '2c. Bukti pembatasan ukuran log (json-file, max-size, max-file)'
foreach ($svc in 'db', 'app', 'frontend') {
    $id = (cmd /c "docker compose ps -q $svc").Trim()
    Run '02c-log-limit.txt' "docker inspect -f ""$svc {{json .HostConfig.LogConfig}}"" $id" -Append
}
Pause-Step 'Langkah 2c: LogConfig json-file max-size 10m max-file 3.'

# ------------------------------------------------------------------
Header '3. curl -i /health (sehat)'
Run '03-health-sehat.txt' "curl.exe -s -i $Base/health"
Pause-Step 'Langkah 3: /health 200 OK.'

# ------------------------------------------------------------------
Header '4. Picu log terstruktur'
$f = '04-picu-log.txt'
'' | Out-File (Join-Path $Bukti $f) -Encoding utf8
$since = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

# (a) WARNING: validasi login gagal (password kosong)
$r = Send 'POST' '/api/login' @{ email = 'bukan-email'; password = '' }
Note $f "[WARNING] POST /api/login dengan input tidak valid -> HTTP $($r.Code)"

# login sungguhan untuk dapat token (token TIDAK dicetak/disimpan)
$r = Send 'POST' '/api/login' @{ email = 'admin@example.com'; password = 'password123' }
$token = ($r.Body | ConvertFrom-Json).token
Note $f "Login admin -> HTTP $($r.Code) (token disimpan di memori saja)"

# (b) WARNING: validasi data film gagal
$r = Send 'POST' '/api/movies' @{ title = ''; director = 'X'; genre = 'Drama'; release_year = 1500; rating = 99 } $token
Note $f "[WARNING] POST /api/movies dengan data tidak valid -> HTTP $($r.Code)"

# (c) INFO: simpan data film
$r = Send 'POST' '/api/movies' @{ title = 'Film Uji P10'; director = 'Sutradara Uji'; genre = 'Drama'; release_year = 2024; rating = 7.5; synopsis = 'Data uji logging P10.' } $token
$movieId = ($r.Body | ConvertFrom-Json).data.id
Note $f "[INFO] POST /api/movies (simpan) -> HTTP $($r.Code), id=$movieId"

# (d) INFO: ubah data film
$r = Send 'PUT' "/api/movies/$movieId" @{ rating = 8.0 } $token
Note $f "[INFO] PUT /api/movies/$movieId (ubah rating) -> HTTP $($r.Code)"

Note $f '(Log ERROR gagal konek DB dipicu di langkah 5, saat DB dimatikan.)'
Start-Sleep -Seconds 1

Header '4b. docker compose logs app'
Run '05-logs-app-sehat.txt' "docker compose logs app --since $since"
Pause-Step 'Langkah 4: log terstruktur INFO & WARNING di docker compose logs app.'

# ------------------------------------------------------------------
Header '5. docker compose stop db'
Run '06-stop-db.txt' 'docker compose stop db'
$since = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
Note '06-stop-db.txt' 'Menunggu service app menjadi unhealthy...'
$t = Wait-Health 'app' 'unhealthy' 120
Note '06-stop-db.txt' "app unhealthy setelah ~$t detik"

# (e) ERROR: request API saat DB mati
$r = Send 'GET' '/api/movies' $null $token
Note '06-stop-db.txt' "[ERROR] GET /api/movies saat DB mati -> HTTP $($r.Code)"

Header '5b. docker compose ps (sakit)'
Run '07-ps-sakit.txt' 'docker compose ps -a'
Pause-Step 'Langkah 5: db mati, app (unhealthy).'

Header '5c. curl -i /health (sakit)'
Run '08-health-sakit.txt' "curl.exe -s -i $Base/health"
Pause-Step 'Langkah 5: /health 503 dan menyebut komponen database.'

Header '5d. docker compose logs app (log ERROR)'
Run '09-logs-app-sakit.txt' "docker compose logs app --since $since"
Pause-Step 'Langkah 5: log ERROR gagal konek DB.'

# ------------------------------------------------------------------
Header '6. docker compose start db'
Run '10-start-db.txt' 'docker compose start db'
Wait-Health 'db' 'healthy' | Out-Null
$t = Wait-Health 'app' 'healthy'
Note '10-start-db.txt' "app kembali healthy setelah ~$t detik"

Header '6b. docker compose ps (sehat lagi)'
Run '11-ps-pulih.txt' 'docker compose ps'
Run '11-ps-pulih.txt' "curl.exe -s -i $Base/health" -Append
Pause-Step 'Langkah 6: semua service healthy lagi.'

# Bersihkan data uji
if ($movieId) { Send 'DELETE' "/api/movies/$movieId" $null $token | Out-Null }
Send 'POST' '/api/logout' $null $token | Out-Null

Header 'Selesai. Semua output tersimpan di folder bukti\'
Get-ChildItem $Bukti -Filter *.txt | Select-Object Name, Length | Format-Table -AutoSize
