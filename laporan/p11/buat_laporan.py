"""
Generator laporan praktikum P11 (PDF): Pemantauan dengan Prometheus & Grafana.

Format sama dengan laporan P10: cover, lalu setiap screenshot diikuti
paragraf keterangan. Angka (detik alarm berbunyi, jumlah request, dll.)
dibaca dari output skenario di bukti/p11/.

Jalankan dari root repo setelah screenshot ada di screenshots/p11/:
    python laporan/p11/buat_laporan.py
"""

import html
import re
import subprocess
import sys
from pathlib import Path

NAMA = "Denise Aditya"
NIM = "24/535439/SV/24228"
KELAS = "PL5A1"
DOSEN = "Galih Malela Darmaji"
MATKUL = "KONSTRUKSI DAN EVOLUSI PERANGKAT LUNAK"
PERTEMUAN = "PERTEMUAN 11"
TOPIK = "PEMANTAUAN DENGAN PROMETHEUS &amp; GRAFANA"
TAHUN = "2026"

ROOT = Path(__file__).resolve().parents[2]
BUKTI = ROOT / "bukti" / "p11"
SHOTS = ROOT / "screenshots" / "p11"
OUT_DIR = Path(__file__).resolve().parent
LOGO = ROOT / "laporan" / "logo-ugm.png"
PDF_NAME = "P11_535439_DeniseAditya.pdf"

BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]


# ---------------------------------------------------------------- angka dari bukti
def read(name: str) -> str:
    p = BUKTI / name
    return p.read_text(encoding="utf-8-sig") if p.exists() else ""


def first_sec(text: str, state: str, default: str = "?") -> str:
    m = re.search(rf"\[\s*(\d+)s\] \S+ = {state}", text)
    return m.group(1) if m else default


stop = read("06-stop-db.txt")
N = {
    "up": str(len(re.findall(r"\bUP\s*$", read("02-targets.txt"), re.M))) or "5",
    "traffic": (re.search(r"(\d+) request", read("04-traffic.txt")) or [None, "?"])[1],
    "pending": first_sec(stop, "pending"),
    "firing": first_sec(stop, "firing"),
    "pulih": (re.search(r"kembali \w+ setelah ~(\d+) detik", read("08-start-db.txt")) or [None, "?"])[1],
}

