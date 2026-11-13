<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import AppIcon from '../components/AppIcon.vue'
import { posterStyle } from '../poster'

const router = useRouter()
const email = ref('admin@example.com')
const password = ref('')
const showPassword = ref(false)
const error = ref('')
const fieldErrors = ref({})
const loading = ref(false)

// Poster hiasan di sisi kiri halaman login
const decorPosters = [
  { title: 'Inception', r: '-6deg' },
  { title: 'Parasite', r: '3deg' },
  { title: 'Spirited Away', r: '-2deg' },
  { title: 'The Raid', r: '5deg' },
]

async function login() {
  error.value = ''
  fieldErrors.value = {}
  loading.value = true
  try {
    const { data } = await api.post('/login', {
      email: email.value,
      password: password.value,
    })
    localStorage.setItem('token', data.token)
    router.push({ name: 'movies' })
  } catch (e) {
    if (e.response?.status === 422) {
      fieldErrors.value = e.response.data.errors
    } else if (e.response?.status === 401) {
      error.value = e.response.data.message
    } else {
      error.value = 'Tidak bisa terhubung ke server.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="auth">
    <section class="auth-hero">
      <span class="brand">
        <span class="brand-mark"><AppIcon name="film" /></span>
        MovieApp
      </span>

      <div>
        <h1>Kelola koleksi <em>film favoritmu</em> di satu tempat.</h1>
        <p>Catat judul, sutradara, genre, dan rating film yang sudah kamu tonton. Rapi, cepat, dan mudah dicari.</p>
        <div class="poster-strip" aria-hidden="true">
          <div
            v-for="p in decorPosters"
            :key="p.title"
            class="mini-poster"
            :style="{ ...posterStyle(p.title), '--r': p.r }"
          ></div>
        </div>
      </div>

      <small class="muted">&copy; {{ new Date().getFullYear() }} MovieApp</small>
    </section>

    <section class="auth-panel">
      <form class="auth-card" @submit.prevent="login" novalidate>
        <h2>Selamat datang kembali</h2>
        <p class="muted">Masuk untuk mengelola daftar film.</p>

        <div v-if="error" class="alert" role="alert">
          <AppIcon name="alert" style="width: 18px; height: 18px; flex-shrink: 0" />
          <span>{{ error }}</span>
        </div>

        <label class="field" :class="{ 'has-error': fieldErrors.email }">
          <span>Email</span>
          <input v-model="email" type="email" autocomplete="username" placeholder="nama@email.com" />
          <small v-if="fieldErrors.email" class="error">{{ fieldErrors.email[0] }}</small>
        </label>

        <label class="field" :class="{ 'has-error': fieldErrors.password }">
          <span>Password</span>
          <div class="password-wrap">
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              placeholder="Masukkan password"
            />
            <button
              type="button"
              :aria-label="showPassword ? 'Sembunyikan password' : 'Tampilkan password'"
              @click="showPassword = !showPassword"
            >
              <AppIcon :name="showPassword ? 'eyeOff' : 'eye'" />
            </button>
          </div>
          <small v-if="fieldErrors.password" class="error">{{ fieldErrors.password[0] }}</small>
        </label>

        <button type="submit" class="btn btn-block" :disabled="loading">
          {{ loading ? 'Memproses...' : 'Masuk' }}
        </button>

      </form>
    </section>
  </main>
</template>
