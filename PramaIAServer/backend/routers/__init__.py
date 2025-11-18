
# Questo file rende la cartella 'routers' un pacchetto Python
# e permette di importare i suoi moduli o le variabili definite qui.

# Importa i moduli router in modo che siano accessibili come backend.routers.auth_router, ecc.
# Questo permette di usare router.router in main.py

from .auth_router import router as auth_router
from .documents_router import router as documents_router
from .chat_router import router as chat_router
from .sessions_router import router as sessions_router
from .protected_router import router as protected_router
from .dashboard_router import router as dashboard_router
from .update_prompt_router import router as update_prompt_router
from .llm_router import router as llm_router
from .plugins_router import router as plugins_router
from .usage import usage_router
from .document_monitor_router import router as document_monitor_router
from .workflow_router import router as workflow_router
from .pdk_router import router as pdk_router
from .pdf_monitor_compatibility_router import router as pdf_monitor_compatibility_router
