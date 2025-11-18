# Nodi PDK Riutilizzabili per Eventi PDF Monitor

Questo documento definisce i nodi riutilizzabili che saranno implementati nel PDK per supportare i vari workflow di gestione eventi PDF.

## 1. VectorStoreOperations

Nodo che fornisce operazioni complete sul vectorstore.

### Input
- `operation_type`: Tipo di operazione (`add`, `get`, `update`, `delete`, `query`)
- `document_id`: ID del documento (per get, update, delete)
- `document_content`: Contenuto del documento (per add, update)
- `document_metadata`: Metadati del documento (per add, update)
- `query_text`: Testo della query (per query)
- `namespace`: Namespace del vectorstore
- `collection_name`: Nome della collezione

### Output
- `status`: Stato dell'operazione
- `document_id`: ID del documento elaborato
- `result`: Risultato dell'operazione (dipende dal tipo)

### Implementazione
```python
class VectorStoreOperations:
    def process(self, inputs):
        operation_type = inputs.get("operation_type")
        document_id = inputs.get("document_id")
        document_content = inputs.get("document_content")
        document_metadata = inputs.get("document_metadata", {})
        query_text = inputs.get("query_text")
        namespace = inputs.get("namespace", "default")
        collection_name = inputs.get("collection_name", "default")
        
        # Ottieni riferimento al vectorstore
        vectorstore = self._get_vectorstore(collection_name, namespace)
        
        if operation_type == "add":
            return self._add_document(vectorstore, document_content, document_metadata)
        elif operation_type == "get":
            return self._get_document(vectorstore, document_id)
        elif operation_type == "update":
            return self._update_document(vectorstore, document_id, document_content, document_metadata)
        elif operation_type == "delete":
            return self._delete_document(vectorstore, document_id)
        elif operation_type == "query":
            return self._query_documents(vectorstore, query_text)
        else:
            raise ValueError(f"Operazione non supportata: {operation_type}")
```

## 2. DocumentProcessor

Nodo che gestisce l'elaborazione di documenti PDF.

### Input
- `file_path`: Percorso del file PDF
- `file_content`: Contenuto del file (alternativo a file_path)
- `chunking_strategy`: Strategia di suddivisione del testo
- `chunk_size`: Dimensione dei chunk
- `chunk_overlap`: Sovrapposizione tra chunk
- `metadata`: Metadati del documento

### Output
- `document_text`: Testo estratto dal documento
- `chunks`: Lista di chunk di testo
- `metadata`: Metadati arricchiti

### Implementazione
```python
class DocumentProcessor:
    def process(self, inputs):
        file_path = inputs.get("file_path")
        file_content = inputs.get("file_content")
        chunking_strategy = inputs.get("chunking_strategy", "paragraph")
        chunk_size = inputs.get("chunk_size", 1000)
        chunk_overlap = inputs.get("chunk_overlap", 200)
        metadata = inputs.get("metadata", {})
        
        # Estrai testo
        document_text = self._extract_text(file_path, file_content)
        
        # Suddividi in chunk
        chunks = self._chunk_text(document_text, chunking_strategy, chunk_size, chunk_overlap)
        
        # Arricchisci metadati
        enriched_metadata = self._enrich_metadata(metadata, document_text)
        
        return {
            "document_text": document_text,
            "chunks": chunks,
            "metadata": enriched_metadata
        }
```

## 3. MetadataManager

Nodo che gestisce i metadati dei documenti.

### Input
- `operation`: Operazione sui metadati (`update`, `merge`, `validate`)
- `current_metadata`: Metadati attuali
- `new_metadata`: Nuovi metadati
- `validation_schema`: Schema per validazione (opzionale)

### Output
- `metadata`: Metadati risultanti
- `is_valid`: Risultato validazione
- `validation_errors`: Eventuali errori di validazione

