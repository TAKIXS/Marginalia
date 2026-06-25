import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 15000 })

// Global response interceptor for consistent error handling
api.interceptors.response.use(
  (res) => res,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail

    if (status === 500) {
      // Already handled by backend — just show generic message
      console.error('Server error:', detail || error.message)
    } else if (status === 404) {
      // Let components handle 404 for specific resources, others are generic
      if (!error.config?.url?.match(/\/\d+$/)) {
        console.error('Not found:', error.config?.url)
      }
    } else if (!error.response) {
      console.error('Network error — server may be down')
    }
    // 400 errors are passed through for components to handle specifically
    return Promise.reject(error)
  }
)

// ── Books ──────────────────────────────────────────

export const getBooks = () => api.get('/books')
export const createBook = (data) => api.post('/books', data)
export const deleteBook = (id) => api.delete(`/books/${id}`)
export const getBook = (id) => api.get(`/books/${id}`)
export const updateBook = (id, data) => api.put(`/books/${id}`, data)
export const getBookGroups = (bookId) => api.get('/books/groups', { params: bookId ? { book_id: bookId } : {} })

// ── Excerpts ───────────────────────────────────────

export const createExcerpt = (data) => api.post('/excerpts', data)
export const getExcerpts = (params) => api.get('/excerpts', { params })
export const getExcerpt = (id) => api.get(`/excerpts/${id}`)
export const updateExcerpt = (id, data) => api.put(`/excerpts/${id}`, data)
export const deleteExcerpt = (id) => api.delete(`/excerpts/${id}`)
export const getRandomExcerpt = () => api.get('/excerpts/random')
export const toggleFavorite = (id) => api.put(`/excerpts/${id}/favorite`)
export const exportExcerpts = (params) => api.get('/excerpts/export', { params, responseType: 'blob' })
export const batchDeleteExcerpts = (ids) => api.post('/excerpts/batch-delete', { ids })
export const batchTagExcerpts = (ids, tag_ids) => api.post('/excerpts/batch-tag', { ids, tag_ids })

// ── Upload ─────────────────────────────────────────

export const uploadImage = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/excerpts/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// ── Tags ───────────────────────────────────────────

export const getTags = () => api.get('/tags')
export const createTag = (data) => api.post('/tags', data)
export const updateTag = (id, data) => api.put(`/tags/${id}`, data)
export const deleteTag = (id) => api.delete(`/tags/${id}`)

export default api
