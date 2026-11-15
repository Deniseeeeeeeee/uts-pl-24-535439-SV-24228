<?php

use App\Http\Controllers\HealthController;
use Illuminate\Support\Facades\Route;

// Endpoint health check untuk Docker healthcheck / monitoring.
// Didaftarkan TANPA middleware group (tanpa session, cookie, auth),
// supaya tetap bisa menjawab walaupun DB sedang mati.
Route::get('/health', HealthController::class)->name('health');

// P11: metrik aplikasi untuk di-scrape Prometheus (format teks Prometheus)
Route::get('/metrics', \App\Http\Controllers\MetricsController::class)->name('metrics');
