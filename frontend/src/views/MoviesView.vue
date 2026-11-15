<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import AppIcon from '../components/AppIcon.vue'
import { posterStyle, initials } from '../poster'

const router = useRouter()
const movies = ref([])
const loading = ref(false)
const saving = ref(false)
const errors = ref({})
const editingId = ref(null)

// ---------- Modal & dialog ----------
const showForm = ref(false)
const deleting = ref(null) // film yang akan dihapus (dialog konfirmasi)
const deletingBusy = ref(false)

// ---------- Pencarian, filter, urutan ----------
const search = ref('')
const activeGenre = ref('Semua')
const sortBy = ref('terbaru')

// ---------- Toast ----------
const toasts = ref([])
let toastId = 0
function notify(text, type = 'success') {
  const id = ++toastId
  toasts.value.push({ id, text, type })
  setTimeout(() => {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }, 3200)
}

// ---------- Form ----------
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

function openCreate() {
  resetForm()
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  resetForm()
}

// ---------- Data turunan ----------
const genres = computed(() => {
  const set = new Set(movies.value.map((m) => m.genre).filter(Boolean))
  return ['Semua', ...[...set].sort()]
})

const filteredMovies = computed(() => {
  const q = search.value.trim().toLowerCase()
  let list = movies.value.filter((m) => {
    const cocokGenre = activeGenre.value === 'Semua' || m.genre === activeGenre.value
    const cocokCari =
      !q ||
      [m.title, m.director, m.genre].some((v) => String(v || '').toLowerCase().includes(q))
    return cocokGenre && cocokCari
  })

  const byNum = (key) => (a, b) => (Number(b[key]) || 0) - (Number(a[key]) || 0)
  if (sortBy.value === 'rating') list = [...list].sort(byNum('rating'))
  else if (sortBy.value === 'tahun') list = [...list].sort(byNum('release_year'))
  else if (sortBy.value === 'judul') list = [...list].sort((a, b) => a.title.localeCompare(b.title))
  else list = [...list].sort((a, b) => b.id - a.id)
  return list
})

const featured = computed(() => {
  if (!movies.value.length) return null
  return [...movies.value].sort((a, b) => (Number(b.rating) || 0) - (Number(a.rating) || 0))[0]
})

const stats = computed(() => {
  const rated = movies.value.filter((m) => m.rating !== null && m.rating !== '')
  const avg = rated.length
    ? rated.reduce((s, m) => s + Number(m.rating), 0) / rated.length
    : 0
  return {
    total: movies.value.length,
    avg: avg ? avg.toFixed(1) : '-',
    genres: genres.value.length - 1,
  }
})

function formatRating(r) {
  if (r === null || r === '' || r === undefined) return '-'
  return Number(r).toFixed(1)
}

// ---------- API ----------
async function loadMovies() {
  loading.value = true
  try {
    const { data } = await api.get('/movies')
    movies.value = data.data
  } catch {
    notify('Gagal memuat data film.', 'error')
  } finally {
    loading.value = false
  }
}

