from fastapi import APIRouter
from .session_management import router as session_router
from .document_management import router as document_router
from .admin_operations import router as admin_router
from .monitoring import router as monitoring_router

router = APIRouter()
router.include_router(session_router, tags=["Session Management"])
router.include_router(document_router, tags=["Document Management"])
router.include_router(admin_router, tags=["Admin Operations"])
router.include_router(monitoring_router, tags=["Monitoring & Debug"])