### Implementazione
```python
class MetadataManager:
    def process(self, inputs):
        operation = inputs.get("operation", "update")
        current_metadata = inputs.get("current_metadata", {})
        new_metadata = inputs.get("new_metadata", {})
        validation_schema = inputs.get("validation_schema")
        
        if operation == "update":
            result_metadata = new_metadata
        elif operation == "merge":
            result_metadata = self._merge_metadata(current_metadata, new_metadata)
        else:
            result_metadata = current_metadata
            
        # Validazione metadati
        is_valid, validation_errors = self._validate_metadata(result_metadata, validation_schema)
        
        return {
            "metadata": result_metadata,
            "is_valid": is_valid,
            "validation_errors": validation_errors
        }
```

## 4. EventLogger

Nodo che gestisce la registrazione degli eventi nel sistema.

### Input
- `event_type`: Tipo di evento
- `source`: Sorgente dell'evento
- `status`: Stato dell'evento
- `document_id`: ID del documento (opzionale)
- `file_path`: Percorso del file (opzionale)
- `folder_path`: Percorso della cartella (opzionale)
- `metadata`: Metadati aggiuntivi

### Output
- `event_id`: ID dell'evento registrato
- `timestamp`: Timestamp di registrazione
- `status`: Stato dell'operazione

### Implementazione
```python
class EventLogger:
    def process(self, inputs):
        event_type = inputs.get("event_type")
        source = inputs.get("source", "pdk")
        status = inputs.get("status", "completed")
        document_id = inputs.get("document_id")
        file_path = inputs.get("file_path")
        folder_path = inputs.get("folder_path")
        metadata = inputs.get("metadata", {})
        
        # Registra evento nel database
        event_id = self._log_event(event_type, source, status, document_id, file_path, folder_path, metadata)
        
        return {
            "event_id": event_id,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
```

## 5. FolderStructureManager

Nodo che gestisce la struttura delle cartelle e i riferimenti tra documenti.

### Input
- `operation`: Tipo di operazione (`update_references`, `rebuild_structure`, `get_related_documents`)
- `folder_path`: Percorso della cartella
- `new_folder_path`: Nuovo percorso (per rinomina/spostamento)
- `recursive`: Flag per operazioni ricorsive

### Output
- `affected_documents`: Lista dei documenti interessati
- `structure_metadata`: Metadati della struttura cartella
- `status`: Stato dell'operazione

### Implementazione
```python
class FolderStructureManager:
    def process(self, inputs):
        operation = inputs.get("operation")
        folder_path = inputs.get("folder_path")
        new_folder_path = inputs.get("new_folder_path")
        recursive = inputs.get("recursive", True)
        
        if operation == "update_references":
            return self._update_references(folder_path, new_folder_path, recursive)
        elif operation == "rebuild_structure":
            return self._rebuild_structure(folder_path, recursive)
        elif operation == "get_related_documents":
            return self._get_related_documents(folder_path, recursive)
        else:
            raise ValueError(f"Operazione non supportata: {operation}")
```

## Integrazione nei Workflow

Questi nodi possono essere combinati nei workflow per gestire i vari tipi di eventi:

### Esempio: Workflow `remove_pdf_from_chroma`

```
[Start] --> [ValidateInput] --> [VectorStoreOperations:get] --> [VectorStoreOperations:delete] --> [EventLogger] --> [End]
```

### Esempio: Workflow `update_pdf_metadata`

```
[Start] --> [ValidateInput] --> [MetadataManager] --> [VectorStoreOperations:get] --> [VectorStoreOperations:update] --> [EventLogger] --> [End]
```

## Vantaggi dell'Approccio

1. **Riutilizzo**: Ogni nodo può essere utilizzato in più workflow
2. **Testabilità**: Facile testare ogni nodo separatamente
3. **Manutenibilità**: Modifiche a una funzionalità impattano solo il nodo specifico
4. **Estensibilità**: Facile aggiungere nuove funzionalità estendendo i nodi esistenti
