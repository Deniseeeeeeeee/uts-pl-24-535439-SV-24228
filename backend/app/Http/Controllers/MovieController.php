<?php

namespace App\Http\Controllers;

use App\Models\Movie;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class MovieController extends Controller
{
    // GET /api/movies
    public function index(): JsonResponse
    {
        return response()->json([
            'message' => 'Daftar film berhasil diambil.',
            'data' => Movie::orderByDesc('id')->get(),
        ], 200);
    }

    // POST /api/movies
    public function store(Request $request): JsonResponse
    {
        $data = $request->validate([
            'title' => ['required', 'string', 'max:255'],
            'director' => ['required', 'string', 'max:255'],
            'genre' => ['required', 'string', 'max:100'],
            'release_year' => ['required', 'integer', 'min:1888', 'max:' . (date('Y') + 5)],
            'rating' => ['nullable', 'numeric', 'between:0,10'],
            'synopsis' => ['nullable', 'string'],
        ]);

        $movie = Movie::create($data);

        return response()->json([
            'message' => 'Film berhasil ditambahkan.',
            'data' => $movie,
        ], 201);
    }

    // GET /api/movies/{movie}
    public function show(Movie $movie): JsonResponse
    {
        return response()->json([
            'message' => 'Detail film berhasil diambil.',
            'data' => $movie,
        ], 200);
    }

    // PUT/PATCH /api/movies/{movie}
    public function update(Request $request, Movie $movie): JsonResponse
    {
        $data = $request->validate([
            'title' => ['sometimes', 'required', 'string', 'max:255'],
            'director' => ['sometimes', 'required', 'string', 'max:255'],
            'genre' => ['sometimes', 'required', 'string', 'max:100'],
            'release_year' => ['sometimes', 'required', 'integer', 'min:1888', 'max:' . (date('Y') + 5)],
            'rating' => ['nullable', 'numeric', 'between:0,10'],
            'synopsis' => ['nullable', 'string'],
        ]);

        $movie->update($data);

        return response()->json([
            'message' => 'Film berhasil diperbarui.',
            'data' => $movie->fresh(),
        ], 200);
    }

    // DELETE /api/movies/{movie}
    public function destroy(Movie $movie): JsonResponse
    {
        $movie->delete();

        return response()->json([
            'message' => 'Film berhasil dihapus.',
        ], 200);
    }
}
