from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import requests

# Importa le funzioni dal servizio utente consolidato
from backend.services import user_service
# Importa il modello Pydantic corretto per l'utente autenticato
from backend.schemas.user_schemas import UserSchema as User, UserCreate, UserUpdate # Corretto il percorso di importazione e rinominato UserSchema in User
from backend.auth import get_current_admin_user
from backend.db.database import get_db
from backend.core.config import OPENAI_API_KEY

app = FastAPI()

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(get_current_admin_user)],
    responses={403: {"description": "Operation not permitted"}},
)

@router.get("/users/", response_model=List[User]) # User qui è UserSchema
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Recupera la lista di tutti gli utenti. Richiede privilegi di amministratore.
    """
    users = user_service.get_users(db, skip=skip, limit=limit)
    return users

@router.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Crea un nuovo utente. Richiede privilegi di amministratore.
    """
    # Verifichiamo che l'email sia valida e presente prima di cercarla
    if user.email:
        db_user = user_service.get_user_by_email(db, email=str(user.email))
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
    return user_service.create_user(db=db, user_in=user)

@router.put("/users/{user_id}", response_model=User)
def update_existing_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
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

@router.get("/openai-credit")
def get_openai_credit():
    """
    Recupera le informazioni sul credito OpenAI per l'amministratore.
    """
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    url = "https://api.openai.com/dashboard/billing/credit_grants"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {"credit": data.get("total_available", 0.0)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore recupero credito: {e}")

# Rimuovere l'importazione circolare e l'inclusione del router
# Questa operazione deve essere fatta nel file main.py
