FROM php:8.2-apache

# Ekstensi PHP yang dibutuhkan Laravel + driver MySQL, mod_rewrite untuk routing,
# dan curl untuk HEALTHCHECK (memanggil GET /health)
RUN apt-get update \
    && apt-get install -y --no-install-recommends unzip git libzip-dev curl \
    && docker-php-ext-install pdo_mysql zip \
    && a2enmod rewrite \
    && rm -rf /var/lib/apt/lists/*

# Apache melayani folder public/ milik Laravel
ENV APACHE_DOCUMENT_ROOT=/var/www/html/public
RUN sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/sites-available/*.conf \
    && sed -ri -e 's!/var/www/!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf

COPY --from=composer:2.7 /usr/bin/composer /usr/bin/composer

WORKDIR /var/www/html

# 1) Salin composer.json dan composer.lock dulu, lalu pasang dependensi.
#    Selama kedua file ini tidak berubah, lapisan ini diambil dari cache.
COPY composer.json composer.lock ./
RUN composer install --no-dev --no-scripts --no-autoloader --prefer-dist --no-interaction

# 2) Baru salin kode aplikasi
COPY . .

RUN composer dump-autoload --optimize --no-dev --no-interaction \
    && chown -R www-data:www-data storage bootstrap/cache

# Skrip start: migrasi + seed, lalu jalankan Apache.
# sed membuang karakter CRLF (kalau file dibuat di Windows) supaya skrip bisa jalan di Linux.
RUN sed -i 's/\r$//' docker-entrypoint.sh && chmod +x docker-entrypoint.sh

EXPOSE 80

CMD ["./docker-entrypoint.sh"]
