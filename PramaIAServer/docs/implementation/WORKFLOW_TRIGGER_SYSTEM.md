# Sistema di Associazione Eventi-Workflow per PramaIA

## Struttura Attuale del Software

PramaIA è un'architettura basata su microservizi che comprende tre componenti principali:

1. **PramaIA-PDK (Plugin Development Kit)**
   - Core del sistema per l'estensibilità
   - Gestisce i workflow e i plugin
   - Fornisce l'API per l'esecuzione dei nodi di elaborazione
   - Contiene i workflow predefiniti (`pdf_ingest_complete_pipeline.json`, `query_chroma_semantic_public.json`, ecc.)

2. **PramaIA-Agents**
   - Contiene agenti esterni autonomi che estendono le funzionalità del sistema
   - Include il `pdf-folder-monitor-agent` che monitora cartelle per nuovi PDF
   - Comunica con il backend tramite API REST

3. **PramaIAServer**
   - Backend principale del sistema (FastAPI)
   - Gestisce autenticazione, database e API
   - Coordina l'esecuzione dei workflow tramite PDK
   - Fornisce l'interfaccia frontend (React)

### Processo Attuale di Monitoraggio e Processamento PDF

1. **Rilevamento PDF**
   - L'agent `pdf-folder-monitor-agent` monitora cartelle specifiche
   - Quando un PDF viene rilevato, viene aggiunto al buffer eventi
   - Il file viene inviato al backend tramite richiesta POST a `/api/pdf-monitor/upload/`

2. **Gestione Backend**
   - Il router `pdf_monitor_router.py` riceve il PDF
   - Un endpoint hardcoded inoltra il PDF a un workflow predefinito
   - Attualmente utilizza il plugin `pdf-semantic-complete-plugin` e un nodo specifico

3. **Esecuzione Workflow**
   - Il PDK Server riceve la richiesta e avvia il workflow
   - Il file viene elaborato dai nodi del workflow (estrazione, chunking, vettorizzazione, ecc.)
   - I risultati (incluso il document_id) vengono restituiti al plugin

4. **Gestione Eventi**
   - Il plugin aggiorna lo stato dell'evento nel buffer
   - L'interfaccia di monitoraggio mostra lo stato di elaborazione

### Limitazioni Attuali

- **Routing Hardcoded**: Il collegamento tra gli eventi del monitor PDF e i workflow è fisso
- **Mancanza di Flessibilità**: Non è possibile eseguire più workflow per un singolo PDF
- **Configurazione Limitata**: Non ci sono filtri o condizioni per l'esecuzione
- **Interfaccia di Gestione Assente**: Nessuna UI per configurare le associazioni

## Richiesta di Miglioramento

Si richiede un sistema più flessibile ed espandibile che permetta di:

1. Associare dinamicamente diversi tipi di eventi a workflow specifici
2. Configurare quali workflow vengono eseguiti quando un nuovo PDF viene rilevato
3. Stabilire condizioni e filtri per l'esecuzione dei workflow
4. Gestire queste associazioni tramite un'interfaccia grafica
5. Supportare l'esecuzione di più workflow per lo stesso evento

L'obiettivo è aumentare la scalabilità e la manutenibilità del sistema, rendendo più semplice l'aggiunta di nuovi workflow o l'integrazione con nuove sorgenti di eventi.

## Soluzione Proposta: Sistema di Trigger per Workflow

La soluzione proposta introduce un nuovo sottosistema di "Trigger per Workflow" che permette di associare eventi a workflow in modo flessibile e configurabile.

### 1. Modello di Dati per i Trigger

```python
# models/workflow_triggers.py
class WorkflowTrigger(BaseModel):
    id: str
    name: str  # Nome descrittivo
    event_type: str  # Tipo di evento (es. "pdf_upload", "file_created")
    source: str  # Sorgente dell'evento (es. "pdf-monitor", "scheduler")
    workflow_id: str  # ID del workflow da eseguire
    conditions: dict = {}  # Condizioni opzionali (filtri)
    active: bool = True  # Stato attivo/inattivo
    created_at: datetime
    updated_at: datetime
```

