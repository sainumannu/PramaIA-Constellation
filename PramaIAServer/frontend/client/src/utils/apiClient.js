// API client con interceptor per autenticazione
import axios from 'axios';
import config from '../config';

// Crea un'istanza di axios con configurazione di base
const apiClient = axios.create({
  baseURL: config.BACKEND_URL,
  timeout: 10000,
});

// Interceptor per aggiungere automaticamente il token di autenticazione
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor per gestire errori di autenticazione
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Token scaduto o non valido, rimuovi il token e reindirizza al login
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
