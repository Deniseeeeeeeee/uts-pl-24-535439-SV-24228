<?php

namespace App\Http\Controllers;

use App\Support\LogContext;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Str;
use Throwable;

/**
 * GET /health
 *
 * Benar-benar memeriksa komponen yang dibutuhkan aplikasi:
 *  - database: menjalankan SELECT 1
 *  - cache   : put lalu get sebuah nilai acak
 *
 * Setiap pemeriksaan dibungkus try/catch, jadi endpoint ini tidak ikut crash
 * ketika DB mati. Hasilnya 200 kalau semua sehat, 503 kalau ada yang gagal.
 */
class HealthController extends Controller
{
    public function __invoke(): JsonResponse
    {
        $checks = [
            'database' => $this->checkDatabase(),
            'cache' => $this->checkCache(),
        ];

        $failed = array_keys(array_filter($checks, fn ($c) => $c['status'] !== 'ok'));
        $healthy = empty($failed);

        $body = [
            'status' => $healthy ? 'ok' : 'fail',
            'checks' => $checks,
            'timestamp' => now()->toIso8601String(),
        ];

        if (! $healthy) {
            $body['failed'] = $failed;
        }

        return response()->json($body, $healthy ? 200 : 503);
    }

    private function checkDatabase(): array
    {
        $start = microtime(true);

        try {
            DB::select('SELECT 1');

            return ['status' => 'ok', 'latency_ms' => $this->elapsed($start)];
        } catch (Throwable $e) {
            // Log ERROR: gagal konek DB (detail teknis hanya di log, bukan di balasan)
            Log::error('Health check: gagal terhubung ke database', [
                ...LogContext::actor(),
                'action' => 'health.check_database',
                'component' => 'database',
                'reason' => $this->reason($e),
                'exception' => class_basename($e),
                'latency_ms' => $this->elapsed($start),
            ]);

            DB::purge(); // buang koneksi rusak supaya cek berikutnya mencoba ulang

            return ['status' => 'fail', 'error' => 'Tidak dapat terhubung ke database'];
        }
    }

    private function checkCache(): array
    {
        $start = microtime(true);
        $key = 'health:'.Str::random(12);
        $value = Str::random(16);

        try {
            Cache::put($key, $value, 10);
            $ok = Cache::get($key) === $value;
            Cache::forget($key);

            if (! $ok) {
                throw new \RuntimeException('Nilai yang dibaca dari cache tidak sama dengan yang ditulis');
            }

            return [
                'status' => 'ok',
                'driver' => config('cache.default'),
                'latency_ms' => $this->elapsed($start),
            ];
        } catch (Throwable $e) {
            Log::error('Health check: cache tidak bisa ditulis/dibaca', [
                ...LogContext::actor(),
                'action' => 'health.check_cache',
                'component' => 'cache',
                'reason' => $this->reason($e),
                'exception' => class_basename($e),
            ]);

            return ['status' => 'fail', 'error' => 'Cache tidak dapat ditulis/dibaca'];
        }
    }

    /**
     * Ambil pesan dari PDOException asli. Pesan QueryException memuat SQL
     * beserta binding-nya, jadi tidak dipakai supaya tidak ada data yang bocor.
     */
    private function reason(Throwable $e): string
    {
        $root = $e->getPrevious() ?? $e;

        return Str::limit($root->getMessage(), 200);
    }

    private function elapsed(float $start): float
    {
        return round((microtime(true) - $start) * 1000, 2);
    }
}
