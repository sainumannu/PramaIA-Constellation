from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from backend.schemas.user_schemas import UserSchema, UserCreate, UserUpdate
from backend.services import user_service
from backend.auth.dependencies import get_current_user, admin_required
from backend.db.models import User as AuthUser # Per il type hinting di current_user

router = APIRouter()

@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_new_user(
    user_in: UserCreate,
    _: AuthUser = Depends(admin_required) # Solo admin può creare utenti
):
    """
    Crea un nuovo utente. Richiede privilegi di amministratore.
    """
    db_user = user_service.create_user(user_in=user_in)
    return db_user

@router.get("/", response_model=List[UserSchema])
def read_users_list(
    skip: int = 0,
    limit: int = 100,
    _: AuthUser = Depends(admin_required) # Solo admin può listare utenti
):
    """
    Recupera una lista di utenti. Richiede privilegi di amministratore.
    """
    users = user_service.get_users(skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=UserSchema)
def read_user_by_id(
    user_id: int,
    _: AuthUser = Depends(admin_required) # Solo admin può vedere dettagli specifici
):
    """
    Recupera un utente specifico per ID. Richiede privilegi di amministratore.
    """
    db_user = user_service.get_user_by_id(user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=UserSchema)
def update_existing_user(
    user_id: int,
    user_in: UserUpdate,
    _: AuthUser = Depends(admin_required) # Solo admin può aggiornare utenti
):
    """
    Aggiorna un utente esistente. Richiede privilegi di amministratore.
    """
    updated_user = user_service.update_user(user_id=user_id, user_in=user_in)
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated_user

@router.delete("/{user_id}", response_model=UserSchema)
def delete_existing_user(
    user_id: int,
    _: AuthUser = Depends(admin_required) # Solo admin può eliminare utenti
):
    """
    Elimina un utente esistente. Richiede privilegi di amministratore.
    """
    deleted_user = user_service.delete_user(user_id=user_id)
    if deleted_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return deleted_user