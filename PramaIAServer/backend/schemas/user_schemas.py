from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    role: str = "user"
    is_active: bool = True

class UserCreate(UserBase):
    password: str # Password è obbligatoria per la creazione

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None # Per permettere il cambio password

class UserInDBBase(UserBase): # Base per i modelli che includono l'ID del DB
    id: int
    
    class Config:
        from_attributes = True # orm_mode = True per Pydantic v1

class UserSchema(UserInDBBase): # Schema per restituire l'utente, senza password
    pass

class UserInDB(UserInDBBase): # Schema interno al DB, con password hashata
    hashed_password: str

# Nuovo modello Pydantic per l'utente come rappresentato nel token JWT
class UserInToken(BaseModel):
    username: str
    name: Optional[str] = None
    role: str
    email: Optional[EmailStr] = None
    user_id: Optional[str] = None # ID univoco dal DB o OAuth