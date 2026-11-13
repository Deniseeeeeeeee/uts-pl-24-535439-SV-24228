"""
Generator laporan P10 (PDF).

Membaca output skenario di bukti/*.txt, cuplikan compose.yaml, dan gambar di
screenshots/ (kalau ada), menyusunnya jadi HTML, lalu mencetaknya ke PDF lewat
Microsoft Edge / Google Chrome mode headless.

Jalankan dari root repo:
    python laporan/buat_laporan.py
"""

import datetime
import html
import json
import re
import subprocess
import sys
from pathlib import Path

NAMA = "Denise Aditya"
NIM = "24/535439/SV/24228"
JUDUL = "Praktikum P10 — Logging Terstruktur & Health Check pada Docker Compose"

ROOT = Path(__file__).resolve().parent.parent
BUKTI = ROOT / "bukti"
SHOTS = ROOT / "screenshots"
OUT_DIR = ROOT / "laporan"
PDF_NAME = f"P10_{NIM.replace('/', '-')}_{NAMA.replace(' ', '_')}.pdf"

BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]


# ---------------------------------------------------------------- helpers
def read(name: str) -> str:
    p = BUKTI / name
    if not p.exists():
        return f"(file {name} belum ada — jalankan bukti/skenario.ps1 dulu)"
    return p.read_text(encoding="utf-8-sig").rstrip()


def pre(text: str, cls: str = "") -> str:
    return f'<pre class="{cls}">{html.escape(text)}</pre>'


def compose_block(start: str, stop_pattern: str) -> str:
    """Ambil potongan compose.yaml dari baris `start` sampai sebelum baris yang cocok stop_pattern."""
    lines = (ROOT / "compose.yaml").read_text(encoding="utf-8").splitlines()
    out, on = [], False
    for ln in lines:
        if not on and ln.strip().startswith(start):
            on = True
        elif on and re.match(stop_pattern, ln):
            break
        if on:
            out.append(ln)
    return "\n".join(out).rstrip()


def service_block(service: str, key: str) -> str:
    """Ambil blok `key:` (beserta isi & komentar di atasnya) di dalam service tertentu."""
    lines = (ROOT / "compose.yaml").read_text(encoding="utf-8").splitlines()
    in_svc, out, comments = False, [], []
    for i, ln in enumerate(lines):
        if re.match(rf"^  {service}:\s*$", ln):
            in_svc = True
            continue
        if in_svc and re.match(r"^  [a-z]", ln):
            break
        if not in_svc:
            continue
        if re.match(r"^    #", ln):
            comments.append(ln)
            continue
        if re.match(rf"^    {key}:", ln):
            out = comments + [ln]
            for nxt in lines[i + 1:]:
                if re.match(r"^      ", nxt):
                    out.append(nxt)
                else:
                    break
            break
        comments = []
    return f"  {service}:\n" + "\n".join(out)


def json_logs(*files: str) -> list[dict]:
    logs = []
    for f in files:
        for ln in read(f).splitlines():
            m = re.search(r"\|\s*(\{.*\})\s*$", ln)
            if m:
                try:
                    logs.append(json.loads(m.group(1)))
                except json.JSONDecodeError:
                    pass
    return logs


def first(logs, level, action_prefix):
    for log in logs:
        ctx = log.get("context", {})
        if log.get("level_name") == level and str(ctx.get("action", "")).startswith(action_prefix):
            return log
    return None


