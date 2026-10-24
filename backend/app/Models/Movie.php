<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Movie extends Model
{
    protected $fillable = [
        'title',
        'director',
        'genre',
        'release_year',
        'rating',
        'synopsis',
    ];

    protected $casts = [
        'release_year' => 'integer',
        'rating' => 'float',
    ];
}
