import json, sys
DS = {"type": "prometheus", "uid": "prometheus"}
PROJ = 'container_label_com_docker_compose_project="uts-pl-24-535439-sv-24228"'
USER_ROUTES = 'route!~"/health|/metrics|unmatched"'
pid = [0]

def target(expr, legend, ref, instant=False):
    t = {"datasource": DS, "expr": expr, "legendFormat": legend, "refId": ref}
    t.update({"instant": True, "range": False} if instant else {"range": True})
    return t

def ts(title, desc, unit, axis, targets, x, y, w=12, h=9, extra=None, legend="bottom"):
    pid[0] += 1
    p = {
        "id": pid[0], "type": "timeseries", "title": title, "description": desc,
        "datasource": DS, "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "fieldConfig": {"defaults": {
            "unit": unit, "min": 0,
            "custom": {"axisLabel": axis, "drawStyle": "line", "lineWidth": 2, "fillOpacity": 12,
                       "showPoints": "never", "spanNulls": True, "axisPlacement": "left"},
            "color": {"mode": "palette-classic"}}, "overrides": []},
        "options": {"legend": {"displayMode": "table", "placement": legend, "calcs": ["lastNotNull", "max"]},
                    "tooltip": {"mode": "multi", "sort": "desc"}},
        "targets": [target(*t, chr(65 + i)) for i, t in enumerate(targets)],
    }
    if extra: p["fieldConfig"]["defaults"].update(extra)
    return p

def stat(title, desc, unit, targets, x, y, w, h, mappings=None, thresholds=None, text="value_and_name"):
    pid[0] += 1
    return {
        "id": pid[0], "type": "stat", "title": title, "description": desc,
        "datasource": DS, "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "fieldConfig": {"defaults": {
            "unit": unit, "mappings": mappings or [],
            "thresholds": thresholds or {"mode": "absolute", "steps": [{"color": "blue", "value": None}]},
            "color": {"mode": "thresholds"}}, "overrides": []},
        "options": {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "colorMode": "background", "graphMode": "none", "textMode": text,
                    "justifyMode": "center", "orientation": "auto", "wideLayout": True,
                    "text": {"titleSize": 15, "valueSize": 30}},
        "targets": [target(*t, chr(65 + i), instant=True) for i, t in enumerate(targets)],
    }

UPDOWN = [{"type": "value", "options": {"0": {"text": "MATI", "color": "red", "index": 0},
                                        "1": {"text": "HIDUP", "color": "green", "index": 1}}}]
RG = {"mode": "absolute", "steps": [{"color": "red", "value": None}, {"color": "green", "value": 1}]}

panels = [
    stat("Apakah semua layanan sedang hidup?",
         "1 = HIDUP, 0 = MATI. Baris 'up' berasal dari keberhasilan Prometheus men-scrape tiap target; "
         "baris database/cache berasal dari pemeriksaan langsung oleh aplikasi (app_dependency_up).",
         "none",
         [("max by (job) (up)", "{{job}}"), ("max by (component) (app_dependency_up)", "{{component}} (dicek app)")],
         0, 0, 18, 5, UPDOWN, RG),
    stat("Berapa film di katalog saat ini?", "Jumlah baris di tabel movies.", "short",
         [("max(app_movies_total)", "film")], 18, 0, 6, 5, text="value"),

    ts("Berapa permintaan per detik yang dilayani aplikasi?",
       "Laju request pengguna ke aplikasi per route, rata-rata 5 menit terakhir. Pemanggilan /health dan /metrics oleh sistem tidak dihitung.",
       "reqps", "permintaan / detik",
       [(f'sum by (route) (rate(app_http_requests_total{{{USER_ROUTES}}}[5m]))', "{{route}}")], 0, 5),
    ts("Berapa persen permintaan yang berakhir error server (5xx)?",
       "Porsi request berstatus 5xx dibanding seluruh request pengguna (5 menit). Naik tajam saat database mati.",
       "percentunit", "persentase error",
       [(f'(sum(rate(app_http_requests_total{{{USER_ROUTES},status=~"5.."}}[5m])) or vector(0)) / clamp_min(sum(rate(app_http_requests_total{{{USER_ROUTES}}}[5m])), 1e-9)', "error 5xx")],
       12, 5, extra={"max": 1}),

    ts("Container mana yang paling banyak memakai CPU?",
       "Pemakaian CPU per container dari cAdvisor. 100% = satu core penuh.",
       "percentunit", "CPU (1 core = 100%)",
       [(f'sum by (container_label_com_docker_compose_service) (rate(container_cpu_usage_seconds_total{{{PROJ}}}[5m]))', "{{container_label_com_docker_compose_service}}")],
       0, 14, legend="right"),
    ts("Berapa memori yang dipakai tiap container?",
       "Working set memory per container dari cAdvisor (memori yang benar-benar dipakai, tidak termasuk cache yang bisa dibuang).",
       "bytes", "memori",
       [(f'sum by (container_label_com_docker_compose_service) (container_memory_working_set_bytes{{{PROJ}}})', "{{container_label_com_docker_compose_service}}")],
       12, 14, legend="right"),

    ts("Seberapa lambat respons API untuk 95% permintaan?",
       "Persentil ke-95 waktu respons per route (histogram app_http_request_duration_seconds, 5 menit).",
       "s", "waktu respons",
       [(f'histogram_quantile(0.95, sum by (le, route) (rate(app_http_request_duration_seconds_bucket{{{USER_ROUTES}}}[5m])))', "p95 {{route}}")],
       0, 23),
    ts("Seberapa sibuk CPU dan memori mesin host?",
       "Data node-exporter untuk mesin (VM Docker) tempat semua container berjalan.",
       "percentunit", "pemakaian",
       [('1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))', "CPU host"),
        ('1 - avg(node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)', "memori host")],
       12, 23, extra={"max": 1}),
]

dash = {
    "uid": "movie-app-p11", "title": "Movie App — Kesehatan & Kinerja",
    "description": "Dashboard P11: apakah layanan hidup, berapa beban dan error aplikasi, dan berapa sumber daya yang dipakai tiap container.",
    "tags": ["movie-app", "p11"], "timezone": "browser", "editable": True, "schemaVersion": 41,
    "version": 1, "refresh": "10s", "time": {"from": "now-30m", "to": "now"},
    "graphTooltip": 1, "panels": panels, "templating": {"list": []}, "annotations": {"list": []},
}
json.dump(dash, open(sys.argv[1], "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("panel:", len(panels))
