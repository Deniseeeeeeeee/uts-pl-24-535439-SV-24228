<?php

namespace App\Http\Controllers;

use App\Models\Movie;
use App\Support\Metrics;
use Illuminate\Http\Response;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;
use Throwable;

/**
 * GET /metrics — data untuk di-scrape Prometheus (format teks Prometheus).
 *
 * Berisi:
 *  - app_http_requests_total                : jumlah request per method/route/status
 *  - app_http_request_duration_seconds      : histogram waktu respons per route
 *  - app_dependency_up{component=...}       : 1/0, apakah DB dan cache bisa dipakai
 *  - app_movies_total                       : jumlah film di katalog
 */
class MetricsController extends Controller
{
    public function __invoke(): Response
    {
        $lines = [];
        $counters = Metrics::counters();

        $lines[] = '# HELP app_http_requests_total Jumlah request HTTP yang dilayani aplikasi.';
        $lines[] = '# TYPE app_http_requests_total counter';
        foreach ($counters['app_http_requests_total'] ?? [] as $c) {
            $lines[] = $this->line('app_http_requests_total', $c['labels'], $c['value']);
        }

        $lines[] = '# HELP app_http_request_duration_seconds Waktu respons request HTTP.';
        $lines[] = '# TYPE app_http_request_duration_seconds histogram';
        foreach ($counters['app_http_request_duration_seconds_bucket'] ?? [] as $c) {
            $lines[] = $this->line('app_http_request_duration_seconds_bucket', $c['labels'], $c['value']);
        }
        foreach ($counters['app_http_request_duration_seconds_sum_us'] ?? [] as $c) {
            $lines[] = $this->line('app_http_request_duration_seconds_sum', $c['labels'], $c['value'] / 1e6);
        }
        foreach ($counters['app_http_request_duration_seconds_count'] ?? [] as $c) {
            $lines[] = $this->line('app_http_request_duration_seconds_count', $c['labels'], $c['value']);
        }

        // Status dependensi: dicek langsung saat di-scrape, exception ditangkap
        $dbUp = $this->databaseUp();
        $lines[] = '# HELP app_dependency_up Apakah dependensi aplikasi bisa dipakai (1 = ya, 0 = tidak).';
        $lines[] = '# TYPE app_dependency_up gauge';
        $lines[] = $this->line('app_dependency_up', ['component' => 'database'], $dbUp ? 1 : 0);
        $lines[] = $this->line('app_dependency_up', ['component' => 'cache'], $this->cacheUp() ? 1 : 0);

        if ($dbUp) {
            $lines[] = '# HELP app_movies_total Jumlah film di katalog.';
            $lines[] = '# TYPE app_movies_total gauge';
            $lines[] = $this->line('app_movies_total', [], Movie::count());
        }

        $lines[] = '# HELP app_metrics_storage_enabled Apakah penyimpanan penghitung (APCu) aktif.';
        $lines[] = '# TYPE app_metrics_storage_enabled gauge';
        $lines[] = $this->line('app_metrics_storage_enabled', [], Metrics::enabled() ? 1 : 0);

        return response(implode("\n", $lines)."\n", 200, [
            'Content-Type' => 'text/plain; version=0.0.4; charset=utf-8',
        ]);
    }

    private function databaseUp(): bool
    {
        try {
            DB::select('SELECT 1');

            return true;
        } catch (Throwable) {
            DB::purge();

            return false;
        }
    }

    private function cacheUp(): bool
    {
        try {
            $key = 'metrics:'.Str::random(8);
            Cache::put($key, 1, 5);
            $ok = Cache::get($key) === 1;
            Cache::forget($key);

            return $ok;
        } catch (Throwable) {
            return false;
        }
    }

    private function line(string $name, array $labels, int|float $value): string
    {
        $pairs = [];
        foreach ($labels as $k => $v) {
            $pairs[] = $k.'="'.addcslashes((string) $v, "\\\"\n").'"';
        }

        return $name.($pairs ? '{'.implode(',', $pairs).'}' : '').' '.$value;
    }
}
