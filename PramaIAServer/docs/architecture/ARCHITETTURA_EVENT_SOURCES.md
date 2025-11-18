# Architettura Event Sources Modulari - PramaIA

## Panoramica

Il sistema dovrebbe permettere la registrazione dinamica di "Event Sources" (sorgenti di eventi) 
che possono generare trigger per i workflow, proprio come il sistema PDK per i nodi.

## Struttura di un Event Source

Ogni Event Source dovrebbe avere la seguente struttura:

```json
{
  "id": "pdf-monitor-source",
  "name": "PDF Monitor",
  "description": "Monitora cartelle per nuovi file PDF",
  "version": "1.0.0",
  "eventTypes": [
    {
      "type": "pdf_uploaded",
      "label": "PDF Caricato",
      "description": "Quando un nuovo PDF viene rilevato",
      "schema": {
        "properties": {
          "filePath": {"type": "string", "description": "Percorso del file"},
          "fileName": {"type": "string", "description": "Nome del file"},
          "fileSize": {"type": "number", "description": "Dimensione in bytes"},
          "timestamp": {"type": "string", "format": "datetime"}
        }
      }
    }
  ],
  "configSchema": {
    "type": "object",
    "properties": {
      "watchPath": {
        "type": "string",
        "title": "Cartella da monitorare",
        "description": "Percorso della cartella da monitorare"
      },
      "extensions": {
        "type": "array", 
        "items": {"type": "string"},
        "title": "Estensioni file",
        "default": [".pdf"]
      }
    },
    "required": ["watchPath"]
  },
  "webhookEndpoint": "/api/events/pdf-monitor",
  "status": "active"
}
```

## Architettura del Sistema

### 1. Event Sources Registry (Backend)

```python
# backend/core/event_sources_registry.py
class EventSourceRegistry:
    def __init__(self):
        self.sources = {}
    
    def register_source(self, source_config):
        """Registra una nuova sorgente di eventi"""
        self.sources[source_config['id']] = source_config
    
    def get_available_sources(self):
        """Ritorna tutte le sorgenti disponibili"""
        return list(self.sources.values())
    
    def get_event_types_for_source(self, source_id):
        """Ritorna i tipi di eventi per una sorgente specifica"""
        source = self.sources.get(source_id)
        return source['eventTypes'] if source else []
```

### 2. Event Source Plugin Structure

```
PramaIA-EventSources/
├── pdf-monitor-source/
│   ├── source.json          # Manifest della sorgente
│   ├── handler.py           # Logica di gestione eventi
│   ├── README.md           # Documentazione
│   └── requirements.txt    # Dipendenze Python
├── scheduler-source/
│   ├── source.json
│   ├── handler.py
│   └── cron_utils.py
└── api-webhook-source/
    ├── source.json
    ├── handler.py
    └── webhook_validator.py
```

### 3. Dynamic API Endpoints

Il sistema dovrebbe creare dinamicamente endpoint per ogni sorgente:

```python
# backend/routers/dynamic_event_sources.py
from fastapi import APIRouter, Depends
from backend.core.event_sources_registry import EventSourceRegistry

router = APIRouter()
registry = EventSourceRegistry()

def create_dynamic_endpoints():
    """Crea endpoint dinamici per ogni sorgente registrata"""
    for source in registry.get_available_sources():
        endpoint = source['webhookEndpoint']
        
        @router.post(endpoint)
        async def handle_event(event_data: dict, source_id: str = source['id']):
            # Logica per processare l'evento e triggere i workflow
            await process_event(source_id, event_data)
```

### 4. Frontend Dinamico

Il frontend dovrebbe caricare dinamicamente le sorgenti disponibili:

```javascript
// services/eventSourcesApi.js
export const eventSourcesApi = {
  async getAvailableSources() {
    const response = await axios.get('/api/event-sources');
    return response.data;
  },
  
  async getEventTypesForSource(sourceId) {
    const response = await axios.get(`/api/event-sources/${sourceId}/events`);
    return response.data;
  }
};
```

## Implementazione delle Sorgenti Specifiche

### PDF Monitor Source
- **Tipo**: File System Watcher
- **Eventi**: `pdf_uploaded`, `pdf_modified`, `pdf_deleted`
- **Config**: Cartelle da monitorare, filtri estensioni
- **Handler**: Monitora filesystem, invia webhook al server

### API Webhook Source  
- **Tipo**: HTTP Endpoint
- **Eventi**: `api_call_received`, `webhook_triggered`
- **Config**: Endpoint personalizzati, autenticazione
- **Handler**: Espone endpoint REST, valida richieste

### Scheduler Source
- **Tipo**: Cron/Timer
- **Eventi**: `scheduled_trigger`, `recurring_event`
- **Config**: Espressioni cron, timezone
- **Handler**: Gestisce timer, invia eventi programmati

### Sistema Source (Built-in)
- **Tipo**: Interno al sistema
- **Eventi**: `user_login`, `workflow_completed`, `error_occurred`
- **Config**: Livelli di log, filtri eventi
- **Handler**: Ascolta eventi interni del sistema

## Vantaggi di questa Architettura

1. **Estensibilità**: Nuove sorgenti senza modificare il core
2. **Modularità**: Ogni sorgente è indipendente
3. **Consistenza**: Schema uniforme come i PDK
4. **Manutenibilità**: Logica separata per ogni tipo di evento
5. **Configurabilità**: Ogni sorgente ha il suo schema di config
6. **Scalabilità**: Facile aggiungere nuovi tipi di eventi

## Esempio di Utilizzo

1. Un developer crea una nuova "email-source"
2. La registra nel sistema con il suo manifest
3. Il sistema automaticamente:
   - Espone gli endpoint necessari
   - Aggiorna il frontend con i nuovi tipi di eventi
   - Permette la configurazione tramite UI
4. Gli utenti possono creare trigger basati su eventi email
