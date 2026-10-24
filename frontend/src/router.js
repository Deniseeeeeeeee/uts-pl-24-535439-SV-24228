import { createRouter, createWebHistory } from 'vue-router'
import LoginView from './views/LoginView.vue'
import MoviesView from './views/MoviesView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    { path: '/', name: 'movies', component: MoviesView, meta: { requiresAuth: true } },
  ],
})

// Halaman yang butuh login tidak bisa dibuka tanpa token
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) return { name: 'login' }
  if (to.name === 'login' && token) return { name: 'movies' }
})

export default router
