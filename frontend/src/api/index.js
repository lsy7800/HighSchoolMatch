import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// Attach admin token (if present) to every request.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On 401 from an admin route, drop the token so the guard redirects to login.
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('admin_token')
    }
    return Promise.reject(err)
  }
)

// ---- public ----
export const getYears = () => api.get('/years').then((r) => r.data)
export const recommend = (payload) => api.post('/recommend', payload).then((r) => r.data)
export const getSchool = (code) => api.get(`/schools/${code}`).then((r) => r.data)

// ---- admin ----
export const adminLogin = (username, password) => {
  const form = new URLSearchParams()
  form.append('username', username)
  form.append('password', password)
  return api.post('/admin/login', form).then((r) => r.data)
}
export const adminMe = () => api.get('/admin/me').then((r) => r.data)
export const adminListSchools = (params) =>
  api.get('/admin/schools', { params }).then((r) => r.data)
export const adminGetSchool = (id) => api.get(`/admin/schools/${id}`).then((r) => r.data)
export const adminCreateSchool = (payload) =>
  api.post('/admin/schools', payload).then((r) => r.data)
export const adminUpdateSchool = (id, payload) =>
  api.put(`/admin/schools/${id}`, payload).then((r) => r.data)
export const adminDeleteSchool = (id) =>
  api.delete(`/admin/schools/${id}`).then((r) => r.data)
export const adminUpsertStat = (id, payload) =>
  api.put(`/admin/schools/${id}/stat`, payload).then((r) => r.data)
export const adminDeleteStat = (id, year) =>
  api.delete(`/admin/schools/${id}/stat/${year}`).then((r) => r.data)
export const adminGetConfig = () => api.get('/admin/config').then((r) => r.data)
export const adminUpdateConfig = (values) =>
  api.put('/admin/config', { values }).then((r) => r.data)

export const adminImport = (kind, file, commit) => {
  const form = new FormData()
  form.append('file', file)
  form.append('commit', commit ? 'true' : 'false')
  return api
    .post(`/admin/import/${kind}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((r) => r.data)
}

export default api
