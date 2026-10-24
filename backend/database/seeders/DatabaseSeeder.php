<?php

namespace Database\Seeders;

use App\Models\Movie;
use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        User::updateOrCreate(
            ['email' => 'admin@example.com'],
            ['name' => 'Admin Movie', 'password' => Hash::make('password123')]
        );

        $movies = [
            ['title' => 'Inception', 'director' => 'Christopher Nolan', 'genre' => 'Sci-Fi', 'release_year' => 2010, 'rating' => 8.8, 'synopsis' => 'Pencuri yang menanamkan ide lewat mimpi.'],
            ['title' => 'Parasite', 'director' => 'Bong Joon-ho', 'genre' => 'Thriller', 'release_year' => 2019, 'rating' => 8.5, 'synopsis' => 'Keluarga miskin menyusup ke keluarga kaya.'],
            ['title' => 'Spirited Away', 'director' => 'Hayao Miyazaki', 'genre' => 'Animation', 'release_year' => 2001, 'rating' => 8.6, 'synopsis' => 'Gadis kecil terjebak di dunia roh.'],
            ['title' => 'The Raid', 'director' => 'Gareth Evans', 'genre' => 'Action', 'release_year' => 2011, 'rating' => 7.6, 'synopsis' => 'Tim SWAT terjebak di gedung penuh penjahat.'],
        ];

        foreach ($movies as $movie) {
            Movie::updateOrCreate(['title' => $movie['title']], $movie);
        }
    }
}
