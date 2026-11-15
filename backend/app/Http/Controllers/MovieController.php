<?php

namespace App\Http\Controllers;

use App\Models\Movie;
use App\Support\LogContext;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;

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

        // Log INFO: data berhasil disimpan (hanya id & nama field, bukan isi data)
        Log::info('Film baru disimpan', [
            ...LogContext::actor($request),
            'action' => 'movie.store',
            'movie_id' => $movie->id,
            'fields' => array_keys($data),
            'reason' => 'user menambahkan film lewat POST /api/movies',
        ]);

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

        $movie->fill($data);
        $changed = array_keys($movie->getDirty());
        $movie->save();

        // Log INFO: data berhasil diperbarui (hanya nama field yang berubah)
        Log::info('Film diperbarui', [
            ...LogContext::actor($request),
            'action' => 'movie.update',
            'movie_id' => $movie->id,
            'changed_fields' => $changed,
            'reason' => 'user mengubah film lewat PUT /api/movies/{id}',
        ]);

        return response()->json([
            'message' => 'Film berhasil diperbarui.',
            'data' => $movie->fresh(),
        ], 200);
    }

    // DELETE /api/movies/{movie}
    public function destroy(Request $request, Movie $movie): JsonResponse
    {
        $movie->delete();

        Log::info('Film dihapus', [
            ...LogContext::actor($request),
            'action' => 'movie.destroy',
            'movie_id' => $movie->id,
            'reason' => 'user menghapus film lewat DELETE /api/movies/{id}',
        ]);

        return response()->json([
            'message' => 'Film berhasil dihapus.',
        ], 200);
    }
}