### 2. API per la Gestione dei Trigger

Nuovi endpoint REST per gestire le associazioni:

```python
# routers/workflow_triggers_router.py

@router.get("/triggers/", summary="Ottieni tutte le associazioni eventi-workflow")
async def get_triggers(current_user: UserInToken = Depends(get_current_user)):
    # Implementazione

@router.post("/triggers/", summary="Crea una nuova associazione evento-workflow")
async def create_trigger(trigger: WorkflowTrigger, current_user: UserInToken = Depends(get_current_user)):
    # Implementazione

@router.put("/triggers/{trigger_id}", summary="Aggiorna un'associazione evento-workflow")
async def update_trigger(trigger_id: str, trigger: WorkflowTrigger, current_user: UserInToken = Depends(get_current_user)):
    # Implementazione

@router.delete("/triggers/{trigger_id}", summary="Elimina un'associazione evento-workflow")
async def delete_trigger(trigger_id: str, current_user: UserInToken = Depends(get_current_user)):
    # Implementazione
```

### 3. Modifica del Router PDF Monitor

Modificare l'endpoint di upload per utilizzare il sistema di trigger:

```python
@router.post("/upload/", summary="Ricevi PDF dal plugin PDF Monitor e inoltra ai workflow PDK configurati")
async def receive_pdf_from_plugin(file: UploadFile = File(...)):
    try:
        # Ricerca trigger attivi per eventi "pdf_upload" dalla sorgente "pdf-monitor"
        active_triggers = db.get_active_triggers(event_type="pdf_upload", source="pdf-monitor")
        
        if not active_triggers:
            logger.warning("Nessun workflow associato all'evento di upload PDF")
            return {"status": "warning", "message": "Nessun workflow configurato per questo evento"}
        
        results = []
        document_id = None
        
        for trigger in active_triggers:
            # Verifica condizioni (filtri)
            if not evaluate_trigger_conditions(trigger, file):
                continue
                
            # Esegui il workflow associato
            result = await execute_workflow_for_trigger(trigger, file)
            results.append(result)
            
            # Estrai document_id dal primo risultato valido
            if not document_id and result.get("status") == "success":
                document_id = extract_document_id(result)
        
        return {
            "status": "success",
            "message": f"PDF '{file.filename}' elaborato da {len(results)} workflow",
            "document_id": document_id,
            "workflow_results": results
        }
    except Exception as e:
        logger.error(f"Errore ricezione PDF dal plugin: {e}")
        # Gestione errori
```

### 4. Funzioni di Supporto

```python
def evaluate_trigger_conditions(trigger, file):
    """Valuta le condizioni di un trigger per un file specifico."""
    conditions = trigger.get("conditions", {})
    
    # Filtro per nome file
    if "filename_pattern" in conditions:
        import re
        pattern = conditions["filename_pattern"]
        if not re.match(pattern, file.filename):
            return False
    
    # Filtro per dimensione file
    if "max_size_kb" in conditions:
        max_size = conditions["max_size_kb"] * 1024
        if file.size > max_size:
            return False
    
    # Altri filtri...
    
    return True

async def execute_workflow_for_trigger(trigger, file):
    """Esegue un workflow specifico per un trigger."""
    try:
        workflow_id = trigger["workflow_id"]
        
        # Ottiene il file come bytes
        file_bytes = await file.read()
        file.seek(0)  # Reimposta il puntatore per riletture successive
        
        # Prepara il payload per il PDK
        PDK_URL = os.getenv("PDK_SERVER_URL", f"http://localhost:{os.getenv('PDK_SERVER_PORT', '3001')}")
        PDK_WORKFLOW_ENDPOINT = f"{PDK_URL}/api/workflows/{workflow_id}/execute"
        
        # Esegui il workflow
        import requests
        response = requests.post(
            PDK_WORKFLOW_ENDPOINT,
            files={"file": (file.filename, file_bytes)},
            data={"metadata": json.dumps({"filename": file.filename, "source": "pdf-monitor-plugin"})},
            timeout=60
        )
        
        if response.status_code == 200:
            return {
                "status": "success",
                "workflow_id": workflow_id,
                "result": response.json()
            }
        else:
            return {
                "status": "error",
                "workflow_id": workflow_id,
                "error": f"HTTP {response.status_code}: {response.text}"
            }
    except Exception as e:
        return {
            "status": "error",
            "workflow_id": trigger["workflow_id"],
            "error": str(e)
        }
```

