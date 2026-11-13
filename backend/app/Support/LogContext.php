<?php

namespace App\Support;

use Illuminate\Http\Request;
use Throwable;

/**
 * Konteks standar untuk log terstruktur: SIAPA yang melakukan aksi.
 *
 * Hanya user id dan alamat IP yang dicatat. Email, nama, password, dan token
 * sengaja tidak pernah dimasukkan ke log.
 */
class LogContext
{
    public static function actor(?Request $request = null): array
    {
        $request ??= request();

        return [
            'user_id' => self::userId(),
            'ip' => $request?->ip(),
            'method' => $request?->method(),
            'path' => $request ? '/'.ltrim($request->path(), '/') : null,
        ];
    }

    /**
     * Ambil id user HANYA kalau sudah di-resolve oleh middleware auth.
     * Memanggil $request->user() langsung bisa memicu query ke DB,
     * dan itu akan gagal lagi ketika DB sedang mati.
     */
    private static function userId(): ?int
    {
        try {
            $guard = auth()->guard('sanctum');

            return $guard->hasUser() ? $guard->id() : null;
        } catch (Throwable) {
            return null;
        }
    }
}
