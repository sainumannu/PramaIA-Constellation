# Sistema di Tag PDK - Documentazione Completa

## 📋 Panoramica

Il sistema di tag PDK (Plugin Development Kit) fornisce una soluzione completa per l'organizzazione e il filtraggio di plugin ed event sources attraverso un sistema di etichettatura gerarchico a 4 livelli.

## 🏗️ Architettura del Sistema

### Livelli di Tag Gerarchici

1. **Plugin Level** - Tag applicati all'intero plugin
2. **Node Level** - Tag specifici per i singoli nodi di elaborazione
3. **Event Source Level** - Tag per le sorgenti di eventi
4. **Event Type Level** - Tag per i tipi di eventi specifici

### Schema TypeScript

```typescript
// Interfacce core con supporto tag
interface PluginManifestSchema {
  name: string;
  version: string;
  description: string;
  tags?: string[];  // ← Tag a livello plugin
  nodes?: NodeConfigSchema[];
  // ... altri campi
}

interface NodeConfigSchema {
  id: string;
  name: string;
  tags?: string[];  // ← Tag a livello nodo
  // ... altri campi
}

interface EventSourceManifestSchema {
  id: string;
  name: string;
  tags?: string[];  // ← Tag a livello event source
  eventTypes?: EventTypeSchema[];
  // ... altri campi
}

interface EventTypeSchema {
  id: string;
  name: string;
  tags?: string[];  // ← Tag a livello event type
  // ... altri campi
}
```

## 🔧 Implementazione Backend

### API Server Extensions

Il server PDK (`plugin-api-server.js`) è stato esteso con:

#### Nuovi Endpoint

1. **GET /api/plugins** - Lista plugin con filtri tag
   ```javascript
   // Esempi di utilizzo:
   GET /api/plugins                          // Tutti i plugin
   GET /api/plugins?tags=internal,core       // Plugin con tag 'internal' OR 'core'
   GET /api/plugins?tags=internal&mode=AND   // Plugin con tag 'internal' AND altri
   GET /api/plugins?exclude_tags=deprecated  // Escludi plugin con tag 'deprecated'
   ```

2. **GET /api/event-sources** - Lista event sources con filtri tag
   ```javascript
   GET /api/event-sources?tags=monitoring    // Event sources con tag 'monitoring'
   ```

3. **GET /api/tags** - Statistiche e lista completa tag
   ```json
   {
     "tags": ["internal", "core", "monitoring", ...],
     "count": 40,
     "statistics": [
       { "tag": "text", "count": 5, "percentage": "12.5" },
       ...
     ]
   }
   ```

#### Logica di Filtro

```javascript
// Filtro per tag inclusi (AND/OR mode)
if (tags) {
    const tagList = tags.split(',').map(t => t.trim().toLowerCase());
    filteredItems = filteredItems.filter(item => {
        const itemTags = (item.tags || []).map(t => t.toLowerCase());
        
        if (mode.toLowerCase() === 'and') {
            return tagList.every(tag => itemTags.includes(tag));
        } else {
            return tagList.some(tag => itemTags.includes(tag));
        }
    });
}
```

## 🎨 Implementazione Frontend

### Componenti React

#### 1. PDKTagManagement.jsx
Componenti UI per la gestione dei tag:

- **PDKTagBadge** - Badge visuali per i tag
- **PDKTagFilter** - Pannello di filtro interattivo
- **PDKTagCloud** - Visualizzazione cloud dei tag
- **PDKTagStats** - Statistiche tag
- **PDKTagManagementPanel** - Pannello completo di gestione

#### 2. PDKPluginList.jsx
Lista plugin migliorata con:
- Integrazione tag filtering
- Pannelli espandibili
- UI responsiva
- Stati di caricamento ed errore

#### 3. PDKEventSourcesList.jsx
Lista event sources con:
- Gestione lifecycle (persistent, on-demand, scheduled)
- Controlli start/stop
- Dettagli configurazione
- Visualizzazione tag per event types

### Custom Hooks

#### usePDKData.js
```javascript
const usePDKData = () => {
  // Gestisce fetch dei dati con filtri tag
  // Fornisce stati loading/error
  // Supporta fallback per server PDK non disponibile
};

const usePDKPlugins = (initialFilters = {}) => {
  // Hook specifico per plugin
};

const usePDKEventSources = (initialFilters = {}) => {
  // Hook specifico per event sources
};
```

## 📊 Tag Semantici Predefiniti

### Plugin Categories
- `internal` - Plugin interni del sistema
- `core` - Funzionalità core
- `external` - Plugin esterni/community
- `utility` - Utilità generali
- `integration` - Plugin di integrazione

