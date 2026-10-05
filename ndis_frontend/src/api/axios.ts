import axios from 'axios'

// ── Authenticated API instance (for protected routes) ────────────────────────
const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ndis_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Redirect to login on 401 (for protected routes only)
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('ndis_token')
      localStorage.removeItem('ndis_user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ── Public API instance (for login / forgot-password — no redirect on 401) ──
export const publicApi = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

export default api
