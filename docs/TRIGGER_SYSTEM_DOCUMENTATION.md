# Documentazione Sistema Trigger PramaIA

## Panoramica

Il sistema trigger di PramaIA implementa un'architettura event-driven che collega automaticamente eventi del sistema (upload di file, query di ricerca, modifiche filesystem) ai workflow corrispondenti. Questo documento descrive i trigger attualmente configurati e operativi.

## Architettura Trigger

```
Event Producer → Trigger Engine → Workflow Execution
     ↓               ↓               ↓
PDF Monitor → pdf_file_added → CREATE Pipeline (10 nodi)
PDF Monitor → pdf_file_updated → UPDATE Pipeline (11 nodi)  
PDF Monitor → pdf_file_deleted → DELETE Pipeline (12 nodi)
Search API → pdf_search_query → READ Pipeline (10 nodi)
```

## Trigger Configurati

### 1. PDF File Added Trigger

**Trigger ID:** `Trigger Aggiunta PDF`
- **Event Type:** `pdf_file_added`
- **Source:** `pdf-monitor-event-source`
- **Target Workflow:** PDF Document CREATE Pipeline (`wf_7af99caf311a`)
- **Status:** ✅ Attivo
- **Nodi Workflow:** 10

**Descrizione:** Si attiva quando viene rilevato un nuovo file PDF nel sistema di monitoraggio. Avvia il workflow di creazione che include parsing del documento, estrazione metadati, e archiviazione.

**Payload Evento Esempio:**
```json
{
  "event_type": "pdf_file_added",
  "data": {
    "file_path": "/uploads/document.pdf",
    "file_size": 2048576,
    "mime_type": "application/pdf",
    "created_at": "2025-11-15T10:00:00Z"
  },
  "metadata": {
    "source": "pdf-monitor-event-source",
    "timestamp": "2025-11-15T10:00:00Z"
  }
}
```

### 2. PDF File Updated Trigger

**Trigger ID:** `Trigger Aggiornamento PDF`
- **Event Type:** `pdf_file_updated`
- **Source:** `pdf-monitor-event-source`
- **Target Workflow:** PDF Document UPDATE Pipeline (`wf_fcad5d0befdb`)
- **Status:** ✅ Attivo
- **Nodi Workflow:** 11

**Descrizione:** Si attiva quando viene modificato un file PDF esistente. Gestisce l'aggiornamento dei metadati, rielaborazione del contenuto e versioning.

**Payload Evento Esempio:**
```json
{
  "event_type": "pdf_file_updated",
  "data": {
    "file_path": "/uploads/document_v2.pdf",
    "previous_file_path": "/uploads/document.pdf",
    "file_size": 2560000,
    "modified_at": "2025-11-15T10:30:00Z"
  },
  "metadata": {
    "source": "pdf-monitor-event-source",
    "timestamp": "2025-11-15T10:30:00Z"
  }
}
```

### 3. PDF File Deleted Trigger

**Trigger ID:** `Trigger Eliminazione PDF`
- **Event Type:** `pdf_file_deleted`
- **Source:** `pdf-monitor-event-source`
- **Target Workflow:** PDF Document DELETE Pipeline (`wf_04f5046263ff`)
- **Status:** ✅ Attivo
- **Nodi Workflow:** 12

**Descrizione:** Si attiva quando un file PDF viene rimosso dal sistema. Gestisce la pulizia dei metadati, rimozione da vectorstore e archiviazione storica.

**Payload Evento Esempio:**
```json
{
  "event_type": "pdf_file_deleted",
  "data": {
    "file_path": "/uploads/document.pdf",
    "deleted_at": "2025-11-15T11:00:00Z",
    "document_id": "doc_12345"
  },
  "metadata": {
    "source": "pdf-monitor-event-source",
    "timestamp": "2025-11-15T11:00:00Z"
  }
}
```

### 4. PDF Search Query Trigger

**Trigger ID:** `Trigger Query PDF`
- **Event Type:** `pdf_search_query`
- **Source:** `search-api-source`
- **Target Workflow:** PDF Document READ Pipeline (`wf_86ee1359f7f8`)
- **Status:** ✅ Attivo
- **Nodi Workflow:** 10

**Descrizione:** Si attiva quando viene eseguita una query di ricerca sui documenti PDF. Gestisce la ricerca semantica, ranking dei risultati e formattazione della risposta.

**Payload Evento Esempio:**
```json
{
  "event_type": "pdf_search_query",
  "data": {
    "query": "contratti di locazione 2024",
    "filters": {
      "date_range": "2024-01-01,2024-12-31",
      "document_type": "contract"
    },
    "user_id": "user_123"
  },
  "metadata": {
    "source": "search-api-source",
    "timestamp": "2025-11-15T12:00:00Z"
  }
}
```

## Event Sources

### pdf-monitor-event-source
**Tipo:** File System Monitor  
**Eventi generati:** `pdf_file_added`, `pdf_file_updated`, `pdf_file_deleted`  
**Descrizione:** Monitora una directory specificata per modifiche ai file PDF

