# Architettura dei Workflow per Eventi PDF Monitor

Questo documento definisce l'architettura per la gestione degli eventi generati dal sistema PDF Monitor attraverso workflow specifici nel PDK.

## Tipi di Eventi

Il sistema PDF Monitor genera diversi tipi di eventi che richiedono elaborazione:

1. **Aggiunta Documento** (`document_added`): Un nuovo documento PDF viene aggiunto a una cartella monitorata
2. **Rimozione Documento** (`document_removed`): Un documento PDF viene rimosso da una cartella monitorata
3. **Rinomina Documento** (`document_renamed`): Un documento PDF viene rinominato
4. **Modifica Documento** (`document_modified`): Il contenuto di un documento PDF viene modificato
5. **Aggiunta Cartella** (`folder_added`): Una nuova cartella viene aggiunta all'interno di una cartella monitorata
6. **Rimozione Cartella** (`folder_removed`): Una cartella viene rimossa
7. **Rinomina Cartella** (`folder_renamed`): Una cartella viene rinominata

## Architettura dei Workflow

Per ogni tipo di evento, abbiamo definito un workflow dedicato con nodi specifici per l'elaborazione richiesta:

### 1. Workflow `ingest_pdf_to_chroma_public` (già esistente)
**Evento**: `document_added`
**Funzione**: Elabora un nuovo PDF e lo aggiunge al vectorstore
- Nodo 1: Estrazione testo dal PDF
- Nodo 2: Chunking del testo
- Nodo 3: Generazione embeddings
- Nodo 4: Salvataggio nel vectorstore
- Nodo 5: Aggiornamento metadati

### 2. Workflow `remove_pdf_from_chroma`
**Evento**: `document_removed`
**Funzione**: Rimuove un documento dal vectorstore
- Nodo 1: Validazione richiesta di rimozione
- Nodo 2: Ricerca documento nel vectorstore
- Nodo 3: Rimozione del documento
- Nodo 4: Pulizia metadati associati
- Nodo 5: Registrazione evento rimozione

### 3. Workflow `update_pdf_metadata`
**Evento**: `document_renamed` o `document_modified`
**Funzione**: Aggiorna metadati e/o contenuto di un documento esistente
- Nodo 1: Validazione richiesta di aggiornamento
- Nodo 2: Recupero documento esistente
- Nodo 3: Aggiornamento metadati
- Nodo 4: Se modificato, aggiornamento contenuto
- Nodo 5: Registrazione evento aggiornamento

### 4. Workflow `manage_folder_structure`
**Eventi**: `folder_added`, `folder_removed`, `folder_renamed`
**Funzione**: Gestisce modifiche alla struttura delle cartelle
- Nodo 1: Identificazione tipo di modifica
- Nodo 2: Recupero documenti interessati
- Nodo 3: Aggiornamento metadati dei documenti
- Nodo 4: Aggiornamento riferimenti strutturali
- Nodo 5: Registrazione evento cartella

## Nodi Riutilizzabili

Per ottimizzare lo sviluppo, abbiamo identificato diversi nodi riutilizzabili:

1. **VectorStoreOperations**: Gestisce operazioni CRUD sul vectorstore
   - Funzioni: add, get, update, delete, query

2. **DocumentProcessor**: Elabora documenti PDF
   - Funzioni: extract_text, chunk_text, generate_embeddings

3. **MetadataManager**: Gestisce i metadati dei documenti
   - Funzioni: update_metadata, merge_metadata, validate_metadata

4. **EventLogger**: Registra eventi nel sistema
   - Funzioni: log_event, update_event_status, query_events

5. **FolderStructureManager**: Gestisce la struttura delle cartelle
   - Funzioni: update_references, rebuild_structure, get_related_documents

## Integrazione con il Sistema di Trigger

I workflow vengono attivati dal sistema di trigger in base al tipo di evento:

1. Il PDF Monitor genera eventi nel sistema
2. Il sistema di trigger identifica il tipo di evento
3. Il trigger avvia il workflow appropriato
4. Il workflow elabora l'evento e aggiorna lo stato

## Implementazione

L'implementazione prevede:

1. Definizione dei nuovi workflow nel PDK
2. Creazione dei nodi riutilizzabili
3. Aggiornamento del router PDF Monitor per utilizzare i nuovi workflow
4. Configurazione dei trigger per i vari tipi di eventi
5. Aggiornamento dell'interfaccia utente per visualizzare lo stato dei vari tipi di eventi

## Vantaggi

Questo approccio offre:

1. **Modularità**: Ogni tipo di evento ha un percorso di elaborazione dedicato
2. **Riutilizzo**: I nodi comuni sono condivisi tra i workflow
3. **Flessibilità**: Facile aggiungere nuovi tipi di eventi o modificare l'elaborazione esistente
4. **Tracciabilità**: Chiara visibilità dell'elaborazione di ogni evento
5. **Resilienza**: Ogni workflow può gestire errori in modo specifico
