import axios from 'axios'

// Alamat API diambil dari variabel lingkungan (.env), tidak ditulis mati di komponen.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { Accept: 'application/json' },
})

// Kirim token di setiap permintaan setelah login
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Kalau token ditolak (401), hapus token lalu kembali ke halaman login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const sedangDiLogin = window.location.pathname === '/login'
    if (error.response?.status === 401 && !sedangDiLogin) {
      localStorage.removeItem('token')
      window.location.assign('/login')
    }
    return Promise.reject(error)
  },
)

export default api
