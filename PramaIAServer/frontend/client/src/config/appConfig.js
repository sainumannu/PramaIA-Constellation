// Configurazione globale per il frontend
// Tutte le costanti di configurazione dovrebbero essere definite qui
// per evitare hardcoding nei componenti

// Configurazione delle porte (leggibili da variabili d'ambiente se disponibili)
export const BACKEND_PORT = process.env.REACT_APP_BACKEND_PORT || 8000;
export const FRONTEND_PORT = process.env.REACT_APP_FRONTEND_PORT || 3000;
export const PLUGIN_DOCUMENT_MONITOR_PORT = process.env.REACT_APP_DOCUMENT_MONITOR_PORT || 8001;
export const PDK_SERVER_PORT = process.env.REACT_APP_PDK_SERVER_PORT || 3001;
export const VECTORSTORE_PORT = process.env.REACT_APP_VECTORSTORE_PORT || 8090;

// URL di base per i servizi
export const BACKEND_BASE_URL = process.env.REACT_APP_BACKEND_BASE_URL || `http://localhost:${BACKEND_PORT}`;
export const FRONTEND_BASE_URL = process.env.REACT_APP_FRONTEND_BASE_URL || `http://localhost:${FRONTEND_PORT}`;
export const PLUGIN_DOCUMENT_MONITOR_BASE_URL = process.env.REACT_APP_DOCUMENT_MONITOR_BASE_URL || `http://localhost:${PLUGIN_DOCUMENT_MONITOR_PORT}`;
export const PDK_SERVER_BASE_URL = process.env.REACT_APP_PDK_SERVER_BASE_URL || `http://localhost:${PDK_SERVER_PORT}`;
export const VECTORSTORE_BASE_URL = process.env.REACT_APP_VECTORSTORE_BASE_URL || `http://localhost:${VECTORSTORE_PORT}`;

// Retrocompatibilità per il vecchio nome PDF Monitor
export const PLUGIN_PDF_MONITOR_BASE_URL = PLUGIN_DOCUMENT_MONITOR_BASE_URL;

// URL specifici dell'API
export const API_BASE_URL = BACKEND_BASE_URL;
export const AUTH_BASE_URL = `${BACKEND_BASE_URL}/auth`;
export const DOCUMENTS_BASE_URL = `${BACKEND_BASE_URL}/documents`;
export const CHAT_BASE_URL = `${BACKEND_BASE_URL}/chat`;
export const SESSIONS_BASE_URL = `${BACKEND_BASE_URL}/sessions`;
export const USERS_BASE_URL = `${BACKEND_BASE_URL}/users`;
export const USAGE_BASE_URL = `${BACKEND_BASE_URL}/usage`;
export const LLM_BASE_URL = `${BACKEND_BASE_URL}/llm`;

// URL specifici per il PDK
export const PDK_API_BASE_URL = PDK_SERVER_BASE_URL;
export const PDK_PLUGINS_URL = `${PDK_API_BASE_URL}/plugins`;
export const PDK_EVENT_SOURCES_URL = `${PDK_API_BASE_URL}/event-sources`;
export const PDK_TAGS_URL = `${PDK_API_BASE_URL}/tags`;

// URL specifici per il PDK tramite backend (proxy)
export const PDK_BACKEND_API_BASE_URL = BACKEND_BASE_URL + '/api/pdk';
export const PDK_BACKEND_PLUGINS_URL = `${PDK_BACKEND_API_BASE_URL}/plugins`;
export const PDK_BACKEND_EVENT_SOURCES_URL = `${PDK_BACKEND_API_BASE_URL}/event-sources`;

// Configurazioni specifiche
export const OLLAMA_DEFAULT_URL = process.env.REACT_APP_OLLAMA_URL || 'http://localhost:11434';

// Configurazioni Workflow
export const WORKFLOW_CATEGORIES = [
  { value: 'General', label: 'Generale' },
  { value: 'PDF Processing', label: 'Elaborazione PDF' },
  { value: 'Data Analysis', label: 'Analisi Dati' },
  { value: 'API Integration', label: 'Integrazione API' },
  { value: 'AI Models', label: 'Modelli AI' },
  { value: 'Text Processing', label: 'Elaborazione Testo' },
  { value: 'Advanced', label: 'Avanzato' }
];

// Configurazioni Node Palette - Categorie funzionali per tutti i nodi (inclusi PDK)
export const NODE_CATEGORIES = [
  { value: 'input', label: 'Input', description: 'Nodi per l\'acquisizione di dati' },
  { value: 'processing', label: 'Elaborazione', description: 'Nodi per l\'elaborazione generale dei dati' },
  { value: 'llm', label: 'LLM', description: 'Nodi per l\'integrazione con modelli linguistici' },
  { value: 'pdf', label: 'PDF', description: 'Nodi specifici per l\'elaborazione di documenti PDF' },
  { value: 'database', label: 'Database', description: 'Nodi per operazioni su database' },
  { value: 'output', label: 'Output', description: 'Nodi per l\'output e la visualizzazione' },
  { value: 'integration', label: 'Integrazione', description: 'Nodi per l\'integrazione con servizi esterni' },
  { value: 'utility', label: 'Utilità', description: 'Nodi di utilità generale' }
];

// Mappa di associazione tag -> categoria per l'inferenza automatica
export const TAG_TO_CATEGORY_MAP = {
  // Categorie di input
  'input': 'input',
  'source': 'input',
  'reader': 'input',
  'import': 'input',
  
  // Categorie di elaborazione
  'processing': 'processing',
  'transform': 'processing',
  'filter': 'processing',
  'converter': 'processing',
  
  // Categorie LLM
  'llm': 'llm',
  'ai': 'llm',
  'ml': 'llm',
  'model': 'llm',
  'gpt': 'llm',
  
  // Categorie PDF
  'pdf': 'pdf',
  'document': 'pdf',
  'ocr': 'pdf',
  
  // Categorie database
  'database': 'database',
  'db': 'database',
  'sql': 'database',
  'storage': 'database',
  
  // Categorie output
  'output': 'output',
  'export': 'output',
  'writer': 'output',
  'display': 'output',
  
  // Categorie integrazione
  'integration': 'integration',
  'api': 'integration',
  'external': 'integration',
  'service': 'integration',
  
  // Categorie utilità
  'utility': 'utility',
  'tool': 'utility',
  'helper': 'utility',
  'misc': 'utility'
};
