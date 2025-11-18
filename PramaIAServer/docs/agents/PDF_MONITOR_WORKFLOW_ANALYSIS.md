# PDF Monitor Agent - Analisi del Workflow

## 🔍 Architettura del Workflow PDF Monitor

Il sistema è composto da tre componenti principali che interagiscono tra loro:

### 1️⃣ **PDF Folder Monitor Agent** (porta 8001)
- **Funzione**: Monitora cartelle specificate alla ricerca di file PDF
- **Tecnologia**: Python con FastAPI e Watchdog
- **Componenti chiave**:
  - `folder_monitor.py`: Implementa il monitoraggio delle cartelle
  - `control_api.py`: Espone API REST per gestire le cartelle monitorate
  - `event_buffer.py`: Gestisce il buffer degli eventi (creazione, modifica, eliminazione file)

### 2️⃣ **Backend Server (PramaIAServer)** (porta 8000)
- **Funzione**: Riceve i PDF dall'agent e li inoltra al PDK
- **Tecnologia**: Python con FastAPI
- **Componenti chiave**:
  - `pdf_monitor_router.py`: Gestisce l'endpoint `/api/pdf-monitor/upload/`

### 3️⃣ **PDK Server** (porta 3001)
- **Funzione**: Esegue il workflow di elaborazione dei PDF
- **Tecnologia**: Node.js
- **Componenti chiave**:
  - Plugin `pdf-semantic-complete-plugin`: Contiene i nodi necessari per processare i PDF
  - Nodo `pdf_input_node`: Entry point per l'elaborazione dei PDF

## 📊 Flusso di Elaborazione

Ecco il flusso completo:

1. **Rilevamento PDF**:
   - L'agent monitora le cartelle configurate usando `watchdog`
   - Quando rileva un nuovo file PDF, registra l'evento nel buffer degli eventi

2. **Invio al Backend**:
   - L'agent carica automaticamente il PDF al backend tramite una richiesta POST a `/api/pdf-monitor/upload/`
   - Include il nome file e il percorso completo
   - Aggiorna lo stato dell'evento a `processing`

3. **Elaborazione nel Backend**:
   - `pdf_monitor_router.py` riceve il file
   - Salva temporaneamente il file in `temp_files/`
   - Prepara il payload per il PDK con `nodeId`, `inputs` e `config`

4. **Esecuzione Workflow PDK**:
   - Il backend invia il file al PDK tramite l'endpoint `/plugins/pdf-semantic-complete-plugin/execute`
   - Specifica `pdf_input_node` come nodo di ingresso
   - Passa il percorso del file e i metadati

5. **Risultati e Feedback**:
   - Il PDK elabora il PDF e restituisce un risultato con `document_id`
   - Il backend inoltra il risultato all'agent
   - L'agent aggiorna lo stato dell'evento a `completed` o `error`

## 🔧 Configurazione e Monitoraggio

- **Configurazione Cartelle**:
  - Endpoint `POST /monitor/configure` per aggiungere nuove cartelle da monitorare
  - Configurazione salvata in `monitor_config.json`

- **Eventi e Stato**:
  - Gli eventi sono tracciati in un database SQLite (`event_buffer.db`)
  - Ogni evento ha uno stato: `new`, `processing`, `completed`, `error`
  - API per visualizzare e gestire gli eventi (`/monitor/events`)

- **Gestione Errori**:
  - Retry automatici in caso di errori di comunicazione
  - Registrazione dettagliata degli errori

## 🚀 Punti di Forza del Sistema

1. **Separazione delle Responsabilità**:
   - L'agent gestisce solo il monitoraggio file e la comunicazione
   - Il backend coordina l'elaborazione e l'integrazione
   - Il PDK si occupa dell'elaborazione effettiva

2. **Robustezza**:
   - Buffer eventi per tracciare lo stato di ogni file
   - Gestione degli errori con informazioni dettagliate
   - Pulizia automatica dei file temporanei

3. **Flessibilità**:
   - Configurazione runtime delle cartelle da monitorare
   - Supporto per diversi tipi di eventi (creazione, modifica, eliminazione)
   - Facile estensione per supportare nuovi tipi di file

4. **Configurazione Centralizzata**:
   - Utilizzo di variabili d'ambiente per la configurazione
   - Supporto per override di configurazioni

## 📁 Struttura dei file chiave

```
PramaIA-Agents/
└── pdf-folder-monitor-agent/
    ├── src/
    │   ├── main.py             # Entry point dell'applicazione
    │   ├── control_api.py      # API FastAPI per la gestione
    │   ├── folder_monitor.py   # Sistema di monitoraggio cartelle
    │   └── event_buffer.py     # Gestione eventi e stati
    ├── monitor_config.json     # Configurazione cartelle monitorate
    └── event_buffer.db         # Database SQLite per eventi

PramaIAServer/
└── backend/
    └── routers/
        └── pdf_monitor_router.py  # Gestore ricezione PDF e inoltro al PDK

PramaIA-PDK/
└── plugins/
    └── pdf-semantic-complete-plugin/
        ├── plugin.json        # Configurazione plugin
        └── src/
            └── pdf_input_processor.py  # Nodo entry point per PDF
```

## 📌 Variabili d'ambiente chiave

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `PLUGIN_PDF_MONITOR_PORT` | Porta dell'agent PDF Monitor | 8001 |
| `BACKEND_PORT` | Porta del backend PramaIAServer | 8000 |
| `BACKEND_HOST` | Host del backend | localhost |
| `PDK_SERVER_PORT` | Porta del PDK Server | 3001 |

## 🛠️ Possibili miglioramenti

1. **Compressione dei file**: Implementare compressione per PDF di grandi dimensioni
2. **Autenticazione API**: Aggiungere token di autenticazione per maggiore sicurezza
3. **Batching**: Supporto per invio di più file in batch
4. **Feedback real-time**: Implementare websocket per aggiornamenti in tempo reale
5. **Monitoraggio avanzato**: Aggiungere metriche e dashboard per monitoraggio performance

---

**Documentazione tecnica** - v1.0.0 (05/08/2025)
