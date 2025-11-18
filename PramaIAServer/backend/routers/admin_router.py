from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
from backend.auth.dependencies import get_current_admin_user
from backend.db.database import get_db
from backend.core.config import OPENAI_API_KEY
import requests

# Importa i tuoi service e modelli
from backend.services import user_service
# PDF indexing migrato al PDK - ExecutionContext non più necessario
from backend.schemas.user_schemas import UserSchema, UserUpdate, UserCreate

router = APIRouter()

# --- Gestione Utenti ---
@router.get("/users/", response_model=List[UserSchema])
def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)  # Assicura che solo gli admin possano accedere
):
    """
    Recupera la lista di tutti gli utenti. Richiede privilegi di amministratore.
    """
    users = user_service.get_users(db, skip=skip, limit=limit)
    return users

@router.post("/users/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_new_user(
    user: UserCreate, 
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)  # Assicura che solo gli admin possano accedere
):
    """
    Crea un nuovo utente. Richiede privilegi di amministratore.
    """
    # Verifichiamo che l'email sia valida e presente prima di cercarla
    if user.email:
        db_user = user_service.get_user_by_email(db, email=str(user.email))
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
    return user_service.create_user(db=db, user_in=user)

@router.put("/users/{user_id}", response_model=UserSchema)
def update_existing_user(
    user_id: int, 
    user: UserUpdate, 
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)  # Assicura che solo gli admin possano accedere
):
    """
    Aggiorna un utente esistente. Richiede privilegi di amministratore.
    """
    db_user = user_service.update_user(db, user_id=user_id, user_in=user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_user(user_id: int, db: Session = Depends(get_db)):
    """
    Elimina un utente esistente. Richiede privilegi di amministratore.
    """
    db_user = user_service.delete_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return

# --- Gestione Monitoraggio PDF ---
@router.post("/pdf/index")
async def force_pdf_indexing(
    file_path: Optional[str] = None,
    current_admin = Depends(get_current_admin_user)
):
    """
    DEPRECATO: L'indicizzazione PDF è stata migrata all'architettura PDK.
    Utilizzare il PDK server per gestire l'indicizzazione PDF.
    """
    return {
        "status": "deprecated",
        "message": "PDF indexing migrato al PDK. Utilizzare il PDK server su porta 3001.",
        "pdk_endpoint": "http://localhost:3001/api/plugins/pdf-semantic-complete-plugin/execute",
        "migration_note": "Le funzionalità PDF sono ora gestite tramite plugin PDK"
    }
