# 📊 Flusso Sistema Trigger Moderno - PramaIA

> **Documento di Riferimento**: Architettura e flusso dati del sistema di trigger moderno quando un client carica un file nel sistema PramaIA.

---

## 🎯 **1. Frontend Upload**

Il client frontend invia il file tramite upload standard:

```jsx
// Client invia file via upload standard
POST /documents/upload-with-visibility/
// FormData con file + is_public flag
```

**Componenti Frontend:**
- `DocumentsManager.jsx` / `DocumentManager.jsx` / `FileUpload.jsx`
- `FormData` con file + flag `is_public`
- Headers: `Authorization: Bearer ${token}` + `Content-Type: multipart/form-data`

---

## ⚙️ **2. Backend Documents Router**

Il router documenti gestisce l'upload iniziale:

```python
// documents_router.py
@router.post("/upload-with-visibility/")
async def upload_pdfs_with_visibility():
    # Chiama document_service (senza sistema trigger diretto)
    await document_service.process_uploaded_file(content, filename, user_id, is_public)
```

**Funzionalità:**
- Validazione autenticazione e autorizzazione
- Lettura file multipart
- Chiamata al `document_service` per elaborazione base
- Salvataggio metadati e file fisico

---

## 🔥 **3. Sistema Trigger Moderno**

Quando è configurato un trigger nel database, il sistema funziona tramite eventi generici:

### **A. Endpoint Eventi Generici**

```python
// event_trigger_system.py
POST /api/events/process

# Evento generico che attiva trigger
{
    "event_type": "file_upload",
    "data": {
        "filename": "document.pdf",
        "content_type": "application/pdf",
        "size": 12345,
        "user_id": "user123"
    },
    "metadata": {
        "source": "document-upload",
        "user_id": "user123"
    }
}
```

### **B. TriggerService Processing**

```python
// trigger_service.py
class TriggerService:
    async def process_event(event_type, data, metadata):
        # 1. Trova trigger corrispondenti nel database
        matching_triggers = await self._find_matching_triggers(event_type, data, metadata)
        
        # 2. Per ogni trigger attivo
        for trigger in matching_triggers:
            # 3. Valuta condizioni (filtri)
            if self._evaluate_trigger_conditions(trigger, data, metadata):
                # 4. Esegue workflow usando WorkflowEngine
                result = await self._execute_workflow(trigger, data, metadata)
```

**Processo TriggerService:**
1. **Query Database**: Cerca trigger attivi per `event_type` e `source`
2. **Pattern Matching**: Verifica condizioni configurate nei trigger
3. **Workflow Execution**: Esegue workflow associati tramite WorkflowEngine locale

### **C. Workflow Execution**

```python
// trigger_service.py
async def _execute_workflow(trigger, data, metadata):
    # 1. Recupera workflow dal database
    workflow = WorkflowCRUD.get_workflow(self.db, workflow_id)
    
    # 2. Prepara input data
    input_data = self._prepare_workflow_input(data, metadata, trigger)
    
    # 3. Esegue LOCALMENTE usando WorkflowEngine
    result = await self.workflow_engine.execute_workflow(
        workflow=workflow,
        input_data=input_data,
        execution_id=execution_record.execution_id
    )
```

---

## 🚀 **4. WorkflowEngine Locale**

Il **WorkflowEngine** esegue il workflow **localmente nel server**, non nel PDK:

```python
// Workflow Engine (locale)
- Legge nodi dal database (workflows, workflow_nodes, workflow_connections)
- Esegue nodi in sequenza secondo le connessioni definite
- I nodi possono chiamare PDK quando necessario
- Gestisce input/output tra nodi
- Salva risultati nel database (workflow_executions)
```

**Caratteristiche:**
- **Esecuzione Locale**: Non dipende dal PDK per l'orchestrazione
- **Database-Driven**: Workflow definiti nel database SQLite
- **Logging Completo**: Traccia esecuzioni in `workflow_executions`
- **Stato Persistente**: Mantiene stato e risultati nel database

---

## 🔌 **5. Chiamate PDK (quando necessario)**

I **nodi del workflow** possono chiamare il PDK per elaborazioni specifiche:

```python
// workflow_trigger_service.py
async def execute_workflow_for_trigger(trigger, file):
    # Se trigger specifica target_node_id
    if target_node_id:
        # Chiamata diretta al nodo PDK specifico
        PDK_ENDPOINT = f"{PDK_URL}/plugins/{plugin_id}/execute"
        
        payload = {
            "nodeId": target_node_id,
            "inputs": {},
            "config": {
                "file_path": temp_filepath,
                "extract_text": True,
                "metadata": {...}
            }
        }
```

**Integrazione PDK:**
- **Plugin-specific**: Chiamate a plugin specifici (es. `document-semantic-complete-plugin`)
- **Node-specific**: Routing a nodi specifici (es. `document_input_node`)
- **Multipart Upload**: File + JSON payload
- **Timeout Management**: Gestione timeout e errori

---

