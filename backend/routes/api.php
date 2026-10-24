<?php

use App\Http\Controllers\AuthController;
use App\Http\Controllers\MovieController;
use Illuminate\Support\Facades\Route;

// Satu-satunya endpoint publik
Route::post('/login', [AuthController::class, 'login']);

// Semua endpoint lain wajib pakai token Sanctum
Route::middleware('auth:sanctum')->group(function () {
    Route::post('/logout', [AuthController::class, 'logout']);
    Route::apiResource('movies', MovieController::class);
});
