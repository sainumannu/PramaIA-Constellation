# Workflow per Eventi PDF Monitor

Questo documento descrive nel dettaglio i workflow che gestiranno i vari tipi di eventi generati dal sistema PDF Monitor.

## 1. Workflow: `ingest_pdf_to_chroma_public` (Esistente)

**Evento**: `document_added`

**Descrizione**: Questo workflow esistente elabora un nuovo documento PDF e lo aggiunge al vectorstore. Per completezza, ne descriviamo i componenti principali.

### Nodi:
1. **InputValidator**
   - Valida il file PDF e i metadati di ingresso
   - Input: `pdf_file`, `user_id`, `metadata`
   - Output: `validated_file_path`, `validated_metadata`

2. **DocumentProcessor**
   - Estrae il testo dal PDF e lo suddivide in chunk
   - Input: `file_path`, `chunking_strategy`, `chunk_size`
   - Output: `document_text`, `chunks`, `enriched_metadata`

3. **EmbeddingGenerator**
   - Genera gli embedding per i chunk di testo
   - Input: `chunks`, `embedding_model`
   - Output: `embeddings`

4. **VectorStoreIngestion**
   - Aggiunge i chunk con gli embedding al vectorstore
   - Input: `chunks`, `embeddings`, `metadata`
   - Output: `document_id`, `status`

5. **EventLogger**
   - Registra l'evento di aggiunta documento
   - Input: `event_type`, `document_id`, `file_path`, `status`
   - Output: `event_id`

## 2. Workflow: `remove_pdf_from_chroma`

**Evento**: `document_removed`

**Descrizione**: Questo workflow rimuove un documento dal vectorstore quando viene eliminato dal filesystem.

### Nodi:
1. **InputValidator**
   - Valida la richiesta di rimozione
   - Input: `document_id` o `file_path`
   - Output: `validated_document_id`

2. **DocumentResolver**
   - Risolve l'ID del documento in base al percorso file
   - Input: `file_path` (opzionale se document_id è fornito)
   - Output: `document_id`, `metadata`

3. **VectorStoreOperations**
   - Rimuove il documento dal vectorstore
   - Input: `operation_type: "delete"`, `document_id`
   - Output: `status`

4. **MetadataCleanup**
   - Rimuove i metadati associati al documento
   - Input: `document_id`
   - Output: `cleanup_status`

5. **EventLogger**
   - Registra l'evento di rimozione
   - Input: `event_type: "document_removed"`, `document_id`, `file_path`, `status`
   - Output: `event_id`

## 3. Workflow: `update_pdf_metadata`

**Eventi**: `document_renamed`, `document_modified`

**Descrizione**: Questo workflow aggiorna i metadati e/o il contenuto di un documento esistente nel vectorstore.

### Nodi:
1. **InputValidator**
   - Valida la richiesta di aggiornamento
   - Input: `document_id` o `file_path`, `new_metadata`, `new_content` (opzionale)
   - Output: `validated_document_id`, `validated_metadata`

2. **DocumentResolver**
   - Risolve l'ID del documento e recupera i metadati esistenti
   - Input: `file_path` o `document_id`
   - Output: `document_id`, `current_metadata`

3. **MetadataManager**
   - Gestisce l'aggiornamento dei metadati
   - Input: `operation: "merge"`, `current_metadata`, `new_metadata`
   - Output: `updated_metadata`, `is_valid`

4. **ConditionalContentProcessor**
   - Se `new_content` è fornito, elabora il nuovo contenuto
   - Input: `document_id`, `new_content`
   - Output: `processed_content`, `chunks`

5. **VectorStoreOperations**
   - Aggiorna il documento nel vectorstore
   - Input: `operation_type: "update"`, `document_id`, `document_content` (opzionale), `document_metadata`
   - Output: `status`

6. **EventLogger**
   - Registra l'evento di aggiornamento
   - Input: `event_type`, `document_id`, `file_path`, `status`
   - Output: `event_id`

## 4. Workflow: `manage_folder_structure`

**Eventi**: `folder_added`, `folder_removed`, `folder_renamed`

**Descrizione**: Questo workflow gestisce le modifiche alla struttura delle cartelle e aggiorna i riferimenti nei documenti.

