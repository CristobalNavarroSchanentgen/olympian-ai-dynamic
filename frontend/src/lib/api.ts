import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('olympian-token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('olympian-token')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

export default api

// Typed API methods
export const discoveryAPI = {
  scan: () => api.get('/discovery/scan'),
  getStatus: () => api.get('/discovery/status'),
  getServices: () => api.get('/discovery/services'),
}

export const ollamaAPI = {
  discover: () => api.get('/ollama/discover'),
  getModels: (endpoint?: string) => 
    api.get('/ollama/models', { params: { endpoint } }),
  getAllModels: () => api.get('/ollama/models/all'),
  chat: (data: any) => api.post('/ollama/chat', data),
  pullModel: (data: any) => api.post('/ollama/models/pull', data),
}

export const configAPI = {
  getDynamic: () => api.get('/config/dynamic'),
  getPreferences: () => api.get('/config/preferences'),
  updatePreferences: (data: any) => api.put('/config/preferences', data),
  addOverride: (data: any) => api.post('/config/override', data),
  removeOverride: (serviceType: string) => 
    api.delete(`/config/override/${serviceType}`),
}

export const projectAPI = {
  list: (activeOnly?: boolean) => 
    api.get('/projects', { params: { active_only: activeOnly } }),
  get: (id: string) => api.get(`/projects/${id}`),
  create: (data: any) => api.post('/projects', data),
  update: (id: string, data: any) => api.put(`/projects/${id}`, data),
  delete: (id: string) => api.delete(`/projects/${id}`),
  duplicate: (id: string, newName?: string) => 
    api.post(`/projects/${id}/duplicate`, { new_name: newName }),
}

export const chatAPI = {
  sendMessage: (data: any) => api.post('/chat/message', data),
  listConversations: (projectId?: string, limit?: number, offset?: number) => 
    api.get('/chat/conversations', { 
      params: { project_id: projectId, limit, offset } 
    }),
  getConversation: (id: string) => api.get(`/chat/conversations/${id}`),
  createConversation: (data: any) => api.post('/chat/conversations', data),
  deleteConversation: (id: string) => api.delete(`/chat/conversations/${id}`),
  clearConversation: (id: string) => api.post(`/chat/conversations/${id}/clear`),
  regenerateResponse: (id: string) => api.post(`/chat/regenerate/${id}`),
}

export const systemAPI = {
  getResources: () => api.get('/system/resources'),
  getCapacity: () => api.get('/system/capacity'),
  optimize: () => api.post('/system/optimize'),
  getProcesses: () => api.get('/system/processes'),
  getMetrics: () => api.get('/system/metrics'),
  getLimits: () => api.get('/system/limits'),
}