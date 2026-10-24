<?php

namespace Tests\Feature;

use App\Models\Movie;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Laravel\Sanctum\Sanctum;
use Tests\TestCase;

class MovieTest extends TestCase
{
    use RefreshDatabase;

    private function buatFilm(array $override = []): Movie
    {
        return Movie::create(array_merge([
            'title' => 'Inception',
            'director' => 'Christopher Nolan',
            'genre' => 'Sci-Fi',
            'release_year' => 2010,
            'rating' => 8.8,
            'synopsis' => 'Pencuri yang menanamkan ide lewat mimpi.',
        ], $override));
    }

    public function test_endpoint_movies_tanpa_token_mengembalikan_401(): void
    {
        $this->getJson('/api/movies')->assertStatus(401);
    }

    public function test_index_menampilkan_semua_film(): void
    {
        Sanctum::actingAs(User::factory()->create());
        $this->buatFilm();
        $this->buatFilm(['title' => 'Parasite']);

        $this->getJson('/api/movies')
            ->assertStatus(200)
            ->assertJsonCount(2, 'data');
    }

    public function test_store_membuat_film_dan_mengembalikan_201(): void
    {
        Sanctum::actingAs(User::factory()->create());

        $this->postJson('/api/movies', [
            'title' => 'Interstellar',
            'director' => 'Christopher Nolan',
            'genre' => 'Sci-Fi',
            'release_year' => 2014,
            'rating' => 8.7,
        ])
            ->assertStatus(201)
            ->assertJsonPath('data.title', 'Interstellar');

        $this->assertDatabaseHas('movies', ['title' => 'Interstellar']);
    }

    public function test_store_dengan_data_tidak_valid_mengembalikan_422(): void
    {
        Sanctum::actingAs(User::factory()->create());

        $this->postJson('/api/movies', [
            'title' => '',
            'release_year' => 'bukan-angka',
            'rating' => 99,
        ])
            ->assertStatus(422)
            ->assertJsonValidationErrors(['title', 'director', 'genre', 'release_year', 'rating']);
    }

    public function test_show_menampilkan_satu_film(): void
    {
        Sanctum::actingAs(User::factory()->create());
        $film = $this->buatFilm();

        $this->getJson("/api/movies/{$film->id}")
            ->assertStatus(200)
            ->assertJsonPath('data.title', 'Inception');
    }

    public function test_update_mengubah_data_film(): void
    {
        Sanctum::actingAs(User::factory()->create());
        $film = $this->buatFilm();

        $this->putJson("/api/movies/{$film->id}", ['title' => 'Inception (Edited)'])
            ->assertStatus(200)
            ->assertJsonPath('data.title', 'Inception (Edited)');

        $this->assertDatabaseHas('movies', ['id' => $film->id, 'title' => 'Inception (Edited)']);
    }

    public function test_destroy_menghapus_film(): void
    {
        Sanctum::actingAs(User::factory()->create());
        $film = $this->buatFilm();

        $this->deleteJson("/api/movies/{$film->id}")->assertStatus(200);

        $this->assertDatabaseMissing('movies', ['id' => $film->id]);
    }
}
