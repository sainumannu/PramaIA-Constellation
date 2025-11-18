/**
 * Utility per costruire URL API in modo consistente
 * Centralizza la logica di costruzione degli URL per evitare hardcoding
 */

import { 
  API_BASE_URL, 
  PDK_SERVER_BASE_URL,
  PLUGIN_PDF_MONITOR_BASE_URL 
} from '../config/appConfig';

/**
 * Costruisce URL per le API del backend principale
 */
export const buildBackendApiUrl = (endpoint) => {
  // Rimuovi slash iniziale se presente
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  return `${API_BASE_URL}/${cleanEndpoint}`;
};

/**
 * Costruisce URL per le API del server PDK
 */
export const buildPDKApiUrl = (endpoint) => {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  return `${PDK_SERVER_BASE_URL}/${cleanEndpoint}`;
};

/**
 * Costruisce URL per le API del monitor PDF
 */
export const buildPDFMonitorApiUrl = (endpoint) => {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  return `${PLUGIN_PDF_MONITOR_BASE_URL}/${cleanEndpoint}`;
};

/**
 * Costruisce URL per le API del VectorstoreService attraverso il backend
 */
export const buildVectorstoreApiUrl = (endpoint) => {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  // Utilizziamo il backend come proxy per tutte le chiamate al VectorstoreService
  return `${API_BASE_URL}/${cleanEndpoint}`;
};

/**
 * URL predefiniti per le API più comuni
 */
export const API_URLS = {
  // Backend principale
  AUTH: buildBackendApiUrl('auth'),
  DOCUMENTS: buildBackendApiUrl('api/database-management/documents'),
  CHAT: buildBackendApiUrl('chat'),
  SESSIONS: buildBackendApiUrl('sessions'),
  USERS: buildBackendApiUrl('users'),
  DATABASE_MANAGEMENT: buildBackendApiUrl('api/database-management'),
  
  // Vectorstore (attraverso il backend che fa da proxy)
  VECTORSTORE: buildBackendApiUrl('api/database-management/vectorstore'),
  
  // PDK Server
  PDK_PLUGINS: buildPDKApiUrl('api/plugins'),
  PDK_EVENT_SOURCES: buildPDKApiUrl('api/event-sources'),
  PDK_TAGS: buildPDKApiUrl('api/tags'),
  
  // PDF Monitor
  PDF_MONITOR_EVENTS: buildPDFMonitorApiUrl('monitor/events')
};

/**
 * Headers standard per le richieste API
 */
export const getAuthHeaders = (additionalHeaders = {}) => {
  return {
    'Authorization': `Bearer ${localStorage.getItem('token') || 'fake-token'}`,
    'Content-Type': 'application/json',
    ...additionalHeaders
  };
};

/**
 * Configurazione standard per fetch
 */
export const createFetchConfig = (method = 'GET', body = null, additionalHeaders = {}) => {
  const config = {
    method,
    headers: getAuthHeaders(additionalHeaders)
  };
  
  if (body && method !== 'GET') {
    config.body = typeof body === 'string' ? body : JSON.stringify(body);
  }
  
  return config;
};
