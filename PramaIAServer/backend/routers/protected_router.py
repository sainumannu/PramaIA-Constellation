# protected_router.py
from fastapi import APIRouter, Depends
import logging
from backend.auth.dependencies import get_current_user, get_current_admin_user # Non importare User da qui
from backend.schemas.user_schemas import UserInToken # Importa il modello Pydantic corretto

logger = logging.getLogger(__name__)
logger.info("--- protected_router.py: Modulo in fase di caricamento ---") # LOG DIAGNOSTICO

router = APIRouter()
logger.info("--- protected_router.py: Istanza APIRouter creata ---") # LOG DIAGNOSTICO

@router.get("/me", response_model=UserInToken) # Il response_model è già corretto
async def read_users_me(current_user: UserInToken = Depends(get_current_user)):
    """
    Restituisce le informazioni dell'utente corrente autenticato.
    """
    logger.info(f"Richiesta ricevuta per /protected/me per l'utente: {current_user.user_id}")
    return current_user

@router.get("/test") # NUOVO ENDPOINT DI TEST
async def test_protected_route():
    logger.info("Richiesta ricevuta per /protected/test")
    return {"message": "Protected router test endpoint reached!"}

@router.get("/admin/area")
async def admin_area(current_user: UserInToken = Depends(get_current_admin_user)):
    logger.info(f"Accesso all'area admin da parte di: {current_user.user_id}")
    return {"message": f"Ciao {current_user.name}, sei un amministratore!", "email": current_user.email}

@router.get("/utente/area")
async def user_area(current_user: UserInToken = Depends(get_current_user)):
    logger.info(f"Accesso all'area utente da parte di: {current_user.user_id}")
    return {"message": f"Benvenuto {current_user.name}, il tuo ruolo è '{current_user.role}'", "email": current_user.email}
