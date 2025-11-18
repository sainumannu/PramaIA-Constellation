import axios from 'axios';

// Crea una istanza di axios con la configurazione di base
const api = axios.create({
  baseURL: process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Interceptor per aggiungere il token di autenticazione
api.interceptors.request.use(
  config => {
    // Leggi il token SEMPRE al momento della richiesta
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('[API] Token presente, Authorization header aggiunto');
    } else {
      console.warn('[API] Nessun token trovato in localStorage');
    }
    return config;
  },
  error => {
    console.error('Error in request interceptor:', error);
    return Promise.reject(error);
  }
);

// Interceptor per gestire gli errori di autenticazione
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      console.log('Authentication error, redirecting to login...');
      localStorage.removeItem('token');
      // Reindirizza al login solo se non siamo già sulla pagina di login
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    } else if (error.message === 'Network Error') {
      alert('Errore di rete: il backend non risponde o CORS non configurato.');
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const endpoints = {
  documents: {
    list: () => api.get('/api/database-management/documents/public/'),
    delete: (filename) => api.delete(`/api/database-management/documents/${filename}`),
    upload: (formData) => api.post('/api/database-management/documents/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }),
    status: () => api.get('/api/database-management/documents/status/public/')
  },
  sessions: {
    list: () => api.get('/sessions/'),
    create: (data) => api.post('/sessions/new', data),
    delete: (sessionId) => api.delete(`/sessions/${sessionId}`),
    getStatus: (sessionId) => api.get(`/sessions/${sessionId}/status`),
    getSources: (sessionId) => api.get(`/sessions/${sessionId}/sources`),
    updateSources: (sessionId, sources) => api.post(`/sessions/${sessionId}/sources`, { sources })
  },
  chat: {
    ask: (data) => api.post('/chat/ask/', data),
    ollamaModels: () => api.get('/api/ollama/models')
  },
  ollama: {
    status: () => api.get('/api/ollama/status'),
    health: () => api.get('/api/ollama/health'),
    models: () => api.get('/api/ollama/models'),
    recommendedModels: () => api.get('/api/ollama/models/recommended'),
    pullModel: (modelName) => api.post(`/api/ollama/models/${modelName}/pull`),
    testGeneration: (data) => api.post('/api/ollama/test', data),
    modelInfo: (modelName) => api.get(`/api/ollama/models/${modelName}/info`)
  },
  auth: {
    localLogin: (formData) => api.post('/auth/token/local', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }),
    register: (userData) => api.post('/auth/register', userData)
  },
  admin: {
    listUsers: () => api.get('/admin/users/'),
    createUser: (data) => api.post('/admin/users/', data),
    updateUser: (userId, data) => api.put(`/admin/users/${userId}`, data),
    deleteUser: (userId) => api.delete(`/admin/users/${userId}`)
  },
  protected: {
    me: () => api.get('/protected/me')
  },
  ollama: {
    health: () => api.get('/api/ollama/health'),
    status: () => api.get('/api/ollama/status'),
    models: () => api.get('/api/ollama/models'),
    recommendedModels: () => api.get('/api/ollama/models/recommended'),
    pullModel: (modelName) => api.post(`/api/ollama/models/${modelName}/pull`),
    modelInfo: (modelName) => api.get(`/api/ollama/models/${modelName}/info`),
    test: (data) => api.post('/api/ollama/test', data)
  }
};

export default api;
