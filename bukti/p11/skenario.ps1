<#
  Skenario P11: Prometheus, Grafana, cAdvisor, node-exporter + alarm.

  Jalankan dari folder root repo:
      powershell -ExecutionPolicy Bypass -File .\bukti\p11\skenario.ps1

  Skrip berhenti di setiap langkah yang perlu di-screenshot (terminal atau browser).
  Output tiap langkah disimpan ke bukti\p11\NN-nama.txt.
  Pakai -NoPause untuk jalan tanpa jeda.
#>
param([switch]$NoPause)

$ErrorActionPreference = 'Continue'
$Here = $PSScriptRoot
$Root = Split-Path -Parent (Split-Path -Parent $Here)
$App  = 'http://localhost:8000'
$Prom = 'http://localhost:9090'
$Graf = 'http://localhost:3000'
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
    Write-Host ">> $text" -ForegroundColor Magenta
    Read-Host '>> Setelah screenshot, tekan Enter untuk lanjut' | Out-Null
}

function Run($file, $cmd, [switch]$Append) {
    $line = "PS> $cmd"
    Write-Host $line -ForegroundColor Yellow
    $out = cmd /c "$cmd 2>&1"
    $out | ForEach-Object { Write-Host $_ }
    $text = @($line) + $out + ''
    $path = Join-Path $Here $file
    if ($Append) { $text | Out-File $path -Encoding utf8 -Append } else { $text | Out-File $path -Encoding utf8 }
}

function Note($file, $text) {
    Write-Host $text -ForegroundColor Green
    $text | Out-File (Join-Path $Here $file) -Encoding utf8 -Append
}

function Wait-Health($service, $target, $maxSeconds = 240) {
    $name = "$(cmd /c "docker compose ps -q $service 2>nul")".Trim()
    if (-not $name) { Write-Host "  Container $service tidak ditemukan." -ForegroundColor Red; exit 1 }
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt $maxSeconds) {
        $s = "$(cmd /c "docker inspect -f {{.State.Health.Status}} $name 2>nul")".Trim()
        if ($s -eq $target) { Write-Host "  $service : $s"; return }
        Start-Sleep -Seconds 3
    }
    Write-Host "  Timeout menunggu $service menjadi $target" -ForegroundColor Red
}

function Get-Json($url) {
    try { return Invoke-RestMethod -Uri $url -UseBasicParsing } catch { return $null }
}

function Alert-State($name) {
    $r = Get-Json "$Prom/api/v1/alerts"
    $a = $r.data.alerts | Where-Object { $_.labels.alertname -eq $name } | Select-Object -First 1
    if ($a) { return $a.state } else { return 'inactive' }
}

$script:Token = $null
function Login {
    try {
        $body = @{ email = 'admin@example.com'; password = 'password123' } | ConvertTo-Json
        $r = Invoke-RestMethod -Uri "$App/api/login" -Method Post -Body $body -ContentType 'application/json' -Headers @{ Accept = 'application/json' }
        $script:Token = $r.token   # hanya di memori, tidak pernah dicetak/disimpan
    } catch { }
}

# Kirim campuran request pengguna supaya panel "permintaan per detik" terisi
function Traffic($seconds) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $n = 0
    while ($sw.Elapsed.TotalSeconds -lt $seconds) {
        if ($script:Token) {
            cmd /c "curl.exe -s -o nul -H ""Accept: application/json"" -H ""Authorization: Bearer $($script:Token)"" $App/api/movies" | Out-Null
            cmd /c "curl.exe -s -o nul -H ""Accept: application/json"" -H ""Authorization: Bearer $($script:Token)"" $App/api/movies/1" | Out-Null
        }
        cmd /c "curl.exe -s -o nul -H ""Accept: application/json"" -X POST $App/api/login -d email=bukan-email" | Out-Null
        $n += 3
        Write-Progress -Activity 'Mengirim traffic ke aplikasi' -Status "$n request, $([int]$sw.Elapsed.TotalSeconds)/$seconds detik" -PercentComplete ([math]::Min(100, $sw.Elapsed.TotalSeconds / $seconds * 100))
        Start-Sleep -Milliseconds 400
    }
    Write-Progress -Activity 'Mengirim traffic ke aplikasi' -Completed
    return $n
}

# ------------------------------------------------------------------
cmd /c "docker info >nul 2>nul"
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Docker belum jalan. Buka Docker Desktop, tunggu "Engine running", lalu jalankan lagi.' -ForegroundColor Red
    exit 1
}

Header '1. docker compose up -d --build (aplikasi + 4 layanan pemantau)'
Run '01-up.txt' 'docker compose up -d --build'
foreach ($s in 'db', 'app', 'frontend', 'prometheus', 'grafana', 'cadvisor') { Wait-Health $s 'healthy' }
Run '01-ps.txt' 'docker compose ps --format "table {{.Service}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"'
Pause-Step 'SCREENSHOT 01 (terminal): docker compose ps, semua service Up dan (healthy). Simpan: 01-ps-semua-jalan.png'

# ------------------------------------------------------------------
Header '2. Target Prometheus'
Start-Sleep -Seconds 5
$t = Get-Json "$Prom/api/v1/targets"
$lines = $t.data.activeTargets | ForEach-Object { '{0,-15} {1,-22} {2}' -f $_.labels.job, $_.scrapeUrl.Replace('http://', ''), $_.health.ToUpper() }
$lines | ForEach-Object { Write-Host $_ }
(@('JOB             ENDPOINT               STATUS') + $lines) | Out-File (Join-Path $Here '02-targets.txt') -Encoding utf8
Pause-Step "SCREENSHOT 02 (browser): buka $Prom/targets , pastikan semua target UP. Simpan: 02-prometheus-targets.png"