### Processing Types
- `text-processing` - Elaborazione testo
- `document` - Gestione documenti
- `pdf` - Specifico per PDF
- `semantic` - Elaborazione semantica
- `ai` - Intelligenza artificiale

### Event Source Types
- `monitoring` - Monitoraggio
- `file-system` - File system
- `database` - Database
- `api` - API/webhook
- `schedule` - Scheduling/cron

### Automation & Control
- `automation` - Automazione
- `trigger` - Trigger/eventi
- `cron` - Scheduling cron
- `recurring` - Ricorrente
- `timer` - Timer

## 🔄 Workflow di Utilizzo

### 1. Configurazione Tag nei Plugin

```json
{
  "name": "my-plugin",
  "tags": ["external", "text-processing", "utility"],
  "nodes": [
    {
      "id": "text_processor",
      "name": "Text Processor",
      "tags": ["text", "clean", "filter"]
    }
  ]
}
```

### 2. Configurazione Tag negli Event Sources

```json
{
  "name": "file-monitor",
  "tags": ["monitoring", "file-system", "automation"],
  "eventTypes": [
    {
      "id": "file_added",
      "name": "File Added",
      "tags": ["file-system", "trigger"]
    }
  ]
}
```

### 3. Utilizzo Frontend

```jsx
import { PDKTagManagementPanel } from './PDKTagManagement';
import { usePDKPlugins } from '../hooks/usePDKData';

const MyComponent = () => {
  const { plugins, updateFilters } = usePDKPlugins();
  
  return (
    <div>
      <PDKTagManagementPanel
        items={plugins}
        onItemsFilter={setFilteredItems}
        showStats={true}
        showCloud={true}
      />
    </div>
  );
};
```

## 🧪 Testing e Validazione

### Test API
```bash
# Test endpoint plugin
curl "http://localhost:3001/api/plugins?tags=internal"

# Test endpoint event sources  
curl "http://localhost:3001/api/event-sources?tags=monitoring"

# Test statistiche tag
curl "http://localhost:3001/api/tags"
```

### Test Frontend
### Test Frontend
- File di test standalone è stato rimosso per pulizia

### Documentazione
- Componenti React: `PDKDashboard.jsx`
- Mock data per sviluppo

## 📈 Vantaggi del Sistema

### 1. Organizzazione
- Categorizzazione gerarchica
- Filtraggio avanzato
- Ricerca semantica

### 2. User Experience
- Interfaccia intuitiva
- Visualizzazione chiara
- Interazione fluida

### 3. Scalabilità
- Sistema estensibile
- Performance ottimizzate
- Cache intelligente

### 4. Manutenibilità
- Codice modulare
- Documentazione completa
- Test automatizzati

## 🔧 Configurazione e Setup

### 1. Server PDK
```bash
cd PramaIA-PDK/server
node plugin-api-server.js
# Server disponibile su localhost:3001
```

### 2. Frontend Integration
```jsx
// Importa componenti
import PDKDashboard from './components/PDKDashboard';
import { usePDKData } from './hooks/usePDKData';

// Utilizza nel tuo app
<PDKDashboard />
```

### 3. Plugin Configuration
Aggiungi tag nei file `plugin.json`:
```json
{
  "tags": ["category", "type", "functionality"]
}
```

## 🚀 Roadmap Future

### Funzionalità Pianificate
- [ ] Tag autocomplete
- [ ] Tag suggestions basate su ML
- [ ] Esportazione configurazioni tag
- [ ] Tag validation rules
- [ ] Tag analytics dashboard
- [ ] API GraphQL per query complesse

### Miglioramenti UI/UX
- [ ] Drag & drop per tag management
- [ ] Visualizzazioni alternative (grid, card)
- [ ] Filtri salvati/favoriti
- [ ] Dark mode support
- [ ] Mobile responsive optimization

## 📝 Note Implementative

### Backward Compatibility
- Sistema completamente retrocompatibile
- Plugin senza tag funzionano normalmente
- Graceful degradation per API legacy

### Performance
- Caching intelligente dei tag
- Lazy loading per grandi dataset
- Debouncing per filtri real-time

### Security
- Validazione input tag
- Sanitizzazione XSS
- Rate limiting su API

---

**Sistema implementato con successo!** 🎉

Il sistema di tag PDK è ora completamente operativo e integrato in PramaIA, fornendo un'esperienza di gestione plugin ed event sources di livello enterprise con funzionalità avanzate di organizzazione e filtraggio.