## 📊 **6. Configurazione Trigger Database**

I trigger sono configurati nel database SQLite:

```sql
-- Esempi trigger configurati
INSERT INTO workflow_triggers (
    name, event_type, source, workflow_id, active, conditions, target_node_id
) VALUES (
    'PDF Upload Auto-Process',
    'file_upload',
    'document-upload', 
    'pdf_ingest_complete_pipeline',
    1,
    '{"file_type": "pdf", "size_gt": 1000}',
    'pdf_input_node'
);
```

**Parametri Trigger:**
- **name**: Nome descrittivo del trigger
- **event_type**: Tipo di evento (`file_upload`, `pdf_file_added`, etc.)
- **source**: Sorgente dell'evento (`document-upload`, `pdf-monitor`, etc.)
- **workflow_id**: ID del workflow da eseguire
- **conditions**: Filtri JSON per condizioni specifiche
- **target_node_id**: Nodo specifico da targetizzare (opzionale)
- **active**: Flag di attivazione del trigger

---

## 🎯 **7. Flusso Completo Corretto**

```
Frontend Upload
       ↓
Documents Router (/documents/upload-with-visibility/)
       ↓
Document Service (salvataggio file + metadati)
       ↓ [SE TRIGGER CONFIGURATO]
Event Trigger System (/api/events/process)
       ↓
TriggerService.process_event()
       ↓
_find_matching_triggers() → Query DB
       ↓
_evaluate_trigger_conditions() → Filtri
       ↓
_execute_workflow() → WorkflowEngine LOCALE
       ↓
WorkflowEngine.execute_workflow()
       ↓ [Se necessario]
Chiamata nodi PDK specifici
       ↓
Risultato e logging
```

---

## ⚡ **8. Differenze Chiave dal Sistema Legacy**

### **❌ NON PIÙ UTILIZZATO:**
- Router PDF Monitor legacy (`pdf_monitor_router.py`)
- Chiamate dirette PDK dal router di upload
- `document_monitor_service.py` per processing
- Endpoint specifici `/api/pdf-monitor/upload/`

### **✅ SISTEMA MODERNO:**
- **Event Trigger System generico**: `/api/events/process`
- **TriggerService centralizzato**: Gestione unificata trigger
- **WorkflowEngine locale**: Esecuzione workflow nel server
- **Database trigger configuration**: Trigger configurabili via DB
- **Routing intelligente**: Trigger-to-workflow-to-node routing

---

## 🗄️ **9. Database Schema**

### **Trigger Configuration**
```sql
-- Trigger configurati
workflow_triggers: 
  - id, name, event_type, source
  - workflow_id, conditions, target_node_id, active
  - created_at, updated_at
```

### **Workflow Definitions**
```sql
-- Definizioni workflow
workflows: workflow_id, name, description, is_active
workflow_nodes: node_id, workflow_id, node_type, config
workflow_connections: from_node_id, to_node_id, from_port, to_port
```

### **Execution Tracking**
```sql
-- Tracking esecuzioni
workflow_executions: 
  - execution_id, workflow_id, user_id
  - status, input_data, result, error_message
  - started_at, completed_at
```

---

## 🔍 **10. PDF Monitor Agent Integration**

Quando il **PDF Monitor Agent** rileva un nuovo file:

```
PDF Monitor Agent (watchdog)
        ↓ [on_created()]
Event Buffer (SQLite)
        ↓ [HTTP POST]
Backend Compatibility Router (/api/pdf-monitor/upload/)
        ↓ [redirect to document_monitor_service]
Document Service Processing
        ↓ [se configurato]
Event Trigger System (/api/events/process)
        ↓
[STESSO FLUSSO DEL PUNTO 7]
```

**Key Points:**
- Il Monitor Agent usa ancora endpoint di compatibilità
- L'integrazione avviene tramite `document_monitor_service.py`
- Il servizio può inviare eventi al sistema trigger quando configurato
- Stessa logica di trigger per file rilevati vs file caricati

---

## 🎉 **11. Vantaggi del Sistema Moderno**

### **🔧 Flessibilità**
- Trigger configurabili senza modifiche al codice
- Supporto per eventi generici, non solo PDF
- Condizioni personalizzabili via JSON

### **📈 Scalabilità**
- Esecuzione locale vs dipendenza PDK
- Database-driven configuration
- Logging e monitoring centralizzato

### **🔌 Modularità**
- Separazione concerns: trigger ↔ workflow ↔ nodi
- Riutilizzo workflow per diversi trigger
- Integrazione PDK on-demand

### **⚙️ Manutenibilità**
- Configurazione via database vs hardcoded
- Sistema di logging unificato
- Error handling centralizzato

---

**Documento creato**: Novembre 2025  
**Versione Sistema**: Trigger System v2.0.0  
**Maintainer**: PramaIA Development Team

Il sistema è **completamente event-driven** e **configurabile**: quando un file viene caricato, se esiste un trigger configurato per quell'evento, il sistema automaticamente esegue il workflow associato! 🚀