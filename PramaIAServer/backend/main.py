# main.py
from fastapi import FastAPI
import logging
from fastapi.middleware.cors import CORSMiddleware

# Importa le configurazioni
from backend.core.config import FRONTEND_URL

# Importa i router
# Se questo blocco causa problemi, uno dei file router o __init__.py ha un errore
from backend.routers import (
    auth_router,
    documents_router,
    chat_router,
    sessions_router,
    protected_router,
    dashboard_router, # Assicurati che questo sia definito in backend.routers.__init__.py
    usage_router,     # Assicurati che questo sia definito in backend.routers.__init__.py
    update_prompt_router,
    llm_router,  # <--- AGGIUNTO
    pdf_monitor_compatibility_router,  # Corretto il nome dell'import
    workflow_router,  # Nuovo import per workflow
    pdk_router  # Aggiunto per gestire i nodi PDK
)

# Import per il workflow_triggers_router
from backend.routers.workflow_triggers_router import router as workflow_triggers_router

# Import per il router delle event sources
from backend.routers.event_sources_router import router as event_sources_router
from backend.routers.database_management_router import router as database_management_router

# Import per il router delle impostazioni
from backend.routers.settings_router import router as settings_router

# Import per il folder sync router
from backend.api.folder_sync_router import router as folder_sync_router

# Import per il router di compatibilità documenti
from backend.api.documents_compatibility_router import router as documents_compatibility_router

# Import per il PDK router (ora utilizzato attivamente)
# (Gestito tramite importazione normale sopra)

# Importa il router admin separatamente per rompere il ciclo di importazione
from backend.routers.admin import router as admin_router
from backend.routers.admin_router import router as admin_panel_router
from backend.routers import plugins_router

from backend.services.user_service import create_default_admin_user_if_not_exists # Per creare admin di default
from backend.db.database import SessionLocal # Importa SessionLocal per creare una sessione DB



# Configura un logger di base (DEBUG per mostrare tutti i dettagli)
import sys
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
# Forza DEBUG su tutti i logger dei moduli
for name in logging.root.manager.loggerDict:
    logging.getLogger(name).setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Avvio di main.py in modalità DEBUG forzato su tutti i moduli...")

app = FastAPI(debug=True)
logger.info("Istanza FastAPI creata.")

# Evento di startup per creare utente admin di default (opzionale)
@app.on_event("startup")
async def startup_event():
    # Usa un context manager per assicurare che la sessione del DB sia chiusa correttamente
    with SessionLocal() as db:
        create_default_admin_user_if_not_exists(db=db)

origins = [
    FRONTEND_URL,
    "http://localhost:3000",  # Aggiungiamo esplicitamente localhost:3000
    "http://127.0.0.1:3000",  # Aggiungiamo anche 127.0.0.1:3000
    "*",                      # Per debug temporaneo - RIMUOVERE IN PRODUZIONE!
]

logger.info(f"🌍 Configurazione CORS - Origini consentite: {origins}")
logger.info(f"🌍 FRONTEND_URL configurato: {FRONTEND_URL}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("✅ CORSMiddleware aggiunto con successo.")

@app.get("/")
async def read_root_main_app():
    logger.info("Richiesta ricevuta a / nell'app principale.")
    return {"message": "App principale (semplificata) funzionante!"}

# Includi i router
try:
    logger.info("Inclusione routers...")
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    logger.info("auth_router incluso.")
    app.include_router(documents_router, prefix="/api/documents", tags=["documents"])
    logger.info("documents_router incluso.")
    app.include_router(chat_router, prefix="/chat", tags=["chat"])
    logger.info("chat_router incluso.")
    app.include_router(sessions_router, prefix="/sessions", tags=["sessions"])
    logger.info("sessions_router incluso.")
    app.include_router(protected_router, prefix="/protected", tags=["protected"])
    logger.info("protected_router incluso.")
    app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
    logger.info("dashboard_router incluso.")
    app.include_router(admin_router, prefix="/admin", tags=["admin"]) # <-- Aggiunto prefix
    logger.info("admin_router incluso.")
    app.include_router(admin_panel_router, prefix="/admin-panel", tags=["admin-panel"]) # <-- Nuovo router
    logger.info("admin_panel_router incluso.")
    app.include_router(usage_router, prefix="/usage", tags=["usage"])
    logger.info("usage_router incluso.")
    app.include_router(update_prompt_router, tags=["update-prompt"])
    logger.info("update_prompt_router incluso.")
    app.include_router(llm_router, prefix="/llm", tags=["llm"])
    logger.info("llm_router incluso.")
    app.include_router(plugins_router)  # <-- AGGIUNTO: espone /api/pdf-monitor/clients
    logger.info("plugins_router incluso.")
    app.include_router(pdf_monitor_compatibility_router)  # Nuovo endpoint ricezione PDF dal plugin
    logger.info("pdf_monitor_compatibility_router incluso.")
    app.include_router(pdk_router, prefix="/api/workflows", tags=["pdk"])  # Router PDK per gestire nodi dinamici
    logger.info("pdk_router incluso.")
    app.include_router(workflow_triggers_router, prefix="/api/workflows/triggers", tags=["workflow-triggers"])  # Router per i trigger (PRIMA di workflow_router!)
    logger.info("workflow_triggers_router incluso.")
    app.include_router(workflow_router)  # Il prefix /api/workflows è già definito nel router
    logger.info("workflow_router incluso.")
    app.include_router(event_sources_router, tags=["event-sources"])  # Router per le sorgenti di eventi
    app.include_router(database_management_router, tags=["database-management"])  # Router per gestione database e reset
    app.include_router(settings_router, tags=["settings"])  # Router per gestione impostazioni
    app.include_router(folder_sync_router, tags=["folder-sync"])  # Router per sincronizzazione cartelle
    app.include_router(documents_compatibility_router, tags=["documents-compatibility"])  # Router di compatibilità per i documenti
    logger.info("event_sources_router incluso.")
    logger.info("folder_sync_router incluso.")
    logger.info("documents_compatibility_router incluso.")
    logger.info("Tutti i router inclusi con successo.")
except Exception as e:
    logger.error(f"Errore durante l'inclusione dei router: {e}", exc_info=True)
    raise

logger.info("Fine configurazione di main.py.")