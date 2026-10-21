import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8010/api',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('vault_access')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export function saveSession(data) {
  localStorage.setItem('vault_access', data.access)
  localStorage.setItem('vault_refresh', data.refresh)
}

export function clearSession() {
  localStorage.removeItem('vault_access')
  localStorage.removeItem('vault_refresh')
}

export function hasSession() {
  return Boolean(localStorage.getItem('vault_access'))
}

export default api
