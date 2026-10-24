# Tahap 1: build aplikasi Vue dengan Node.js
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Alamat API dimasukkan saat build (variabel VITE_ ikut tertanam di hasil build)
ARG VITE_API_URL=http://localhost:8000/api
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Tahap 2: sajikan hasil build dengan Nginx.
# Hanya folder dist yang disalin, jadi node_modules tidak ikut ke image akhir.
FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
