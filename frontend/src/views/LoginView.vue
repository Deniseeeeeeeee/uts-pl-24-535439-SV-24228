<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const email = ref('admin@example.com')
const password = ref('')
const error = ref('')
const fieldErrors = ref({})
const loading = ref(false)

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
  <main class="center">
    <form class="card login" @submit.prevent="login">
      <h1>Movie App</h1>
      <p class="muted">Masuk untuk mengelola daftar film.</p>

      <label>
        Email
        <input v-model="email" type="email" autocomplete="username" />
        <small v-if="fieldErrors.email" class="error">{{ fieldErrors.email[0] }}</small>
      </label>

      <label>
        Password
        <input v-model="password" type="password" autocomplete="current-password" />
        <small v-if="fieldErrors.password" class="error">{{ fieldErrors.password[0] }}</small>
      </label>

      <p v-if="error" class="error">{{ error }}</p>

      <button type="submit" :disabled="loading">
        {{ loading ? 'Memproses...' : 'Login' }}
      </button>
    </form>
  </main>
</template>
