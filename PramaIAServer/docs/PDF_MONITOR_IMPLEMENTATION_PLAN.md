# Piano di Implementazione - Workflow per Eventi PDF Monitor

Questo documento fornisce un piano dettagliato per implementare i nuovi workflow PDK e integrare il router PDF Monitor con questi workflow.

## Obiettivi

1. Implementare un sistema completo di gestione eventi per il PDF Monitor
2. Creare nodi PDK riutilizzabili e workflow specifici per ogni tipo di evento
3. Aggiornare le API nel router PDF Monitor per utilizzare i nuovi workflow
4. Implementare il sistema di trigger per collegare eventi e workflow

## Fasi di Implementazione

### Fase 1: Implementazione Nodi Riutilizzabili (Settimana 1)

1. **Giorno 1-2: Implementare `VectorStoreOperations`**
   - Sviluppare il nodo con operazioni CRUD complete
   - Implementare la gestione degli errori e il logging
   - Testare con vari tipi di input e casi d'uso

2. **Giorno 3-4: Implementare `DocumentProcessor` e `MetadataManager`**
   - Sviluppare le funzionalità di elaborazione documenti
   - Implementare la gestione dei metadati
   - Testare con vari tipi di documenti e metadati

3. **Giorno 5: Implementare `EventLogger` e `FolderStructureManager`**
   - Sviluppare il sistema di logging eventi
   - Implementare la gestione della struttura cartelle
   - Testare con varie strutture di cartelle

### Fase 2: Implementazione Workflow (Settimana 2)

1. **Giorno 1-2: Implementare `remove_pdf_from_chroma`**
   - Creare la struttura del workflow
   - Connettere i nodi necessari
   - Testare con vari scenari di rimozione documenti

2. **Giorno 3-4: Implementare `update_pdf_metadata`**
   - Creare la struttura del workflow
   - Connettere i nodi necessari
   - Testare con vari scenari di aggiornamento documenti

3. **Giorno 5: Implementare `manage_folder_structure`**
   - Creare la struttura del workflow
   - Connettere i nodi necessari
   - Testare con vari scenari di gestione cartelle

### Fase 3: Implementazione Workflow Avanzati (Settimana 3)

1. **Giorno 1-3: Implementare `reconcile_folder_structure`**
   - Creare la struttura del workflow complesso
   - Connettere i nodi necessari
   - Implementare logica di riconciliazione avanzata
   - Testare con vari scenari di riconciliazione

2. **Giorno 4-5: Configurazione Trigger**
   - Creare le configurazioni dei trigger
   - Testare il collegamento eventi-workflow
   - Implementare la gestione degli errori nei trigger

### Fase 4: Aggiornamento Router PDF Monitor (Settimana 4)

1. **Giorno 1-2: Aggiornare endpoint esistenti**
   - Modificare `/api/pdf-monitor/upload/` per utilizzare i workflow tramite trigger
   - Aggiornare `/api/pdf-monitor/query/` per gestire errori in modo consistente
   - Testare gli endpoint aggiornati

2. **Giorno 3-5: Implementare nuovi endpoint**
   - Creare endpoint per gestire rimozione documenti
   - Creare endpoint per gestire aggiornamento documenti
   - Creare endpoint per gestire operazioni su cartelle
   - Implementare endpoint per la riconciliazione manuale
   - Testare tutti i nuovi endpoint

### Fase 5: Test e Validazione (Settimana 5)

1. **Giorno 1-3: Test completo del sistema**
   - Testare tutti gli scenari di eventi
   - Verificare la corretta attivazione dei workflow
   - Testare la gestione degli errori
   - Verificare la correttezza dei dati nel vectorstore

2. **Giorno 4-5: Ottimizzazione e documentazione**
   - Ottimizzare le performance dei workflow
   - Completare la documentazione
   - Preparare la release

## Aggiornamento del Router PDF Monitor

Il router PDF Monitor (`pdf_monitor_router.py`) dovrà essere aggiornato per supportare tutti i tipi di eventi. Ecco le modifiche necessarie:

### 1. Rifattorizzazione dell'endpoint di upload

```python
@router.post("/upload/", summary="Ricevi PDF dal plugin PDF Monitor e inoltra al workflow PDK")
async def receive_pdf_from_plugin(file: UploadFile = File(...)):
    """
    Riceve un file PDF dal plugin PDF Monitor e lo inoltra al workflow PDK di ingestione.
    """
    try:
        # [Codice esistente per salvare il file temporaneo]
        
        # Invece di chiamare direttamente il workflow, registriamo un evento
        # che attiva il trigger corrispondente
        event_payload = {
            "event_type": "document_added",
            "source": "pdf-monitor",
            "metadata": {
                "file_path": normalized_path.replace("\\", "/"),
                "file_name": file.filename,
                "upload_timestamp": datetime.now().isoformat(),
                "file_size": len(file_bytes)
            }
        }
        
        # Invio dell'evento al sistema di trigger
        event_response = await process_event_internal(event_payload)
        
        # [Gestione della risposta e pulizia]
```