### 5. Interfaccia Utente per la Gestione dei Trigger

Aggiungere una nuova pagina nell'interfaccia admin:

```jsx
// frontend/client/src/pages/WorkflowTriggersPage.jsx
function WorkflowTriggersPage() {
  const [triggers, setTriggers] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Funzioni per caricamento dati e gestione CRUD
  
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Associazioni Eventi-Workflow</h1>
      
      {/* UI per visualizzare e gestire i trigger */}
      <table className="min-w-full bg-white border">
        <thead>
          <tr>
            <th className="py-2 px-4 border">Nome</th>
            <th className="py-2 px-4 border">Tipo Evento</th>
            <th className="py-2 px-4 border">Sorgente</th>
            <th className="py-2 px-4 border">Workflow</th>
            <th className="py-2 px-4 border">Stato</th>
            <th className="py-2 px-4 border">Azioni</th>
          </tr>
        </thead>
        <tbody>
          {/* Lista trigger */}
        </tbody>
      </table>
      
      {/* Modali per creazione/modifica */}
    </div>
  );
}
```

### 6. Componente Editor Condizioni

```jsx
// frontend/client/src/components/TriggerConditionsEditor.jsx
function TriggerConditionsEditor({ conditions, onChange }) {
  // Implementazione di un editor di condizioni
  
  return (
    <div className="p-4 border rounded">
      <h3 className="text-lg font-semibold mb-2">Condizioni di Attivazione</h3>
      
      {/* UI per configurare le condizioni */}
    </div>
  );
}
```

## Vantaggi della Soluzione

1. **Flessibilità**: Gli amministratori possono configurare quali workflow vengono eseguiti per quali eventi.
2. **Scalabilità**: Il sistema supporta facilmente nuovi tipi di eventi e condizioni.
3. **Parallelizzazione**: Un singolo evento può attivare più workflow.
4. **Filtraggio**: Le condizioni permettono di eseguire workflow solo quando necessario.
5. **Interfaccia Intuitiva**: La UI permette una gestione semplice delle associazioni.

## Piano di Implementazione

1. **Fase 1: Database e Modelli**
   - Creare le tabelle necessarie
   - Implementare i modelli Pydantic
   - Aggiungere funzioni CRUD

2. **Fase 2: API Backend**
   - Implementare gli endpoint REST
   - Modificare il router PDF Monitor
   - Aggiungere funzioni di supporto

3. **Fase 3: Interfaccia Utente**
   - Creare la pagina di gestione trigger
   - Implementare l'editor di condizioni
   - Integrare con l'interfaccia esistente

4. **Fase 4: Test e Documentazione**
   - Testare scenari di trigger multipli
   - Verificare la corretta applicazione delle condizioni
   - Documentare API e interfaccia utente

## Conclusioni

Questa soluzione trasforma il sistema da un approccio hardcoded a un'architettura event-driven flessibile. Non solo risolve il problema immediato dell'associazione tra PDF e workflow, ma crea una base solida per future espansioni del sistema.

Con questo approccio, PramaIA potrà facilmente supportare nuovi tipi di eventi, sorgenti di dati e workflow, aumentando significativamente le potenzialità e la versatilità della piattaforma.
