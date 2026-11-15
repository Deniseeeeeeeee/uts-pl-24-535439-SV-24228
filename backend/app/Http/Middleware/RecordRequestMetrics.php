<?php

namespace App\Http\Middleware;

use App\Support\Metrics;
use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

/**
 * Mencatat setiap request (method, pola route, status, durasi) untuk /metrics.
 *
 * Yang dipakai adalah POLA route (mis. "api/movies/{movie}"), bukan URL asli,
 * supaya id atau data lain dari URL tidak ikut masuk ke metrik.
 */
class RecordRequestMetrics
{
    public function handle(Request $request, Closure $next): Response
    {
        $start = microtime(true);

        $response = $next($request);

        $route = $request->route()?->uri() ?? 'unmatched';
        if ($route !== 'metrics') { // scrape Prometheus sendiri tidak dihitung
            Metrics::recordRequest(
                $request->method(),
                '/'.ltrim($route, '/'),
                $response->getStatusCode(),
                microtime(true) - $start,
            );
        }

        return $response;
    }
}
