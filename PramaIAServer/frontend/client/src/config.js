// Configurazione centralizzata per il frontend
export const config = {
  BACKEND_URL: process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000',
  FRONTEND_URL: process.env.REACT_APP_FRONTEND_URL || 'http://localhost:3000'
};

// Backward compatibility
export const API_BASE_URL = config.BACKEND_URL;

export default config;
