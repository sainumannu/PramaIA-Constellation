from pathlib import Path
import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente. python-dotenv cercherà un file .env
# nella directory di lavoro corrente (CWD) o nelle directory parent.
# Se avvii l'app da PramaIA/, e PramaIA/.env esiste, verrà caricato.
# Questo è coerente con come Pydantic BaseSettings (usato in config_auth.py)
# carica il file .env specificato come "env_file = '.env'".
load_dotenv()

# Se vuoi essere più esplicito sulla posizione del .env rispetto alla root del progetto:
# PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent # Sale di due livelli da 'core' per arrivare a 'PramaIA'
# load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEBUG_CLASSIFICATION = os.getenv("DEBUG_CLASSIFICATION", "false").lower() == "true"

# Utilizziamo nomi coerenti con il file .env (*_BASE_URL), mantenendo compatibilità con *_URL
# NOTA: Le porte e gli URL si definiscono SOLO nel file .env
# - In .env si imposta: FRONTEND_PORT, FRONTEND_BASE_URL
# - In config.py si leggono e si espongono come variabili con un valore di default

# Configurazione Frontend
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "3000"))
# Compatibilità: supportiamo sia FRONTEND_URL che FRONTEND_BASE_URL, ma privilegiamo FRONTEND_BASE_URL
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL") or os.getenv("FRONTEND_URL") or f"http://localhost:{FRONTEND_PORT}"
# Alias per compatibilità con il codice esistente
FRONTEND_URL = FRONTEND_BASE_URL

# Configurazione Backend
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL") or os.getenv("BACKEND_URL") or f"http://localhost:{BACKEND_PORT}"
BACKEND_URL = BACKEND_BASE_URL

# Configurazione PDK
PDK_SERVER_PORT = int(os.getenv("PDK_SERVER_PORT", "3001"))
# Compatibilità: supportiamo sia PDK_SERVER_URL che PDK_SERVER_BASE_URL, ma privilegiamo PDK_SERVER_BASE_URL
PDK_SERVER_BASE_URL = os.getenv("PDK_SERVER_BASE_URL") or os.getenv("PDK_SERVER_URL") or f"http://localhost:{PDK_SERVER_PORT}"
# Alias per compatibilità con il codice esistente
PDK_SERVER_URL = PDK_SERVER_BASE_URL

# Configurazione VectorstoreService
VECTORSTORE_SERVICE_PORT = int(os.getenv("VECTORSTORE_SERVICE_PORT", "8090"))
VECTORSTORE_SERVICE_BASE_URL = os.getenv("VECTORSTORE_SERVICE_BASE_URL") or f"http://localhost:{VECTORSTORE_SERVICE_PORT}"
# Flag per abilitare/disabilitare il servizio vectorstore
USE_VECTORSTORE_SERVICE = os.getenv("USE_VECTORSTORE_SERVICE", "true").lower() == "true"

# Configurazione Riconciliazione Vectorstore
VECTORSTORE_RECONCILIATION_ENABLED = os.getenv("VECTORSTORE_RECONCILIATION_ENABLED", "true").lower() == "true"
VECTORSTORE_RECONCILIATION_TIME = os.getenv("VECTORSTORE_RECONCILIATION_TIME", "03:00")
VECTORSTORE_MAX_WORKER_THREADS = int(os.getenv("VECTORSTORE_MAX_WORKER_THREADS", "4"))
VECTORSTORE_BATCH_SIZE = int(os.getenv("VECTORSTORE_BATCH_SIZE", "100"))

BACKEND_DIR = Path(__file__).resolve().parent.parent # PramaIA/backend/
PROJECT_ROOT_DIR = BACKEND_DIR.parent # PramaIA/

# Cartelle principali
DB_DIR = BACKEND_DIR / "db" # PramaIA/backend/db/
DATA_DIR = BACKEND_DIR / "data" # Legacy: PramaIA/backend/data/
INDEXES_DIR = BACKEND_DIR / "indexes" # Ad esempio, PramaIA/backend/indexes/
LOGS_DIR = PROJECT_ROOT_DIR / "logs" # Modificato per puntare a PramaIA/logs/

# Verifica se esiste la cartella data (per compatibilità)
if not DATA_DIR.exists() and DB_DIR.exists():
    DATA_DIR = DB_DIR  # Reindirizza a DB_DIR se data non esiste

DATA_INDEX_PATH = DATA_DIR / "index.json"
TOKEN_LOG_PATH = LOGS_DIR / "tokens.jsonl"
STATE_FILE_PATH = INDEXES_DIR / "last_file.txt" # Considera se questo è ancora usato o se RAG_STATE_FILE_PATH lo sostituisce

RAG_TOKEN_LOG_PATH = LOGS_DIR / "rag_interactions.jsonl" # Nome più specifico
RAG_STATE_FILE_PATH = INDEXES_DIR / "rag_last_file.txt"
RAG_DATA_DIR = DATA_DIR # O una sottocartella specifica per i file RAG
RAG_INDEXES_DIR = INDEXES_DIR

# Configurazione gestione eventi PDF
# Mantieni solo gli eventi delle ultime x ore (default: 24)
PDF_EVENTS_MAX_AGE_HOURS = int(os.getenv("PDF_EVENTS_MAX_AGE_HOURS", "24"))
# Mantieni massimo x eventi (default: 1000)
PDF_EVENTS_MAX_COUNT = int(os.getenv("PDF_EVENTS_MAX_COUNT", "1000"))
# Esegui pulizia automatica quando si visualizzano gli eventi
PDF_EVENTS_AUTO_CLEANUP = os.getenv("PDF_EVENTS_AUTO_CLEANUP", "true").lower() == "true"