### Nodi:
1. **InputValidator**
   - Valida la richiesta di gestione cartella
   - Input: `event_type`, `folder_path`, `new_folder_path` (per rinomina)
   - Output: `validated_folder_path`, `validated_event_type`

2. **FolderStructureManager**
   - Gestisce l'operazione sulla struttura cartella
   - Input: `operation`, `folder_path`, `new_folder_path`, `recursive`
   - Output: `affected_documents`, `structure_metadata`

3. **BatchDocumentUpdater**
   - Aggiorna i metadati di tutti i documenti interessati
   - Input: `documents`, `update_operation`, `metadata_changes`
   - Output: `update_results`

4. **VectorStoreOperations**
   - Aggiorna i metadati strutturali nel vectorstore
   - Input: `operation_type: "update"`, `document_id: "folder_structure"`, `document_metadata`
   - Output: `status`

5. **EventLogger**
   - Registra l'evento relativo alla cartella
   - Input: `event_type`, `folder_path`, `status`, `affected_documents`
   - Output: `event_id`

## 5. Workflow: `reconcile_folder_structure`

**Evento**: `reconciliation_requested`

**Descrizione**: Questo workflow esegue una riconciliazione completa tra la struttura delle cartelle nel filesystem e nel vectorstore.

### Nodi:
1. **InputValidator**
   - Valida la richiesta di riconciliazione
   - Input: `folder_path`, `reconciliation_type`
   - Output: `validated_folder_path`

2. **FilesystemScanner**
   - Scansiona la struttura della cartella nel filesystem
   - Input: `folder_path`, `recursive`, `file_patterns`
   - Output: `filesystem_structure`

3. **VectorStoreStructureResolver**
   - Recupera la struttura attuale dal vectorstore
   - Input: `folder_path`
   - Output: `vectorstore_structure`

4. **DifferencesCalculator**
   - Calcola le differenze tra le due strutture
   - Input: `filesystem_structure`, `vectorstore_structure`
   - Output: `added_files`, `removed_files`, `modified_files`, `added_folders`, `removed_folders`, `renamed_entities`

5. **BatchOperationsExecutor**
   - Esegue le operazioni necessarie per riconciliare le differenze
   - Input: `differences`, `operation_mode`
   - Output: `operation_results`

6. **EventLogger**
   - Registra l'evento di riconciliazione
   - Input: `event_type: "reconciliation_completed"`, `folder_path`, `status`, `operation_results`
   - Output: `event_id`

## Configurazione dei Trigger

Per connettere questi workflow al sistema di trigger, è necessaria la seguente configurazione:

```json
[
  {
    "name": "PDF Added Trigger",
    "event_type": "document_added",
    "source": "pdf-monitor",
    "workflow_id": "ingest_pdf_to_chroma_public",
    "active": true
  },
  {
    "name": "PDF Removed Trigger",
    "event_type": "document_removed",
    "source": "pdf-monitor",
    "workflow_id": "remove_pdf_from_chroma",
    "active": true
  },
  {
    "name": "PDF Updated Trigger",
    "event_type": "document_renamed",
    "source": "pdf-monitor",
    "workflow_id": "update_pdf_metadata",
    "active": true
  },
  {
    "name": "PDF Modified Trigger",
    "event_type": "document_modified",
    "source": "pdf-monitor",
    "workflow_id": "update_pdf_metadata",
    "active": true
  },
  {
    "name": "Folder Structure Change Trigger",
    "event_type": ["folder_added", "folder_removed", "folder_renamed"],
    "source": "pdf-monitor",
    "workflow_id": "manage_folder_structure",
    "active": true
  },
  {
    "name": "Reconciliation Trigger",
    "event_type": "reconciliation_requested",
    "source": "pdf-monitor",
    "workflow_id": "reconcile_folder_structure",
    "active": true
  }
]
```

## Piano di Implementazione

1. **Fase 1**: Implementazione dei nodi riutilizzabili
2. **Fase 2**: Creazione del workflow `remove_pdf_from_chroma`
3. **Fase 3**: Creazione del workflow `update_pdf_metadata`
4. **Fase 4**: Creazione del workflow `manage_folder_structure`
5. **Fase 5**: Creazione del workflow `reconcile_folder_structure`
6. **Fase 6**: Configurazione dei trigger
7. **Fase 7**: Aggiornamento delle API nel router PDF Monitor
8. **Fase 8**: Test e validazione del sistema completo