async function save() {
  errors.value = {}
  saving.value = true
  const payload = { ...form, rating: form.rating === '' ? null : form.rating }

  try {
    if (editingId.value) {
      await api.put(`/movies/${editingId.value}`, payload)
      notify('Film berhasil diperbarui.')
    } else {
      await api.post('/movies', payload)
      notify('Film berhasil ditambahkan.')
    }
    closeForm()
    await loadMovies()
  } catch (e) {
    if (e.response?.status === 422) {
      errors.value = e.response.data.errors
    } else {
      notify('Terjadi kesalahan pada server.', 'error')
    }
  } finally {
    saving.value = false
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
  showForm.value = true
}

async function confirmDelete() {
  if (!deleting.value) return
  deletingBusy.value = true
  try {
    await api.delete(`/movies/${deleting.value.id}`)
    notify(`"${deleting.value.title}" berhasil dihapus.`)
    deleting.value = null
    await loadMovies()
  } catch {
    notify('Gagal menghapus film.', 'error')
  } finally {
    deletingBusy.value = false
  }
}

async function logout() {
  try {
    await api.post('/logout')
  } finally {
    localStorage.removeItem('token')
    router.push({ name: 'login' })
  }
}

// Tutup modal dengan tombol Escape
function onKey(e) {
  if (e.key !== 'Escape') return
  if (deleting.value && !deletingBusy.value) deleting.value = null
  else if (showForm.value && !saving.value) closeForm()
}

onMounted(() => {
  loadMovies()
  window.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <!-- ================= Navbar ================= -->
  <header class="navbar">
    <div class="container">
      <a href="/" class="brand" @click.prevent>
        <span class="brand-mark"><AppIcon name="film" /></span>
        MovieApp
      </a>

      <nav class="nav-links">
        <a href="#koleksi" class="active">Koleksi</a>
        <a href="#koleksi" @click="sortBy = 'rating'">Rating Tertinggi</a>
        <a href="#koleksi" @click="sortBy = 'tahun'">Terbaru Rilis</a>
      </nav>

      <div class="nav-right">
        <button class="btn btn-ghost" @click="logout">
          <AppIcon name="logout" />
          <span class="user-name">Keluar</span>
        </button>
      </div>
    </div>
  </header>

  <main>
    <!-- ================= Hero ================= -->
    <section class="hero">
      <div v-if="featured" class="hero-bg" :style="posterStyle(featured.title)"></div>
      <div class="container">
        <template v-if="featured">
          <span class="hero-tag"><AppIcon name="star" style="width: 12px; height: 12px" /> Rating tertinggi</span>
          <h1>{{ featured.title }}</h1>
          <div class="hero-meta">
            <span style="color: var(--accent); font-weight: 700">★ {{ formatRating(featured.rating) }}</span>
            <span class="dot"></span>
            <span>{{ featured.release_year }}</span>
            <span class="dot"></span>
            <span>{{ featured.genre }}</span>
            <span class="dot"></span>
            <span>Sutradara: {{ featured.director }}</span>
          </div>
          <p class="synopsis">{{ featured.synopsis || 'Belum ada sinopsis untuk film ini.' }}</p>
        </template>
        <template v-else>
          <span class="hero-tag">Koleksi film</span>
          <h1>Daftar Film Kamu</h1>
          <p class="synopsis">Tambahkan film pertama untuk mulai membangun koleksimu.</p>
        </template>

        <div class="hero-actions">
          <button class="btn" @click="openCreate"><AppIcon name="plus" /> Tambah Film</button>
          <button v-if="featured" class="btn btn-ghost" @click="edit(featured)">
            <AppIcon name="edit" /> Ubah
          </button>
        </div>

        <div class="stats">
          <div class="stat"><strong>{{ stats.total }}</strong><span>Total film</span></div>
          <div class="stat"><strong>{{ stats.avg }}</strong><span>Rata-rata rating</span></div>
          <div class="stat"><strong>{{ stats.genres }}</strong><span>Genre</span></div>
        </div>
      </div>
    </section>

    <!-- ================= Koleksi ================= -->
    <section id="koleksi" class="section">
      <div class="container">
        <div class="section-head">
          <div>
            <h2>Koleksi Film</h2>
            <p class="muted">
              Menampilkan {{ filteredMovies.length }} dari {{ movies.length }} film
            </p>
          </div>
        </div>

        <div class="toolbar">
          <div class="search">
            <AppIcon name="search" />
            <input
              v-model="search"
              class="input"
              type="search"
              placeholder="Cari judul, sutradara, atau genre..."
              aria-label="Cari film"
            />
          </div>
          <select v-model="sortBy" class="input select" aria-label="Urutkan">
            <option value="terbaru">Baru ditambahkan</option>
            <option value="rating">Rating tertinggi</option>
            <option value="tahun">Tahun rilis terbaru</option>
            <option value="judul">Judul (A–Z)</option>
          </select>
        </div>

        <div class="chips" role="tablist" aria-label="Filter genre">
          <button
            v-for="g in genres"
            :key="g"
            class="chip"
            :class="{ active: activeGenre === g }"
            role="tab"
            :aria-selected="activeGenre === g"
            @click="activeGenre = g"
          >
            {{ g }}
          </button>
        </div>

        <!-- Memuat -->
        <div v-if="loading && !movies.length" class="movie-grid">
          <div v-for="n in 8" :key="n" class="skeleton">
            <div class="sk-poster"></div>
            <div class="sk-line"></div>
            <div class="sk-line short"></div>
          </div>
        </div>

        <!-- Kosong -->
        <div v-else-if="!filteredMovies.length" class="empty">
          <div>
            <AppIcon name="film" />
            <h3>{{ movies.length ? 'Film tidak ditemukan' : 'Belum ada film' }}</h3>
            <p class="muted">
              {{ movies.length ? 'Coba kata kunci atau genre lain.' : 'Mulai tambahkan film ke koleksimu.' }}
            </p>
            <button
              v-if="movies.length"
              class="btn btn-ghost"
              @click="search = ''; activeGenre = 'Semua'"
            >
              Reset filter
            </button>
            <button v-else class="btn" @click="openCreate"><AppIcon name="plus" /> Tambah Film</button>
          </div>
        </div>

        <!-- Grid film -->
        <div v-else class="movie-grid">
          <article v-for="movie in filteredMovies" :key="movie.id" class="movie-card">
            <div class="poster" :style="posterStyle(movie.title)">
              <span class="rating-badge">
                <AppIcon name="star" /> {{ formatRating(movie.rating) }}
              </span>
              <div class="card-actions">
                <button :aria-label="`Ubah ${movie.title}`" title="Ubah" @click="edit(movie)">
                  <AppIcon name="edit" />
                </button>
                <button
                  class="del"
                  :aria-label="`Hapus ${movie.title}`"
                  title="Hapus"
                  @click="deleting = movie"
                >
                  <AppIcon name="trash" />
                </button>
              </div>
              <span class="poster-initial" aria-hidden="true">{{ initials(movie.title) }}</span>
              <h3 class="poster-title">{{ movie.title }}</h3>
            </div>
            <div class="movie-info">
              <div class="meta">
                <span class="genre-pill">{{ movie.genre }}</span>
                <span>{{ movie.release_year }}</span>
              </div>
              <span class="director">{{ movie.director }}</span>
              <p v-if="movie.synopsis" class="syn">{{ movie.synopsis }}</p>
            </div>
          </article>
        </div>
      </div>
    </section>
  </main>

  <footer class="footer">
    <div class="container">
      <span>&copy; {{ new Date().getFullYear() }} MovieApp</span>
      <span>Dibuat dengan Vue &amp; Laravel</span>
    </div>
  </footer>

  <!-- ================= Modal Tambah / Ubah ================= -->
  <Transition name="modal">
    <div v-if="showForm" class="modal-backdrop" @click.self="!saving && closeForm()">
      <form class="modal" role="dialog" aria-modal="true" @submit.prevent="save" novalidate>
        <div class="modal-head">
          <h3>{{ editingId ? 'Ubah Film' : 'Tambah Film Baru' }}</h3>
          <button type="button" class="btn btn-ghost btn-icon" aria-label="Tutup" @click="closeForm">
            <AppIcon name="close" />
          </button>
        </div>

        <div class="modal-body">
          <div class="form-grid">
            <label class="field full" :class="{ 'has-error': errors.title }">
              <span>Judul</span>
              <input v-model="form.title" placeholder="Contoh: Inception" />
              <small v-if="errors.title" class="error">{{ errors.title[0] }}</small>
            </label>
            <label class="field" :class="{ 'has-error': errors.director }">
              <span>Sutradara</span>
              <input v-model="form.director" placeholder="Nama sutradara" />
              <small v-if="errors.director" class="error">{{ errors.director[0] }}</small>
            </label>
            <label class="field" :class="{ 'has-error': errors.genre }">
              <span>Genre</span>
              <input v-model="form.genre" list="genre-list" placeholder="Action, Drama, ..." />
              <datalist id="genre-list">
                <option v-for="g in genres.slice(1)" :key="g" :value="g" />
              </datalist>
              <small v-if="errors.genre" class="error">{{ errors.genre[0] }}</small>
            </label>
            <label class="field" :class="{ 'has-error': errors.release_year }">
              <span>Tahun rilis</span>
              <input v-model="form.release_year" type="number" placeholder="2024" />
              <small v-if="errors.release_year" class="error">{{ errors.release_year[0] }}</small>
            </label>
            <label class="field" :class="{ 'has-error': errors.rating }">
              <span>Rating (0–10)</span>
              <input v-model="form.rating" type="number" step="0.1" min="0" max="10" placeholder="8.5" />
              <small v-if="errors.rating" class="error">{{ errors.rating[0] }}</small>
            </label>
            <label class="field full" :class="{ 'has-error': errors.synopsis }">
              <span>Sinopsis</span>
              <textarea v-model="form.synopsis" rows="4" placeholder="Ceritakan singkat tentang film ini..."></textarea>
              <small v-if="errors.synopsis" class="error">{{ errors.synopsis[0] }}</small>
            </label>
          </div>
        </div>

        <div class="modal-foot">
          <button type="button" class="btn btn-ghost" :disabled="saving" @click="closeForm">Batal</button>
          <button type="submit" class="btn" :disabled="saving">
            {{ saving ? 'Menyimpan...' : editingId ? 'Simpan Perubahan' : 'Tambah Film' }}
          </button>
        </div>
      </form>
    </div>
  </Transition>

  <!-- ================= Dialog Hapus ================= -->
  <Transition name="modal">
    <div v-if="deleting" class="modal-backdrop" @click.self="!deletingBusy && (deleting = null)">
      <div class="modal sm" role="alertdialog" aria-modal="true">
        <div class="modal-body">
          <div class="confirm-icon"><AppIcon name="trash" /></div>
          <h3 style="margin-bottom: 8px">Hapus film ini?</h3>
          <p class="muted" style="margin: 0 0 8px">
            "<strong style="color: var(--text)">{{ deleting.title }}</strong>" akan dihapus permanen dari koleksi.
          </p>
        </div>
        <div class="modal-foot">
          <button class="btn btn-ghost" :disabled="deletingBusy" @click="deleting = null">Batal</button>
          <button class="btn btn-danger" :disabled="deletingBusy" @click="confirmDelete">
            {{ deletingBusy ? 'Menghapus...' : 'Ya, hapus' }}
          </button>
        </div>
      </div>
    </div>
  </Transition>

  <!-- ================= Toast ================= -->
  <div class="toast-wrap" aria-live="polite">
    <TransitionGroup name="toast">
      <div v-for="t in toasts" :key="t.id" class="toast" :class="{ 'is-error': t.type === 'error' }">
        <AppIcon
          :name="t.type === 'error' ? 'alert' : 'check'"
          :style="{ color: t.type === 'error' ? 'var(--danger)' : 'var(--success)' }"
        />
        {{ t.text }}
      </div>
    </TransitionGroup>
  </div>
</template>