# ------------------------------------------------------------------
Header '3. Keamanan dasar: password admin Grafana sudah diganti'
$f = '03-grafana-password.txt'
'' | Out-File (Join-Path $Here $f) -Encoding utf8
$pass = ((Get-Content .env | Where-Object { $_ -match '^GRAFANA_ADMIN_PASSWORD=' }) -replace '^GRAFANA_ADMIN_PASSWORD=', '').Trim()
$c1 = (cmd /c "curl.exe -s -o nul -w %{http_code} -u admin:admin $Graf/api/user").Trim()
Note $f "Login Grafana admin/admin                    -> HTTP $c1 (ditolak)"
$c2 = (cmd /c "curl.exe -s -o nul -w %{http_code} -u admin:$pass $Graf/api/user").Trim()
Note $f "Login Grafana admin/<GRAFANA_ADMIN_PASSWORD> -> HTTP $c2 (diterima, password tidak dicetak)"
Note $f "Panjang password: $($pass.Length) karakter; disimpan di .env yang di-ignore git"
Pause-Step 'SCREENSHOT 03 (terminal): admin/admin ditolak (401), password baru diterima (200). Simpan: 03-grafana-password.png'

# ------------------------------------------------------------------
Header '4. Traffic ke aplikasi lalu buka dashboard Grafana'
Login
$n = Traffic 120
Note '04-traffic.txt' "Traffic terkirim: $n request dalam 120 detik"
Write-Host ''
Write-Host "Buka $Graf/d/movie-app-p11 lalu login dengan user admin dan password di file .env (GRAFANA_ADMIN_PASSWORD)." -ForegroundColor Green
Pause-Step 'SCREENSHOT 04 (browser): dashboard lengkap, semua panel terisi (zoom out browser bila perlu). Simpan: 04-grafana-dashboard.png'

# ------------------------------------------------------------------
Header '5. Aturan alarm sebelum gangguan (inactive)'
Run '05-alert-sebelum.txt' "curl.exe -s $Prom/api/v1/rules?type=alert"
Write-Host "Status alarm DatabaseAplikasiTidakTerjangkau: $(Alert-State 'DatabaseAplikasiTidakTerjangkau')" -ForegroundColor Green
Pause-Step "SCREENSHOT 05 (browser): buka $Prom/alerts , alarm masih INACTIVE (hijau). Simpan: 05-alert-inactive.png"

# ------------------------------------------------------------------
Header '6. Matikan database dengan sengaja -> alarm harus FIRING'
Run '06-stop-db.txt' 'docker compose stop db'
$sw = [Diagnostics.Stopwatch]::StartNew()
do {
    Traffic 10 | Out-Null    # traffic tetap jalan supaya panel error 5xx ikut naik
    $state = Alert-State 'DatabaseAplikasiTidakTerjangkau'
    Note '06-stop-db.txt' ("[{0,3}s] DatabaseAplikasiTidakTerjangkau = {1}" -f [int]$sw.Elapsed.TotalSeconds, $state)
} until ($state -eq 'firing' -or $sw.Elapsed.TotalSeconds -gt 300)
Run '06-alerts-firing.txt' "curl.exe -s $Prom/api/v1/alerts"
Run '06-ps-db-mati.txt' 'docker compose ps -a --format "table {{.Service}}\t{{.Status}}"'
Pause-Step "SCREENSHOT 06 (browser): buka $Prom/alerts , klik alarm yang FIRING (merah) supaya anotasi tindakan_pertama terlihat. Simpan: 06-alert-firing.png"
Pause-Step "SCREENSHOT 07 (browser): refresh dashboard Grafana, panel status menunjukkan database MATI dan error 5xx naik. Simpan: 07-grafana-db-mati.png"

# ------------------------------------------------------------------
Header '7. Nyalakan database lagi -> alarm kembali normal'
Run '08-start-db.txt' 'docker compose start db'
Wait-Health 'db' 'healthy'
$sw = [Diagnostics.Stopwatch]::StartNew()
do {
    Start-Sleep -Seconds 5
    $state = Alert-State 'DatabaseAplikasiTidakTerjangkau'
} until ($state -eq 'inactive' -or $sw.Elapsed.TotalSeconds -gt 120)
Note '08-start-db.txt' "Alarm DatabaseAplikasiTidakTerjangkau kembali $state setelah ~$([int]$sw.Elapsed.TotalSeconds) detik"
Run '08-ps-pulih.txt' 'docker compose ps --format "table {{.Service}}\t{{.Status}}"'
Pause-Step "SCREENSHOT 08 (browser): buka $Prom/alerts , alarm kembali INACTIVE. Simpan: 08-alert-pulih.png"

if ($script:Token) {
    cmd /c "curl.exe -s -o nul -X POST -H ""Accept: application/json"" -H ""Authorization: Bearer $($script:Token)"" $App/api/logout" | Out-Null
}
Header 'Selesai. Output tersimpan di bukti\p11\'
Get-ChildItem $Here -Filter *.txt | Select-Object Name, Length | Format-Table -AutoSize
