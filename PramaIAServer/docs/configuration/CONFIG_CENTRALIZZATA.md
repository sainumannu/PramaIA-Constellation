# Configurazione Centralizzata PramaIA

## Panoramica

Tutto l'ecosistema PramaIA è stato configurato per usare una configurazione centralizzata che elimina i valori hardcoded e permette una gestione flessibile delle porte e degli URL.

## Architettura della configurazione

### Sistema gerarchico

L'ecosistema PramaIA usa un sistema di configurazione gerarchico:

1. **Configurazione principale**: `PramaIAServer/.env` (contiene tutte le configurazioni sensibili)
2. **Configurazioni specifiche**: Ogni progetto può avere il proprio `.env` per sovrascrivere valori specifici
3. **Template globale**: `.env.example` nella root come riferimento

### File di configurazione

#### File principali
- **`PramaIAServer/.env`** 🔐: File principale con API keys, JWT secrets, OAuth, configurazioni di produzione
- **`PramaIA-PDK/.env`**: Configurazioni specifiche del PDK (porte, timeout)
- **`PramaIA-Plugins/pdf-folder-monitor-plugin/.env`**: Configurazioni specifiche del plugin
- **`.env.example`** (root): Template di riferimento per tutte le configurazioni

#### File di codice configurati
- **`backend/core/config.py`**: Configurazione centralizzata del backend Python
- **`frontend/client/src/config/appConfig.js`**: Configurazione centralizzata del frontend React  
- **`PramaIA-PDK/src/config/index.ts`**: Configurazione centralizzata del PDK TypeScript
- **`start-all-clean.ps1`**: Script PowerShell che carica automaticamente le configurazioni

### Setup iniziale

**Il file `PramaIAServer/.env` è già configurato e contiene le tue credenziali.** Non è necessario copiare nulla.

#### Per personalizzazioni aggiuntive:

1. Le configurazioni delle porte sono già integrate nel tuo `.env` esistente
2. I singoli progetti possono sovrascrivere configurazioni specifiche nei loro `.env` locali
3. Lo script `start-all-clean.ps1` carica automaticamente le configurazioni dal file principale

#### Per nuovi ambienti:
```bash
# Solo se crei un nuovo ambiente
cp .env.example PramaIAServer/.env
# Quindi modifica con le tue credenziali
```

## Porte predefinite

| Servizio | Porta | Variabile ambiente |
|----------|-------|--------------------|
| Backend FastAPI | 8000 | `BACKEND_PORT` |
| Frontend React | 3000 | `FRONTEND_PORT` |
| Plugin PDF Monitor | 8001 | `PLUGIN_PDF_MONITOR_PORT` |
| PDK Server | 3001 | `PDK_SERVER_PORT` |

## Configurazioni per componente

### Backend (Python/FastAPI)
- File: `backend/core/config.py`
- Legge da: variabili d'ambiente o valori di default
- Configurazioni: porte, URL, API keys, debug flags

### Frontend (React)
- File: `frontend/client/src/config/appConfig.js`
- Legge da: variabili d'ambiente `REACT_APP_*` o valori di default
- Configurazioni: porte, URL API, URL Ollama

### PDK (TypeScript/Node.js)
- File: `PramaIA-PDK/src/config/index.ts`
- Legge da: variabili d'ambiente `process.env.*` o valori di default
- Configurazioni: porte, URL, timeout

### Plugin PDF Monitor (Python)
- File: `PramaIA-Plugins/pdf-folder-monitor-plugin/src/main.py`
- Legge da: variabili d'ambiente `os.getenv()` o valori di default
- Configurazioni: porte backend e plugin

### Script di avvio (PowerShell)
- File: `start-all-clean.ps1`
- Legge da: variabili d'ambiente PowerShell `$env:*` o valori di default
- Configurazioni: porte di tutti i servizi

## Come funziona

### 1. Configurazione principale (`PramaIAServer/.env`)
Contiene tutte le configurazioni sensibili e di base:
```bash
# Sicurezza e API
OPENAI_API_KEY=sk-proj-xxx...
CLIENT_ID=xxx
CLIENT_SECRET=xxx
JWT_SECRET=xxx

# Porte e URL (aggiunte alla tua configurazione esistente)
BACKEND_PORT=8000
FRONTEND_PORT=3000
PLUGIN_PDF_MONITOR_PORT=8001
PDK_SERVER_PORT=3001
```

### 2. Script PowerShell intelligente
Lo script `start-all-clean.ps1` ora:
- Carica automaticamente le configurazioni da `PramaIAServer/.env`
- Usa le porte configurate per avviare tutti i servizi
- Mostra i valori caricati per trasparenza

### 3. Precedenza delle configurazioni
1. Variabili d'ambiente di sistema (massima priorità)
2. File `.env` specifico del progetto  
3. File `PramaIAServer/.env` principale
4. Valori di default nel codice (minima priorità)

## Utilizzo

### Avvio normale (usa il tuo .env esistente)
```powershell
.\start-all-clean.ps1
```

### Cambiare porte temporaneamente
```powershell
$env:FRONTEND_PORT=3001
.\start-all-clean.ps1
```

### Cambiare porte permanentemente
Modifica `PramaIAServer/.env` e cambia i valori delle porte.

## Vantaggi della configurazione centralizzata

1. **Eliminazione valori hardcoded**: Nessun numero di porta o URL è più hardcoded nel codice
2. **Flessibilità**: Cambio porte facilmente tramite variabili d'ambiente
3. **Ambiente-specifico**: Configurazioni diverse per sviluppo, test, produzione
4. **Manutenzione semplificata**: Un unico punto di configurazione per tutto l'ecosistema
5. **Deploy facilitato**: Configurazione via environment variables per Docker/Cloud

## Struttura delle variabili d'ambiente

```bash
# Porte servizi
BACKEND_PORT=8000
FRONTEND_PORT=3000
PLUGIN_PDF_MONITOR_PORT=8001
PDK_SERVER_PORT=3001

# URL calcolati automaticamente
BACKEND_BASE_URL=http://localhost:8000
FRONTEND_BASE_URL=http://localhost:3000
# ... etc

# Configurazioni React (prefisso REACT_APP_)
REACT_APP_BACKEND_PORT=8000
REACT_APP_BACKEND_BASE_URL=http://localhost:8000
# ... etc
```

## Note tecniche

- Il frontend React richiede il prefisso `REACT_APP_` per le variabili d'ambiente
- Il PDK TypeScript supporta le variabili d'ambiente Node.js standard
- Il backend Python usa `python-dotenv` per caricare il file `.env`
- Lo script PowerShell legge le variabili d'ambiente del sistema
