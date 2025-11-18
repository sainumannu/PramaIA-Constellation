# Guida all'Implementazione dei Workflow per Eventi PDF Monitor

Questo documento fornisce istruzioni pratiche per implementare il sistema di gestione eventi PDF Monitor con workflow PDK specifici.

## Panoramica

Abbiamo sviluppato un'architettura completa per gestire vari tipi di eventi generati dal sistema PDF Monitor attraverso workflow specifici nel PDK. Questo approccio offre:

1. **Modularità**: Ogni tipo di evento ha il suo percorso ottimizzato
2. **Riutilizzo**: I nodi di base sono condivisi tra workflow diversi
3. **Tracciabilità**: È facile seguire il flusso di ogni tipo di evento
4. **Resilienza**: Ogni workflow può gestire errori in modo specifico

## Struttura dei File

```
pdk/nodes/pdf_monitor/
├── README.md
├── vector_store_operations.py
├── vector_store_operations.json
├── document_processor.py
├── document_processor.json
├── metadata_manager.py
├── metadata_manager.json
├── event_logger.py
├── event_logger.json
└── folder_structure_manager.py
└── folder_structure_manager.json
```

## Nodi Già Implementati

1. **VectorStoreOperations**: Gestisce operazioni CRUD sul vectorstore
   - File: `vector_store_operations.py`
   - Operazioni: add, get, update, delete, query
   - Implementazione completa con gestione errori

2. **DocumentProcessor**: Elabora documenti PDF
   - File: `document_processor.py`
   - Funzionalità: estrazione testo, chunking, arricchimento metadati
   - Supporta vari tipi di strategie di chunking

## Nodi da Implementare

1. **MetadataManager**: Gestisce i metadati dei documenti
   - Implementa: update, merge, validate
   - Da implementare seguendo lo stesso pattern

2. **EventLogger**: Registra eventi nel sistema
   - Da implementare per integrarsi con il sistema di eventi esistente

3. **FolderStructureManager**: Gestisce la struttura delle cartelle
   - Da implementare per gestire operazioni sulla struttura cartelle

## Workflow da Implementare

1. **remove_pdf_from_chroma**: Per eventi `document_removed`
   - Utilizza: VectorStoreOperations (delete), EventLogger

2. **update_pdf_metadata**: Per eventi `document_renamed`, `document_modified`
   - Utilizza: DocumentProcessor, MetadataManager, VectorStoreOperations (update), EventLogger

3. **manage_folder_structure**: Per eventi `folder_*`
   - Utilizza: FolderStructureManager, VectorStoreOperations, EventLogger

4. **reconcile_folder_structure**: Per eventi `reconciliation_requested`
   - Utilizza: tutti i nodi in una pipeline complessa

## Come Procedere

### 1. Completare l'Implementazione dei Nodi

1. Implementa `metadata_manager.py` seguendo il pattern di VectorStoreOperations
2. Implementa `event_logger.py` per integrarsi con il sistema di eventi
3. Implementa `folder_structure_manager.py` per gestire le strutture cartelle

### 2. Creare i File di Workflow

Per ogni workflow da implementare, crea un file JSON nella directory appropriata del PDK:

```json
{
  "id": "remove_pdf_from_chroma",
  "name": "Remove PDF from Vectorstore",
  "description": "Rimuove un documento PDF dal vectorstore",
  "nodes": [
    {
      "id": "input",
      "type": "input",
      "position": { "x": 100, "y": 100 }
    },
    {
      "id": "validate",
      "type": "InputValidator",
      "position": { "x": 300, "y": 100 }
    },
    {
      "id": "delete",
      "type": "VectorStoreOperations",
      "position": { "x": 500, "y": 100 },
      "data": {
        "operation_type": "delete"
      }
    },
    {
      "id": "log",
      "type": "EventLogger",
      "position": { "x": 700, "y": 100 },
      "data": {
        "event_type": "document_removed"
      }
    },
    {
      "id": "output",
      "type": "output",
      "position": { "x": 900, "y": 100 }
    }
  ],
  "edges": [
    { "source": "input", "sourceHandle": "document_id", "target": "validate", "targetHandle": "document_id" },
    { "source": "validate", "sourceHandle": "validated_document_id", "target": "delete", "targetHandle": "document_id" },
    { "source": "delete", "sourceHandle": "status", "target": "log", "targetHandle": "status" },
    { "source": "delete", "sourceHandle": "document_id", "target": "log", "targetHandle": "document_id" },
    { "source": "log", "sourceHandle": "event_id", "target": "output", "targetHandle": "event_id" },
    { "source": "log", "sourceHandle": "status", "target": "output", "targetHandle": "status" }
  ]
}
```

### 3. Aggiornare il Router PDF Monitor

Aggiorna il file `pdf_monitor_router.py` per utilizzare il sistema di trigger e i nuovi workflow:

1. Modifica gli endpoint esistenti per registrare eventi invece di chiamare direttamente i workflow
2. Implementa nuovi endpoint per i vari tipi di eventi
3. Crea una funzione helper per inviare eventi al sistema di trigger

### 4. Configurare i Trigger

Crea le configurazioni dei trigger per collegare eventi e workflow:

```sql
INSERT INTO workflow_triggers (name, event_type, source, workflow_id, active)
VALUES
  ('PDF Added Trigger', 'document_added', 'pdf-monitor', 'ingest_pdf_to_chroma_public', 1),
  ('PDF Removed Trigger', 'document_removed', 'pdf-monitor', 'remove_pdf_from_chroma', 1),
  ('PDF Updated Trigger', 'document_renamed', 'pdf-monitor', 'update_pdf_metadata', 1),
  ('Folder Structure Change', 'folder_added', 'pdf-monitor', 'manage_folder_structure', 1);
```

## Test e Validazione

Per testare ogni componente:

1. **Test dei Nodi**: Utilizza il PDK Node Tester per verificare il funzionamento di ogni nodo
2. **Test dei Workflow**: Esegui i workflow con vari input di test
3. **Test End-to-End**: Simula eventi e verifica la corretta attivazione dei workflow
4. **Verifica Vectorstore**: Controlla che i documenti siano correttamente gestiti nel vectorstore

## Dipendenze

Assicurati di avere installate le seguenti dipendenze:

```
PyMuPDF (fitz)
langchain
langchain-text-splitters
```

## Note Importanti

1. **Gestione Errori**: Tutti i nodi devono gestire correttamente gli errori e restituire risposte consistenti
2. **Logging**: Implementa logging dettagliato per facilitare il debugging
3. **Performance**: Ottimizza per gestire documenti grandi e operazioni batch quando necessario
4. **Compatibilità**: Mantieni compatibilità con il sistema esistente durante la transizione

## Risorse Aggiuntive

- Documentazione del PDK per la creazione di nodi e workflow
- Schema del sistema di trigger esistente
- Documentazione del vectorstore utilizzato