# ---------------------------------------------------------------- isi
# (nama file screenshot di screenshots/p11/, paragraf keterangan)
ISI = [
    ("09-compose-pemantauan", f"""
Empat layanan pemantau, yaitu prometheus, grafana, cadvisor, dan node-exporter, ditambahkan ke
<i>compose.yaml</i> yang sama dengan aplikasi. Versi image dikunci pada tag tertentu
(prom/prometheus:v3.5.0, grafana/grafana:12.1.1, gcr.io/cadvisor/cadvisor:v0.54.1, dan
prom/node-exporter:v1.9.1), bukan latest, sehingga hasil build selalu sama. Data Prometheus dan Grafana
disimpan di named volume <i>prometheus_data</i> dan <i>grafana_data</i>, sehingga riwayat metrik dan
pengaturan Grafana tetap ada walaupun container dibuat ulang. cAdvisor sengaja memakai v0.54.1 karena
v0.52.1 tidak dapat membaca container pada Docker Desktop yang memakai <i>containerd snapshotter</i>.
Port pemantauan hanya dibuka ke 127.0.0.1 supaya tidak dapat diakses dari jaringan luar.
"""),
    ("01-ps-semua-jalan", f"""
Setelah <i>docker compose up -d --build</i>, perintah <i>docker compose ps</i> menampilkan tujuh service:
tiga service aplikasi (app, db, frontend) dan empat service pemantau. Semua berstatus Up, dan service
yang memiliki healthcheck berstatus (healthy). Kolom PORTS menunjukkan Prometheus (9090), Grafana (3000),
dan cAdvisor (8081) hanya terbuka di 127.0.0.1.
"""),
    ("02-prometheus-targets", f"""
Halaman /targets di Prometheus menampilkan {N['up']} target berstatus UP: prometheus, movie-app,
cadvisor, node-exporter, dan grafana. Target movie-app adalah endpoint <i>GET /metrics</i> yang
ditambahkan ke aplikasi Laravel. Endpoint itu berisi jumlah request per route dan status, histogram
waktu respons, jumlah film, serta app_dependency_up yang memeriksa database dan cache secara langsung.
Penghitung request disimpan di APCu, yaitu memori bersama antar proses Apache, karena PHP tidak
menyimpan data antar request. Semua target dipanggil memakai nama service di jaringan Docker Compose.
"""),
    ("04-grafana-dashboard", f"""
Dashboard “Movie App — Kesehatan &amp; Kinerja” disusun sendiri dan dimuat otomatis dari
<i>monitoring/grafana/dashboards/movie-app.json</i>. Dashboard ini berisi delapan panel yang judulnya
ditulis sebagai pertanyaan: apakah semua layanan sedang hidup, berapa film di katalog, berapa permintaan
per detik yang dilayani aplikasi, berapa persen permintaan yang berakhir error 5xx, container mana yang
paling banyak memakai CPU, berapa memori yang dipakai tiap container, seberapa lambat respons API untuk
95% permintaan, dan seberapa sibuk mesin host. Setiap sumbu diberi satuan (req/s, persen, MiB, detik)
beserta label sumbu. Metrik penghitung dibungkus <i>rate(...[5m])</i> agar yang tampil adalah laju,
bukan garis yang terus naik. Sebelum screenshot diambil, skenario mengirim {N['traffic']} request ke
aplikasi agar panel permintaan terisi.
"""),
    ("10-alerts-yml", """
Aturan alarm ditulis di <i>monitoring/prometheus/alerts.yml</i>. Aturan utama,
DatabaseAplikasiTidakTerjangkau, berbunyi ketika app_dependency_up{component="database"} bernilai 0.
Klausa <i>for: 1m</i> membuat alarm baru berbunyi setelah kondisi bertahan satu menit, sehingga
gangguan sesaat tidak langsung membangunkan orang. Anotasi <i>tindakan_pertama</i> menjelaskan langkah
pertama bagi penerima alarm: menjalankan docker compose ps db, menyalakan db bila berhenti, lalu
memastikan /health kembali 200. Aturan kedua, TargetPemantauanMati (up == 0), menjaga semua target
lainnya.
"""),
    ("05-alert-inactive", """
Sebelum gangguan dibuat, halaman Alerts di Prometheus menampilkan kedua aturan alarm dalam keadaan
INACTIVE. Artinya aturan sudah dimuat dan dievaluasi setiap 15 detik, tetapi kondisinya belum
terpenuhi.
"""),
    ("06-alert-firing", f"""
Layanan db kemudian dimatikan dengan sengaja memakai <i>docker compose stop db</i>, sementara skenario
tetap mengirim traffic. Alarm DatabaseAplikasiTidakTerjangkau berubah menjadi PENDING sekitar
{N['pending']} detik setelah db dimatikan, yaitu ketika scrape pertama melaporkan
app_dependency_up = 0. Setelah kondisi bertahan selama <i>for: 1m</i>, alarm berubah menjadi FIRING
sekitar detik ke-{N['firing']}. Halaman Alerts menampilkan label alarm (severity critical,
service db, instance app:80) beserta anotasi summary, description, dan tindakan_pertama.
"""),
    ("07-grafana-db-mati", """
Pada saat yang sama, dashboard Grafana menunjukkan dampak gangguan dari sisi aplikasi. Panel status
menampilkan database (dicek app) dalam keadaan MATI, sementara service lain tetap HIDUP. Panel
persentase error 5xx naik karena request ke /api/movies dibalas HTTP 500. Panel waktu respons p95 juga
meningkat karena setiap request menunggu koneksi database yang gagal.
Panel jumlah film menampilkan <i>No data</i> secara sengaja: saat database tidak terjangkau,
endpoint /metrics tidak mengirim app_movies_total sehingga tidak muncul angka 0 yang menyesatkan.
"""),
    ("08-alert-pulih", f"""
Setelah db dinyalakan kembali dengan <i>docker compose start db</i>, scrape berikutnya melaporkan
app_dependency_up = 1. Alarm kembali INACTIVE sekitar {N['pulih']} detik setelah db healthy, tanpa perlu
me-restart aplikasi maupun Prometheus. Rangkaian INACTIVE, PENDING, FIRING, lalu INACTIVE ini
membuktikan alarm benar-benar berbunyi saat layanan mati dan berhenti saat layanan pulih.
"""),
    ("03-grafana-password", """
Password admin Grafana diganti dari bawaan admin/admin menjadi password acak 24 karakter. Password itu
diisi melalui variabel GRAFANA_ADMIN_PASSWORD di file .env, yang tidak ikut di-commit karena tercantum
di .gitignore. compose.yaml memakai sintaks <i>${GRAFANA_ADMIN_PASSWORD:?...}</i>, sehingga
<i>docker compose up</i> berhenti dengan error bila password belum diisi, dan Grafana tidak pernah
berjalan dengan admin/admin. Pendaftaran pengguna baru dan akses anonim juga dimatikan. Hasil uji
menunjukkan login admin/admin ditolak dengan HTTP 401, sedangkan password baru diterima dengan HTTP 200.
Penggantian ini penting karena admin/admin adalah kredensial bawaan yang diketahui semua orang dan
menjadi sasaran pertama pemindaian otomatis. Admin Grafana dapat melihat seluruh metrik, mengubah
dashboard, serta menambah datasource dan pengguna, sehingga satu kredensial bawaan yang bocor
membuka akses penuh ke sistem pemantauan.
"""),
]

