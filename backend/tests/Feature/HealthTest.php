<?php

namespace Tests\Feature;

use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Tests\TestCase;

class HealthTest extends TestCase
{
    public function test_health_sehat_mengembalikan_200(): void
    {
        $this->getJson('/health')
            ->assertOk()
            ->assertJsonPath('status', 'ok')
            ->assertJsonPath('checks.database.status', 'ok')
            ->assertJsonPath('checks.cache.status', 'ok');
    }

    public function test_health_db_mati_mengembalikan_503_tanpa_crash(): void
    {
        Log::spy();

        // Arahkan koneksi ke file SQLite yang tidak ada -> SELECT 1 gagal
        config(['database.connections.sqlite.database' => '/tidak/ada/db.sqlite']);
        DB::purge('sqlite');

        $this->getJson('/health')
            ->assertStatus(503)
            ->assertJsonPath('status', 'fail')
            ->assertJsonPath('failed', ['database'])
            ->assertJsonPath('checks.cache.status', 'ok');

        Log::shouldHaveReceived('error')
            ->withArgs(fn ($msg, $ctx) => $ctx['component'] === 'database'
                && $ctx['action'] === 'health.check_database')
            ->once();
    }
}
