<?php

namespace App\Exceptions;

use App\Support\LogContext;
use Illuminate\Database\DetectsLostConnections;
use Illuminate\Database\QueryException;
use Illuminate\Foundation\Exceptions\Handler as ExceptionHandler;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Str;
use Illuminate\Validation\ValidationException;
use PDOException;
use Throwable;

class Handler extends ExceptionHandler
{
    use DetectsLostConnections;

    /**
     * The list of the inputs that are never flashed to the session on validation exceptions.
     *
     * @var array<int, string>
     */
    protected $dontFlash = [
        'current_password',
        'password',
        'password_confirmation',
    ];

    /**
     * Register the exception handling callbacks for the application.
     */
    public function register(): void
    {
        // Log ERROR: gagal konek ke database.
        // Pesan QueryException memuat SQL + binding (bisa berisi email dsb.),
        // jadi yang dicatat hanya pesan PDO aslinya, dan default report dimatikan
        // (return false) supaya stack trace berisi binding tidak ikut tercetak.
        $this->reportable(function (QueryException|PDOException $e) {
            $pdo = $e instanceof QueryException ? ($e->getPrevious() ?? $e) : $e;

            if ($this->causedByLostConnection($pdo)) {
                Log::error('Gagal terhubung ke database', [
                    ...LogContext::actor(),
                    'action' => $this->actionName(request()),
                    'component' => 'database',
                    'reason' => Str::limit($pdo->getMessage(), 200),
                    'exception' => class_basename($e),
                ]);
            } else {
                Log::error('Query database gagal', [
                    ...LogContext::actor(),
                    'action' => $this->actionName(request()),
                    'component' => 'database',
                    'reason' => 'SQLSTATE '.($pdo->errorInfo[0] ?? $pdo->getCode()),
                    'exception' => class_basename($e),
                ]);
            }

            return false;
        });
    }

    /**
     * Log WARNING: validasi gagal.
     * Hanya NAMA field yang gagal yang dicatat, bukan nilai yang dikirim user.
     */
    protected function invalidJson($request, ValidationException $exception)
    {
        Log::warning('Validasi input gagal', [
            ...LogContext::actor($request),
            'action' => $this->actionName($request),
            'reason' => 'validation_failed',
            'failed_fields' => array_keys($exception->errors()),
            'rules_failed' => collect($exception->validator->failed())
                ->map(fn ($rules) => array_keys($rules))
                ->all(),
        ]);

        return parent::invalidJson($request, $exception);
    }

    /**
     * Semua error di /api/* selalu dibalas JSON
     * (401 token tidak ada, 422 validasi gagal, 404 data tidak ketemu),
     * walaupun header Accept: application/json lupa dipasang.
     */
    protected function shouldReturnJson($request, Throwable $e)
    {
        return $request->is('api/*') || $request->expectsJson();
    }

    /**
     * Nama aksi dari route, misalnya "movies.store" atau "POST api/login".
     */
    private function actionName(?Request $request): ?string
    {
        if (! $request) {
            return null;
        }

        return $request->route()?->getName()
            ?? $request->method().' '.$request->path();
    }
}
