# backend/routers_init.py
# Includi qui tutti i router che vuoi importare in main.py

from backend.routers.auth_router import auth_router
from backend.routers.documents_router import documents_router
from backend.routers.chat_router import chat_router
from backend.routers.sessions_router import sessions_router
from backend.routers.protected_router import protected_router
from backend.routers.dashboard_router import dashboard_router
from backend.routers.admin_router import admin_router
from backend.routers.usage import usage_router
from backend.routers.update_prompt_router import update_prompt_router
from backend.routers.llm_router import llm_router
from backend.routers.document_monitor_router import router as document_monitor_router
from backend.routers.document_monitor_router_triggers import router as document_monitor_triggers_router
from backend.routers.workflow_triggers_router import router as workflow_triggers_router
# Aggiungi qui altri router se necessario

__all__ = [
    "auth_router",
    "documents_router",
    "chat_router",
    "sessions_router",
    "protected_router",
    "dashboard_router",
    "admin_router",
    "usage_router",
    "update_prompt_router",
    "llm_router",
    "document_monitor_router",
    "document_monitor_triggers_router",
    "workflow_triggers_router",
]
