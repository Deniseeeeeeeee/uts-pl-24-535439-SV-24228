# Movie API (Laravel + Sanctum)

Backend RESTful API bertema **Movie** untuk UTS Konstruksi dan Evolusi Perangkat Lunak.

## Setup

```bash
# 1. Buat project Laravel baru dan masuk ke foldernya
composer create-project laravel/laravel movie-api
cd movie-api

# 2. Pasang Sanctum + routes/api.php
php artisan install:api

# 3. Buat model + controller kosong, lalu timpa isinya dengan file dari paket ini
php artisan make:model Movie
php artisan make:controller MovieController --api
php artisan make:controller AuthController
php artisan make:migration create_movies_table
```

Timpa file berikut dengan isi dari paket ini:

| File paket ini | Tujuan di project |
|---|---|
| `app/Models/Movie.php` | sama |
| `app/Http/Controllers/AuthController.php` | sama |
| `app/Http/Controllers/MovieController.php` | sama |
| `routes/api.php` | sama |
| `bootstrap/app.php` | sama |
| `database/seeders/DatabaseSeeder.php` | sama |
| `database/migrations/2026_10_24_000000_create_movies_table.php` | sama (hapus migration `create_movies_table` bawaan hasil `make:migration` supaya tidak dobel) |
| `postman/Movie-API.postman_collection.json` | sama (commit ke repo) |

Pastikan model `User` memakai trait `HasApiTokens` (sudah otomatis di Laravel 11/12 setelah `install:api`; kalau belum, tambahkan `use Laravel\Sanctum\HasApiTokens;`).

```bash
# 4. Atur database di .env (default SQLite sudah jalan tanpa setup tambahan)
php artisan migrate --seed
php artisan serve
```

Akun uji: `admin@example.com` / `password123`

## Endpoint

| Method | URL | Auth | Keterangan | Status sukses |
|---|---|---|---|---|
| POST | /api/login | Tidak | Login, dapat token | 200 |
| POST | /api/logout | Bearer | Hapus token aktif | 200 |
| GET | /api/movies | Bearer | Tampil semua | 200 |
| GET | /api/movies/{id} | Bearer | Tampil satu | 200 |
| POST | /api/movies | Bearer | Tambah | **201** |
| PUT/PATCH | /api/movies/{id} | Bearer | Ubah | 200 |
| DELETE | /api/movies/{id} | Bearer | Hapus | 200 |

Status error: **422** validasi gagal, **401** token tidak ada / salah / sudah logout, **404** data tidak ditemukan.

## Pengujian Postman

1. Import `postman/Movie-API.postman_collection.json`.
2. Jalankan request **1. Login**. Token otomatis disimpan ke variabel `{{token}}`.
3. Jalankan request lainnya berurutan (4 sampai 12).
4. Ambil screenshot untuk laporan: Login (200), Store (201), Store gagal (422), Tanpa token (401).
