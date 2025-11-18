// DEBUG_CONFIG.js
// File di configurazione centrale per le impostazioni di debug

const DEBUG_CONFIG = {
  // Impostazioni generali
  ENABLE_DEBUG_MODE: false,       // Modalità debug generale
  SHOW_DEBUG_SECTIONS: false,     // Mostra sezioni di debug nell'UI
  VERBOSE_LOGGING: false,         // Log dettagliati nella console
  
  // Impostazioni specifiche
  WORKFLOW_EDITOR: {
    SHOW_PDK_DEBUG: false,        // Mostra sezione debug PDK
    SHOW_NODE_IDS: false,         // Mostra ID nodi nei tooltip
    HIGHLIGHT_TEST_NODES: false,  // Evidenzia nodi di test
    LOG_NODE_EVENTS: false        // Log eventi dei nodi
  },
  
  // Endpoint API 
  API: {
    USE_MOCK_DATA: false,         // Usa dati mock per le API
    LOG_REQUESTS: false,          // Log delle richieste API
    LOG_RESPONSES: false,         // Log delle risposte API
  }
};

export default DEBUG_CONFIG;