### 2. Aggiunta di endpoint per rimozione documenti

```python
@router.delete("/documents/{document_id}", summary="Rimuove un documento dal sistema")
async def remove_document(document_id: str):
    """
    Rimuove un documento dal vectorstore e registra l'evento.
    """
    try:
        # Registra evento di rimozione
        event_payload = {
            "event_type": "document_removed",
            "source": "pdf-monitor",
            "metadata": {
                "document_id": document_id,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Invio dell'evento al sistema di trigger
        event_response = await process_event_internal(event_payload)
        
        # [Gestione della risposta]
```

### 3. Aggiunta di endpoint per gestione cartelle

```python
@router.post("/folders/", summary="Gestisce eventi relativi alle cartelle")
async def manage_folder(request: FolderEventRequest):
    """
    Gestisce eventi relativi alle cartelle (aggiunta, rimozione, rinomina).
    """
    try:
        # Valida il tipo di evento
        valid_event_types = ["folder_added", "folder_removed", "folder_renamed"]
        if request.event_type not in valid_event_types:
            raise HTTPException(status_code=400, detail=f"Tipo evento non valido. Tipi validi: {valid_event_types}")
        
        # Registra evento cartella
        event_payload = {
            "event_type": request.event_type,
            "source": "pdf-monitor",
            "metadata": {
                "folder_path": request.folder_path,
                "new_folder_path": request.new_folder_path,  # Solo per rinomina
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Invio dell'evento al sistema di trigger
        event_response = await process_event_internal(event_payload)
        
        # [Gestione della risposta]
```

### 4. Aggiunta di endpoint per riconciliazione

```python
@router.post("/reconcile/", summary="Richiede riconciliazione tra filesystem e vectorstore")
async def request_reconciliation(request: ReconciliationRequest):
    """
    Richiede una riconciliazione tra la struttura delle cartelle nel filesystem e nel vectorstore.
    """
    try:
        # Registra evento di richiesta riconciliazione
        event_payload = {
            "event_type": "reconciliation_requested",
            "source": "pdf-monitor",
            "metadata": {
                "folder_path": request.folder_path,
                "reconciliation_type": request.reconciliation_type,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Invio dell'evento al sistema di trigger
        event_response = await process_event_internal(event_payload)
        
        # [Gestione della risposta]
```

### 5. Creazione di funzione helper per invio eventi

```python
async def process_event_internal(event_payload):
    """
    Helper interno per inviare eventi al sistema di trigger.
    """
    try:
        # Ottieni URL dell'API eventi
        events_api_url = os.getenv("EVENTS_API_URL", "http://localhost:8000/api/events/process-event/")
        
        # Invia evento
        response = requests.post(events_api_url, json=event_payload, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Errore invio evento: Status {response.status_code}")
            raise Exception(f"Errore invio evento: Status {response.status_code}")
    except Exception as e:
        logger.error(f"Errore processo evento: {e}")
        raise
```

## Dipendenze e Prerequisiti

1. **Sistema di Trigger Funzionante**
   - Il sistema di trigger deve essere già implementato e funzionante
   - API `/api/events/process-event/` deve essere disponibile

2. **PDK con Supporto Workflow**
   - PDK deve supportare la creazione e l'esecuzione di workflow
   - API per l'esecuzione dei workflow deve essere disponibile

3. **Accesso al Vectorstore**
   - I nodi devono avere accesso al vectorstore
   - Librerie client per il vectorstore devono essere disponibili

## Rischi e Mitigazioni

1. **Rischio**: Workflow complessi potrebbero richiedere più tempo del previsto
   **Mitigazione**: Iniziare con implementazioni semplificate e poi iterare

2. **Rischio**: Integrazioni con sistemi esterni potrebbero causare problemi
   **Mitigazione**: Implementare mock per test e sviluppo iniziale

3. **Rischio**: Cambio completo dell'architettura potrebbe causare regressioni
   **Mitigazione**: Implementare gradualmente, mantenendo compatibilità con il sistema esistente

## Conclusione

Questo piano di implementazione fornisce una roadmap dettagliata per sviluppare un sistema completo di gestione eventi per il PDF Monitor. Seguendo questo piano, sarà possibile implementare una soluzione modulare, flessibile e robusta.
