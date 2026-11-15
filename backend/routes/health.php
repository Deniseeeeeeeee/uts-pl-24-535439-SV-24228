<?php

use App\Http\Controllers\HealthController;
use Illuminate\Support\Facades\Route;

// Endpoint health check untuk Docker healthcheck / monitoring.
// Didaftarkan TANPA middleware group (tanpa session, cookie, auth),
// supaya tetap bisa menjawab walaupun DB sedang mati.
Route::get('/health', HealthController::class)->name('health');
