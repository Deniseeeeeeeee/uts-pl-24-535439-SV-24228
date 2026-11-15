<?php

namespace Tests\Feature;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\DB;
use Tests\TestCase;

class MetricsTest extends TestCase
{
    use RefreshDatabase;

    public function test_metrics_berformat_prometheus_dan_melaporkan_dependensi(): void
    {
        $response = $this->get('/metrics');

        $response->assertOk();
        $this->assertStringContainsString('text/plain', $response->headers->get('Content-Type'));
        $response->assertSee('# TYPE app_http_requests_total counter', false);
        $response->assertSee('app_dependency_up{component="database"} 1', false);
        $response->assertSee('app_dependency_up{component="cache"} 1', false);
        $response->assertSee('app_movies_total 0', false);
    }

    public function test_metrics_tetap_200_saat_database_mati(): void
    {
        config(['database.connections.sqlite.database' => '/tidak/ada/db.sqlite']);
        DB::purge('sqlite');

        $this->get('/metrics')
            ->assertOk()
            ->assertSee('app_dependency_up{component="database"} 0', false)
            ->assertDontSee('app_movies_total', false);
    }
}