PENUTUP = """
Seluruh berkas yang diminta sudah di-commit: <i>compose.yaml</i>,
<i>monitoring/prometheus/prometheus.yml</i>, <i>monitoring/prometheus/alerts.yml</i>, dan ekspor JSON
dashboard <i>monitoring/grafana/dashboards/movie-app.json</i>. Endpoint /metrics di aplikasi juga
di-commit beserta test-nya. Output setiap langkah pengujian tersimpan di folder bukti/p11, dan
screenshot di folder screenshots/p11.
"""


def find_shot(stem: str):
    for ext in ("png", "jpg", "jpeg", "webp"):
        hits = sorted(SHOTS.glob(f"{stem}*.{ext}"))
        if hits:
            return hits
    return []


blocks = []
for stem, text in ISI:
    imgs = find_shot(stem)
    figs = "".join(f'<img src="{p.as_uri()}">' for p in imgs) or (
        f'<p class="missing">[Screenshot {stem}.png belum ada di folder screenshots/p11/]</p>'
    )
    blocks.append(f'<section class="item"><div class="fig">{figs}</div><p>{" ".join(text.split())}</p></section>')

HTML = f"""<!doctype html>
<html lang="id"><head><meta charset="utf-8"><title>{html.escape(PDF_NAME)}</title>
<style>
  @page {{ size: Letter; margin: 1in; }}
  body {{ font-family: 'Times New Roman', Times, serif; font-size: 12pt; color: #000; margin: 0; }}
  p {{ line-height: 1.5; text-align: justify; margin: 0 0 12pt; }}
  .cover {{ height: 9in; display: flex; flex-direction: column; align-items: center; text-align: center;
           page-break-after: always; }}
  .cover .judul {{ font-weight: bold; font-size: 14pt; line-height: 1.6; margin-top: 0.1in; }}
  .cover .topik {{ font-weight: bold; font-size: 12pt; margin-top: 4pt; }}
  .cover img {{ width: 1.95in; margin: 0.35in 0 0.3in; }}
  .cover .oleh {{ margin-bottom: 8pt; }}
  .cover table {{ border-collapse: collapse; text-align: left; margin: 0 auto; }}
  .cover td {{ padding: 5pt 0; vertical-align: top; }}
  .cover td:first-child {{ width: 1.7in; }}
  .cover .instansi {{ font-weight: bold; font-size: 14pt; line-height: 1.5; margin-top: auto; }}
  .cover .instansi div {{ margin-bottom: 10pt; }}
  .kepala {{ text-align: center; font-weight: bold; line-height: 1.6; margin-bottom: 18pt; }}
  .item {{ break-inside: avoid; margin-bottom: 14pt; }}
  .fig {{ text-align: center; margin: 6pt 0 14pt; }}
  .fig img {{ max-width: 100%; max-height: 5.2in; display: block; margin: 0 auto 6pt; }}
  .missing {{ color: #b00; text-align: center; }}
</style></head><body>
<div class="cover">
  <div class="judul">LAPORAN PRAKTIKUM<br>{MATKUL}<br>{PERTEMUAN}</div>
  <div class="topik">{TOPIK}</div>
  <img src="{LOGO.as_uri()}" alt="Logo UGM">
  <div class="oleh">Disusun oleh:</div>
  <table>
    <tr><td>Nama</td><td>: {html.escape(NAMA)}</td></tr>
    <tr><td>NIM</td><td>: {html.escape(NIM)}</td></tr>
    <tr><td>Kelas</td><td>: {html.escape(KELAS)}</td></tr>
    <tr><td>Dosen Pengampu</td><td>: {html.escape(DOSEN)}</td></tr>
  </table>
  <div class="instansi">
    <div>PROGRAM STUDI D-IV TEKNOLOGI REKAYASA PERANGKAT LUNAK</div>
    <div>DEPARTEMEN TEKNIK ELEKTRO DAN INFORMATIKA</div>
    <div>SEKOLAH VOKASI</div>
    <div>UNIVERSITAS GADJAH MADA</div>
    <div>YOGYAKARTA</div>
    <div>{TAHUN}</div>
  </div>
</div>
<div class="kepala">{PERTEMUAN}<br>{TOPIK}</div>
{''.join(blocks)}
<p>{" ".join(PENUTUP.split())}</p>
</body></html>
"""

html_path = OUT_DIR / "laporan.html"
html_path.write_text(HTML, encoding="utf-8")
pdf_path = OUT_DIR / PDF_NAME
browser = next((b for b in BROWSERS if Path(b).exists()), None)
if not browser:
    sys.exit(f"Edge/Chrome tidak ditemukan. Buka {html_path} di browser lalu Print -> Save as PDF.")
subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                "--allow-file-access-from-files", f"--print-to-pdf={pdf_path}", html_path.as_uri()],
               check=True, capture_output=True)
missing = [s for s, _ in ISI if not find_shot(s)]
print(f"PDF dibuat: {pdf_path}")
print("Angka dari bukti:", N)
print("Screenshot belum ada: " + (", ".join(missing) if missing else "-"))
