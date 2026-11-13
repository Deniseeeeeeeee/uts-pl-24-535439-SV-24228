#!/bin/sh
set -e

echo "Menjalankan migrasi database..."
i=0
until php artisan migrate --force; do
  i=$((i+1))
  if [ "$i" -ge 15 ]; then
    echo "Migrasi gagal setelah 15 percobaan."
    exit 1
  fi
  echo "Database belum siap, coba lagi ($i/15)..."
  sleep 3
done

# Seeder memakai updateOrCreate, jadi aman dijalankan berulang kali
echo "Mengisi data awal..."
php artisan db:seed --force

echo "Menjalankan server aplikasi..."
exec apache2-foreground