### search-api-source  
**Tipo:** API Endpoint  
**Eventi generati:** `pdf_search_query`  
**Descrizione:** Endpoint API per query di ricerca sui documenti

## Workflow Target

| Workflow | ID | Nodi | Processori Principali |
|----------|----|----|---------------------|
| PDF Document CREATE Pipeline | `wf_7af99caf311a` | 10 | EventInput, FileParsing, MetadataManager |
| PDF Document READ Pipeline | `wf_86ee1359f7f8` | 10 | EventInput, VectorOperations, ResponseFormatter |
| PDF Document UPDATE Pipeline | `wf_fcad5d0befdb` | 11 | EventInput, FileParsing, DocumentProcessor |
| PDF Document DELETE Pipeline | `wf_04f5046263ff` | 12 | EventInput, MetadataManager, EventLogger |

## Configurazione Database

I trigger sono memorizzati nella tabella `workflow_triggers` con la seguente struttura:

```sql
CREATE TABLE workflow_triggers (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(100) NOT NULL,
    workflow_id VARCHAR(255) NOT NULL,
    conditions TEXT DEFAULT '{}',
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    target_node_id VARCHAR(100) DEFAULT NULL,
    FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
);
```

## API Endpoints

### Processo Evento Generico
```http
POST /api/events/process
Content-Type: application/json

{
  "event_type": "pdf_file_added",
  "data": {...},
  "metadata": {...}
}
```

### Gestione Trigger
```http
GET /api/triggers                    # Lista trigger attivi
POST /api/triggers                   # Crea nuovo trigger  
PUT /api/triggers/{trigger_id}       # Aggiorna trigger
DELETE /api/triggers/{trigger_id}    # Elimina trigger
```

## Processamento Eventi

### Flusso di Esecuzione
1. **Ricezione Evento**: Endpoint API riceve evento con payload
2. **Lookup Trigger**: Sistema cerca trigger attivi per `event_type` e `source`
3. **Valutazione Condizioni**: Controlla eventuali condizioni specificate nel trigger
4. **Esecuzione Workflow**: Avvia workflow associato con `TriggerService`
5. **Logging**: Registra risultato esecuzione per monitoraggio

### Gestione Errori
- **Trigger Non Trovato**: Evento ignorato con log informativo
- **Workflow Fallito**: Errore loggato, possibile retry automatico
- **Condizioni Non Soddisfatte**: Evento ignorato con log debug

## Monitoraggio

### Metriche Disponibili
- **Eventi Processati**: Conteggio per tipo evento
- **Trigger Attivati**: Frequenza attivazione per trigger
- **Workflow Eseguiti**: Success rate per workflow
- **Tempi Esecuzione**: Performance timing per workflow

### Log Events
Gli eventi processati sono loggati in `backend.services.trigger_service` con dettagli:
- Event type e source
- Trigger matched
- Workflow execution results
- Error details (se presenti)

## Configurazione e Manutenzione

### Aggiunta Nuovo Trigger
```sql
INSERT INTO workflow_triggers (id, name, event_type, source, workflow_id, active)
VALUES (
    'trigger_new_event',
    'Descrizione Trigger',
    'new_event_type', 
    'event-source',
    'workflow_id_target',
    1
);
```

### Disabilitazione Trigger
```sql
UPDATE workflow_triggers 
SET active = 0 
WHERE event_type = 'pdf_file_added';
```

### Aggiornamento Mapping Workflow
```sql
UPDATE workflow_triggers 
SET workflow_id = 'nuovo_workflow_id'
WHERE event_type = 'pdf_file_updated';
```

## Esempi di Utilizzo

### Test Trigger Manuale
```python
from backend.services.trigger_service import TriggerService

# Simula evento file aggiunto
trigger_service = TriggerService(db)
result = await trigger_service.process_event(
    event_type="pdf_file_added",
    data={"file_path": "/test/doc.pdf"},
    metadata={"source": "pdf-monitor-event-source"}
)
```

### Invio Evento via API
```bash
curl -X POST http://localhost:8000/api/events/process \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "pdf_file_added",
    "data": {"file_path": "/upload/document.pdf"},
    "metadata": {"source": "pdf-monitor-event-source"}
  }'
```

## Troubleshooting

### Problemi Comuni

**Trigger non si attiva:**
- Verificare che `active = 1` nel database
- Controllare corrispondenza esatta `event_type` e `source`
- Validare payload evento formato corretto

**Workflow fallisce:**
- Verificare che workflow_id esista in tabella `workflows`
- Controllare log del WorkflowEngine per errori specifici
- Validare che i nodi del workflow siano configurati correttamente

**Performance lenta:**
- Monitorare tempi esecuzione workflow
- Controllare che i processori non abbiano dipendenze bloccanti
- Verificare connessioni database e servizi esterni

### File di Log
- **Trigger Service**: `backend.services.trigger_service`
- **Workflow Engine**: `backend.engine.workflow_engine`
- **Event Router**: `backend.routers.event_trigger_system`

---

**Ultimo aggiornamento:** 15 Novembre 2025  
**Versione Sistema:** v2.0.0  
**Trigger Attivi:** 4  
**Workflow Target:** 4  
**Event Sources:** 2