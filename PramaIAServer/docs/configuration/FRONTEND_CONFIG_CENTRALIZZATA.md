# Configurazione Centralizzata Frontend

## Panoramica

Questo documento descrive il sistema di configurazione centralizzata implementato per eliminare i riferimenti hardcoded a indirizzi IP e porte nel frontend React.

## Struttura dei File di Configurazione

### 1. `/src/config/appConfig.js`
File principale di configurazione che definisce:
- **Porte**: Backend, Frontend, PDK Server, PDF Monitor Plugin
- **URL Base**: URL completi per tutti i servizi
- **URL API**: Endpoint specifici per diverse funzionalità
- **Configurazioni**: Workflow, categorie nodi, mappature tag

### 2. `/src/config.js`
Configurazione legacy con supporto per variabili d'ambiente:
```javascript
export const config = {
  BACKEND_URL: process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000',
  FRONTEND_URL: process.env.REACT_APP_FRONTEND_URL || 'http://localhost:3000'
};
```

### 3. `/src/utils/apiUtils.js`
Utility per costruire URL e configurazioni fetch in modo consistente.

## Come Utilizzare la Configurazione

### Metodo 1: Import Diretto dalla Configurazione
```javascript
import { API_BASE_URL, PDK_SERVER_BASE_URL } from '../config/appConfig';

// Uso
const response = await fetch(`${API_BASE_URL}/api/documents/`);
```

### Metodo 2: Utilizzare le Utility API (Raccomandato)
```javascript
import { API_URLS, createFetchConfig } from '../utils/apiUtils';

// Uso semplificato
const response = await fetch(API_URLS.DOCUMENTS, createFetchConfig());

// Con POST
const response = await fetch(
  API_URLS.DOCUMENTS, 
  createFetchConfig('POST', { name: 'test.pdf' })
);
```

## Variabili d'Ambiente Supportate

Puoi sovrascrivere le configurazioni usando variabili d'ambiente:

```bash
# .env file
REACT_APP_BACKEND_PORT=8000
REACT_APP_FRONTEND_PORT=3000
REACT_APP_PDK_SERVER_PORT=3001
REACT_APP_PLUGIN_PDF_MONITOR_PORT=8001

# URL completi (sovrascrivono le porte)
REACT_APP_BACKEND_BASE_URL=http://localhost:8000
REACT_APP_PDK_SERVER_BASE_URL=http://localhost:3001
```

## Migrazione dai Riferimenti Hardcoded

### Prima (Hardcoded):
```javascript
const response = await fetch('http://localhost:8000/api/documents/', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`,
    'Content-Type': 'application/json'
  }
});
```

### Dopo (Configurabile):
```javascript
import { API_URLS, createFetchConfig } from '../utils/apiUtils';

const response = await fetch(API_URLS.DOCUMENTS, createFetchConfig());
```

## File Aggiornati

I seguenti file sono stati aggiornati per utilizzare la configurazione centralizzata:

### Componenti React:
- ✅ `DatabaseManagementSimple.jsx`
- ✅ `DocumentManagement.jsx` 
- ✅ `UserManager.jsx`
- ✅ `PDFProcessingMonitor.jsx`
- ✅ `PDKEventSourcesList.jsx`
- ✅ `PDKConfigDebugger.jsx`

### Hook Personalizzati:
- ✅ `usePDKData.js`
- ✅ `useEventSources.js`

### File di Workflow:
- ✅ `NodePalette.js`
- ✅ `DynamicPDKNodes.js`

## Benefici

1. **Manutenibilità**: Un singolo punto di configurazione
2. **Flessibilità**: Supporto per diversi ambienti (dev, staging, prod)
3. **Scalabilità**: Facile aggiunta di nuovi servizi
4. **Debugging**: Configurazione centralizzata facilita il troubleshooting
5. **Deploy**: Possibilità di configurare tramite variabili d'ambiente

## Esempi d'Uso Comuni

### Chiamate API Backend:
```javascript
import { API_URLS, createFetchConfig } from '../utils/apiUtils';

// GET
const users = await fetch(API_URLS.USERS, createFetchConfig());

// POST
const newDoc = await fetch(
  API_URLS.DOCUMENTS, 
  createFetchConfig('POST', { filename: 'test.pdf' })
);

// Con endpoint personalizzato
import { buildBackendApiUrl } from '../utils/apiUtils';
const customUrl = buildBackendApiUrl('api/custom/endpoint');
```

### Chiamate PDK Server:
```javascript
import { API_URLS, buildPDKApiUrl } from '../utils/apiUtils';

// Plugin standard
const plugins = await fetch(API_URLS.PDK_PLUGINS);

// Event sources
const sources = await fetch(API_URLS.PDK_EVENT_SOURCES);

// Endpoint personalizzato
const customPDK = buildPDKApiUrl('api/custom/pdk');
```

## Note per gli Sviluppatori

1. **Non usare mai URL hardcoded** nei nuovi componenti
2. **Utilizzare sempre** le utility in `apiUtils.js` per nuove implementazioni
3. **Testare** con diverse configurazioni di ambiente
4. **Documentare** nuovi endpoint aggiunti alla configurazione
