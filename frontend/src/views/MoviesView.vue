<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const movies = ref([])
const loading = ref(false)
const message = ref('')
const errors = ref({})
const editingId = ref(null)

const emptyForm = () => ({
  title: '',
  director: '',
  genre: '',
  release_year: '',
  rating: '',
  synopsis: '',
})
const form = reactive(emptyForm())

function resetForm() {
  Object.assign(form, emptyForm())
  editingId.value = null
  errors.value = {}
}

async function loadMovies() {
  loading.value = true
  try {
    const { data } = await api.get('/movies')
    movies.value = data.data
  } finally {
    loading.value = false
  }
}

async function save() {
  errors.value = {}
  message.value = ''
  const payload = { ...form, rating: form.rating === '' ? null : form.rating }

  try {
    if (editingId.value) {
      await api.put(`/movies/${editingId.value}`, payload)
      message.value = 'Film berhasil diperbarui.'
    } else {
      await api.post('/movies', payload)
      message.value = 'Film berhasil ditambahkan.'
    }
    resetForm()
    await loadMovies()
  } catch (e) {
    if (e.response?.status === 422) {
      errors.value = e.response.data.errors
    } else {
      message.value = 'Terjadi kesalahan pada server.'
    }
  }
}

function edit(movie) {
  editingId.value = movie.id
  errors.value = {}
  Object.assign(form, {
    title: movie.title,
    director: movie.director,
    genre: movie.genre,
    release_year: movie.release_year,
    rating: movie.rating ?? '',
    synopsis: movie.synopsis ?? '',
  })
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function remove(movie) {
  if (!confirm(`Hapus film "${movie.title}"?`)) return
  await api.delete(`/movies/${movie.id}`)
  message.value = 'Film berhasil dihapus.'
  await loadMovies()
}

async function logout() {
  try {
    await api.post('/logout')
  } finally {
    localStorage.removeItem('token')
    router.push({ name: 'login' })
  }
}

onMounted(loadMovies)
</script>

<template>
  <main class="container">
    <header class="topbar">
      <h1>Daftar Film</h1>
      <button class="secondary" @click="logout">Logout</button>
    </header>

    <p v-if="message" class="notice">{{ message }}</p>

    <form class="card" @submit.prevent="save">
      <h2>{{ editingId ? 'Ubah Film' : 'Tambah Film' }}</h2>
      <div class="grid">
        <label>
          Judul
          <input v-model="form.title" />
          <small v-if="errors.title" class="error">{{ errors.title[0] }}</small>
        </label>
        <label>
          Sutradara
          <input v-model="form.director" />
          <small v-if="errors.director" class="error">{{ errors.director[0] }}</small>
        </label>
        <label>
          Genre
          <input v-model="form.genre" />
          <small v-if="errors.genre" class="error">{{ errors.genre[0] }}</small>
        </label>
        <label>
          Tahun rilis
          <input v-model="form.release_year" type="number" />
          <small v-if="errors.release_year" class="error">{{ errors.release_year[0] }}</small>
        </label>
        <label>
          Rating (0-10)
          <input v-model="form.rating" type="number" step="0.1" />
          <small v-if="errors.rating" class="error">{{ errors.rating[0] }}</small>
        </label>
      </div>
      <label>
        Sinopsis
        <textarea v-model="form.synopsis" rows="3"></textarea>
      </label>
      <div class="actions">
        <button type="submit">{{ editingId ? 'Simpan Perubahan' : 'Tambah' }}</button>
        <button v-if="editingId" type="button" class="secondary" @click="resetForm">Batal</button>
      </div>
    </form>

    <section class="card">
      <p v-if="loading" class="muted">Memuat data...</p>
      <p v-else-if="!movies.length" class="muted">Belum ada film.</p>
      <table v-else>
        <thead>
          <tr>
            <th>Judul</th>
            <th>Sutradara</th>
            <th>Genre</th>
            <th>Tahun</th>
            <th>Rating</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="movie in movies" :key="movie.id">
            <td>{{ movie.title }}</td>
            <td>{{ movie.director }}</td>
            <td>{{ movie.genre }}</td>
            <td>{{ movie.release_year }}</td>
            <td>{{ movie.rating }}</td>
            <td class="row-actions">
              <button class="secondary small" @click="edit(movie)">Ubah</button>
              <button class="danger small" @click="remove(movie)">Hapus</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </main>
</template>
