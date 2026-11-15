<?php

namespace App\Support;

use APCUIterator;

/**
 * Penghitung metrik sederhana berformat Prometheus.
 *
 * PHP tidak menyimpan state antar request, jadi angka disimpan di APCu:
 * memori bersama yang dipakai semua proses Apache di dalam container.
 * Kalau APCu tidak tersedia (misalnya saat test/CLI), semua fungsi no-op.
 *
 * Label sengaja dibatasi (method, route pola, status) supaya jumlah deret
 * waktu tetap kecil, dan tidak ada data pengguna yang masuk ke metrik.
 */
class Metrics
{
    private const PREFIX = 'metrics|';

    /** Batas bucket histogram waktu respons (detik). */
    public const BUCKETS = [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5];

    public static function enabled(): bool
    {
        return function_exists('apcu_enabled') && apcu_enabled();
    }

    public static function recordRequest(string $method, string $route, int $status, float $seconds): void
    {
        if (! self::enabled()) {
            return;
        }

        self::inc('app_http_requests_total', ['method' => $method, 'route' => $route, 'status' => (string) $status]);

        foreach (self::BUCKETS as $le) {
            if ($seconds <= $le) {
                self::inc('app_http_request_duration_seconds_bucket', ['route' => $route, 'le' => (string) $le]);
            }
        }
        self::inc('app_http_request_duration_seconds_bucket', ['route' => $route, 'le' => '+Inf']);
        self::inc('app_http_request_duration_seconds_count', ['route' => $route]);
        // apcu_inc hanya bilangan bulat, jadi jumlah durasi disimpan dalam mikrodetik
        self::inc('app_http_request_duration_seconds_sum_us', ['route' => $route], (int) round($seconds * 1e6));
    }

    /**
     * Semua penghitung yang tersimpan, dikelompokkan per nama metrik.
     *
     * @return array<string, array<int, array{labels: array<string,string>, value: int}>>
     */
    public static function counters(): array
    {
        if (! self::enabled()) {
            return [];
        }

        $out = [];
        foreach (new APCUIterator('/^'.preg_quote(self::PREFIX, '/').'/') as $item) {
            [, $name, $json] = explode('|', $item['key'], 3);
            $out[$name][] = ['labels' => json_decode($json, true) ?: [], 'value' => (int) $item['value']];
        }
        ksort($out);

        return $out;
    }

    private static function inc(string $name, array $labels, int $by = 1): void
    {
        ksort($labels);
        $key = self::PREFIX.$name.'|'.json_encode($labels);

        // apcu_inc gagal kalau kunci belum ada; apcu_add atomik untuk inisialisasi
        if (apcu_inc($key, $by) === false) {
            if (! apcu_add($key, $by)) {
                apcu_inc($key, $by);
            }
        }
    }
}