def http_body(text: str) -> str:
    """Pisahkan header & body dari output curl -i, body di-pretty-print."""
    if "\n\n" not in text:
        return text
    head, body = text.split("\n\n", 1)
    try:
        body = json.dumps(json.loads(body.strip()), indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        pass
    return head + "\n\n" + body


# ---------------------------------------------------------------- isi
logs = json_logs("05-logs-app-sehat.txt", "09-logs-app-sakit.txt")
contoh = [
    ("INFO", "Simpan data film", first(logs, "INFO", "movie.store")),
    ("INFO", "Ubah data film", first(logs, "INFO", "movie.update")),
    ("WARNING", "Validasi login gagal", first(logs, "WARNING", "POST api/login")),
    ("WARNING", "Validasi data film gagal", first(logs, "WARNING", "movies.store")),
    ("ERROR", "Gagal konek DB (request API)", first(logs, "ERROR", "movies.")),
    ("ERROR", "Gagal konek DB (health check)", first(logs, "ERROR", "health.")),
]

log_html = ""
for level, judul, log in contoh:
    if not log:
        continue
    log_html += (
        f'<h4><span class="lvl {level.lower()}">{level}</span> {html.escape(judul)}</h4>'
        + pre(json.dumps(log, indent=2, ensure_ascii=False), "json")
    )

shots = sorted(
    [p for p in SHOTS.glob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
) if SHOTS.exists() else []
if shots:
    shots_html = "".join(
        f'<figure><img src="{p.as_uri()}"><figcaption>Gambar {i}. {html.escape(p.stem.replace("_", " ").replace("-", " "))}</figcaption></figure>'
        for i, p in enumerate(shots, 1)
    )
else:
    shots_html = '<p class="muted">Folder <code>screenshots/</code> belum berisi gambar. Taruh screenshot di folder itu lalu jalankan ulang <code>python laporan/buat_laporan.py</code>.</p>'

today = datetime.date.today().strftime("%d-%m-%Y")

HTML = f"""<!doctype html>
<html lang="id"><head><meta charset="utf-8"><title>{html.escape(PDF_NAME)}</title>
<style>
  @page {{ size: A4; margin: 18mm 16mm; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 10.5pt; color: #1b1f27; line-height: 1.5; }}
  h1 {{ font-size: 17pt; margin: 0 0 4px; }}
  h2 {{ font-size: 13pt; margin: 22px 0 8px; padding-bottom: 4px; border-bottom: 2px solid #e50914; break-after: avoid; }}
  h3 {{ font-size: 11pt; margin: 14px 0 6px; break-after: avoid; }}
  h4 {{ font-size: 10pt; margin: 12px 0 4px; break-after: avoid; }}
  .cover {{ border-left: 5px solid #e50914; padding: 6px 0 6px 14px; margin-bottom: 18px; }}
  .cover table td {{ padding: 1px 12px 1px 0; }}
  pre {{ background: #f4f5f7; border: 1px solid #e1e4ea; border-radius: 6px; padding: 8px 10px;
        font: 8pt/1.4 Consolas, 'Courier New', monospace; white-space: pre-wrap; word-break: break-all;
        margin: 4px 0 10px; }}
  pre.json {{ background: #0f1420; color: #d7e0f0; border-color: #0f1420; }}
  table.t {{ width: 100%; border-collapse: collapse; margin: 6px 0 12px; font-size: 9.5pt; }}
  table.t th, table.t td {{ border: 1px solid #d9dde4; padding: 5px 7px; vertical-align: top; text-align: left; }}
  table.t th {{ background: #f0f2f5; }}
  .lvl {{ display: inline-block; padding: 1px 7px; border-radius: 4px; color: #fff; font-size: 8pt; font-weight: 700; }}
  .lvl.info {{ background: #2563eb; }} .lvl.warning {{ background: #d97706; }} .lvl.error {{ background: #dc2626; }}
  code {{ font-family: Consolas, monospace; background: #f0f2f5; padding: 0 3px; border-radius: 3px; }}
  .muted {{ color: #6b7280; }}
  figure {{ margin: 10px 0 16px; break-inside: avoid; }}
  figure img {{ max-width: 100%; border: 1px solid #d9dde4; border-radius: 4px; }}
  figcaption {{ font-size: 9pt; color: #555; margin-top: 3px; }}
  .avoid {{ break-inside: avoid; }}
</style></head><body>

<div class="cover">
  <h1>{html.escape(JUDUL)}</h1>
  <table>
    <tr><td>Nama</td><td>: {html.escape(NAMA)}</td></tr>
    <tr><td>NIM</td><td>: {html.escape(NIM)}</td></tr>
    <tr><td>Tanggal</td><td>: {today}</td></tr>
    <tr><td>Branch</td><td>: <code>feature/p10-logging-health</code></td></tr>
  </table>
</div>

<h2>1. Ringkasan Perubahan</h2>
<table class="t">
  <tr><th style="width:28%">Tugas</th><th>Implementasi</th></tr>
  <tr><td>Log ke stdout/stderr</td><td><code>LOG_CHANNEL=stderr</code> + <code>LOG_STDERR_FORMATTER=Monolog\\Formatter\\JsonFormatter</code> di <code>compose.yaml</code>. Tidak ada file di <code>storage/logs</code>.</td></tr>
  <tr><td>Log terstruktur</td><td><code>MovieController</code> (INFO), <code>Handler::invalidJson</code> (WARNING), <code>Handler</code> reportable + <code>HealthController</code> (ERROR). Context dibuat oleh <code>App\\Support\\LogContext</code>.</td></tr>
  <tr><td>GET /health</td><td><code>HealthController</code>: <code>SELECT 1</code> ke DB dan put/get/forget cache, tiap cek dalam try/catch; 200 atau 503 + <code>failed</code>.</td></tr>
  <tr><td>Healthcheck compose</td><td>Service <code>app</code> memakai <code>curl</code> (ditambahkan ke image), <code>frontend</code> memakai <code>wget</code>, <code>db</code> memakai <code>mysqladmin ping</code>.</td></tr>
  <tr><td>Logging driver</td><td><code>json-file</code>, <code>max-size: 10m</code>, <code>max-file: 3</code> untuk semua service (YAML anchor).</td></tr>
</table>

<h2>2. Log Laravel ke stdout/stderr</h2>
<p>Image backend memakai <b>php:8.2-apache (mod_php)</b>, bukan php-fpm. Pada mod_php, PHP berjalan di dalam proses Apache sehingga
<code>php://stderr</code> langsung menjadi stderr container. Pada php-fpm hal ini tidak otomatis: output worker dibuang kecuali
<code>catch_workers_output = yes</code> dan <code>error_log = /proc/self/fd/2</code> diaktifkan. Di image ini juga <code>error.log</code> Apache sudah
diarahkan ke <code>/dev/stderr</code>. Bukti: variabel log aktif dan folder <code>storage/logs</code> kosong.</p>
{pre(read("02b-log-ke-stderr.txt"))}

<h2>3. Potongan Log Terstruktur</h2>
<p>Semua log berformat JSON dengan <code>context</code> berisi <b>siapa</b> (<code>user_id</code>, <code>ip</code>), <b>aksi</b> (<code>action</code>, <code>method</code>, <code>path</code>)
dan <b>sebab</b> (<code>reason</code>). Email, nama, password, token, dan isi data tidak pernah dicatat.</p>
{log_html}

<h3>Alasan memilih alur yang diberi log</h3>
<table class="t avoid">
  <tr><th style="width:17%">Level</th><th style="width:25%">Alur</th><th>Alasan</th></tr>
  <tr><td><span class="lvl info">INFO</span></td><td>Simpan / ubah / hapus film</td>
      <td>Operasi yang mengubah data. Log menjadi jejak audit: siapa (user_id) mengubah film mana (movie_id) dan field apa saja, sehingga perubahan atau kehilangan data bisa ditelusuri. Isi data tidak dicatat, cukup id dan nama field.</td></tr>
  <tr><td><span class="lvl warning">WARNING</span></td><td>Validasi input gagal (login & film)</td>
      <td>Bukan kesalahan server, tetapi sinyal yang perlu diawasi: lonjakan di <code>/api/login</code> bisa berarti percobaan brute force, dan lonjakan di <code>/api/movies</code> bisa berarti bug di frontend. Yang dicatat hanya nama field dan rule yang gagal, bukan nilainya, karena nilai bisa berisi password atau email.</td></tr>
  <tr><td><span class="lvl error">ERROR</span></td><td>Gagal konek ke database</td>
      <td>Penyebab paling umum seluruh API gagal (HTTP 500). Harus langsung terlihat dan bisa dikaitkan dengan status <i>unhealthy</i>. Pesan <code>QueryException</code> sengaja tidak dicatat karena memuat SQL beserta binding (misalnya email saat login); yang dicatat hanya pesan PDO, misalnya <code>getaddrinfo for db failed</code>.</td></tr>
</table>

<h2>4. docker compose ps</h2>
<h3>Keadaan sehat</h3>
{pre(read("02-ps-sehat.txt"))}
<h3>Keadaan sakit (setelah <code>docker compose stop db</code>)</h3>
{pre(read("06-stop-db.txt"))}
{pre(read("07-ps-sakit.txt"))}
<h3>Pulih (setelah <code>docker compose start db</code>)</h3>
{pre(read("10-start-db.txt"))}
{pre(read("11-ps-pulih.txt").split("PS> curl")[0].rstrip())}

<h2>5. Balasan GET /health</h2>
<h3>Sehat — HTTP 200</h3>
{pre(http_body(read("03-health-sehat.txt")))}
<h3>Sakit — HTTP 503 (DB mati, endpoint tidak crash)</h3>
{pre(http_body(read("08-health-sakit.txt")))}
<p>Catatan: saat DB dimatikan, nama host <code>db</code> hilang dari DNS Docker sehingga lookup DNS memakan waktu ~5 detik (sudah dipangkas dari ~15 detik
dengan <code>dns_opt timeout:1 attempts:1</code> dan <code>PDO::ATTR_TIMEOUT=3</code>). Karena itu batas <code>curl --max-time</code> di healthcheck dibuat 8 detik.</p>

<h2>6. Cuplikan compose.yaml</h2>
<h3>Logging driver (json-file + rotasi)</h3>
{pre(compose_block("x-logging", r"^services:"))}
<h3>Healthcheck service app</h3>
{pre(service_block("app", "healthcheck"))}
<h3>Healthcheck service frontend & db</h3>
{pre(service_block("frontend", "healthcheck"))}
{pre(service_block("db", "healthcheck"))}
<h3>Variabel log service app</h3>
{pre(chr(10).join(l for l in (ROOT / "compose.yaml").read_text(encoding="utf-8").splitlines() if "LOG_" in l or "P10: log" in l or "dalam format JSON" in l))}

<h2>7. Screenshot</h2>
{shots_html}

<h2>8. Kesimpulan</h2>
<p>Log aplikasi kini keluar ke stderr dalam format JSON sehingga bisa dibaca lewat <code>docker compose logs app</code> dan dirotasi oleh driver
<code>json-file</code> (maks 3 × 10 MB per service). Endpoint <code>/health</code> benar-benar memeriksa DB dan cache, membalas 503 dengan komponen yang gagal
tanpa crash, dan dipakai Docker sebagai healthcheck sehingga status container berubah menjadi <i>unhealthy</i> saat DB mati lalu kembali <i>healthy</i>
otomatis setelah DB dinyalakan.</p>

</body></html>
"""

# ---------------------------------------------------------------- tulis & cetak
OUT_DIR.mkdir(exist_ok=True)
html_path = OUT_DIR / "laporan.html"
html_path.write_text(HTML, encoding="utf-8")
pdf_path = OUT_DIR / PDF_NAME

browser = next((b for b in BROWSERS if Path(b).exists()), None)
if not browser:
    sys.exit(f"Edge/Chrome tidak ditemukan. Buka {html_path} di browser lalu Print -> Save as PDF.")

subprocess.run(
    [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--allow-file-access-from-files",
        f"--print-to-pdf={pdf_path}",
        html_path.as_uri(),
    ],
    check=True,
    capture_output=True,
)
print(f"PDF dibuat: {pdf_path}")
print(f"Screenshot dimasukkan: {len(shots)}")
