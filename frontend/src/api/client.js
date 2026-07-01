import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auth
export const login = async (email, password) => {
  const { data } = await api.post('/auth/login', { email, password })
  return data
}

export const register = async (name, email, password) => {
  const { data } = await api.post('/auth/register', { name, email, password })
  return data
}

export const refreshToken = async (token) => {
  const { data } = await api.post('/auth/refresh', { token })
  return data
}

// Collections
export const createCollection = async (name, visibility = 'private') => {
  const { data } = await api.post('/collections', { name, visibility })
  return data
}

export const listCollections = async () => {
  const { data } = await api.get('/collections')
  return data
}

// Ingest
export const ingestDocuments = async (
  collection,
  files,
  options = {}
) => {
  const formData = new FormData()
  formData.append('collection', collection || 'default')
  files.forEach((file) => formData.append('files', file))
  if (options.chunk_size) formData.append('chunk_size', options.chunk_size.toString())
  if (options.overlap) formData.append('overlap', options.overlap.toString())
  if (options.embed_model) formData.append('embed_model', options.embed_model)

  const { data } = await api.post('/ingest', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

// Chat with SSE streaming
export const chatStream = async (
  collection,
  query,
  options = {},
  onToken,
  onSources,
  onError
) => {
  const token = localStorage.getItem('token')
  const url = `${API_BASE}/chat`

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: token ? `Bearer ${token}` : '',
    },
    body: JSON.stringify({
      collection: collection || 'default',
      query,
      k: options.k || 12,
      rerank_k: options.rerank_k || 6,
      model: options.model,
      max_tokens: options.max_tokens || 600,
      citations: options.citations !== false,
    }),
  })

  if (!response.ok) {
    onError(`HTTP error! status: ${response.status}`)
    return
  }

  const reader = response.body?.getReader()
  const decoder = new TextDecoder()

  if (!reader) {
    onError('No response body')
    return
  }

  let buffer = ''
  let sources = []

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const json = JSON.parse(line.slice(6))
          if (json.error) {
            onError(json.error)
            return
          }
          if (json.token) {
            onToken(json.token)
          }
          if (json.done && json.sources) {
            sources = json.sources
            onSources(sources)
          }
        } catch (e) {
          console.error('Failed to parse SSE data:', e)
        }
      }
    }
  }
}

export default api
