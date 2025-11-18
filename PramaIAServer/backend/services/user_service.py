# user_service.py
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
import re

from backend.db import models # Importa i modelli SQLAlchemy
from backend.schemas.user_schemas import UserCreate, UserUpdate # UserInDB non è più necessario qui
from backend.core.config_auth import settings # Importa le tue impostazioni
from backend.security.password_utils import get_password_hash, verify_password # Importa le funzioni di hashing

# Configura un logger per questo modulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # <--- AGGIUNGI QUESTA RIGA per forzare il livello DEBUG per questo logger

# Regex per validazione email
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def validate_email(email: str) -> bool:
    """Valida il formato dell'email."""
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email))

def sanitize_string(value: str, max_length: int = 255) -> str:
    """Sanitizza e tronca le stringhe di input."""
    if not value:
        return ""
    # Rimuovi caratteri di controllo e whitespace eccessivi
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', str(value).strip())
    return sanitized[:max_length]

def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    """Recupera un utente per ID."""
    if not user_id or user_id <= 0:
        return None
    
    try:
        return db.query(models.User).filter(models.User.id == user_id).first()
    except SQLAlchemyError as e:
        logger.error(f"USER_SERVICE: Database error while getting user by ID {user_id}: {str(e)}")
        return None

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Recupera un utente per username."""
    if not username or not username.strip():
        return None
    
    username = sanitize_string(username).lower()
    logger.debug(f"USER_SERVICE: Querying for username: '{username}'")
    
    try:
        user = db.query(models.User).filter(models.User.username == username).first()
        if user:
            logger.debug(f"USER_SERVICE: User '{username}' found in DB.")
        else:
            logger.debug(f"USER_SERVICE: User '{username}' NOT found in DB.")
        return user
    except SQLAlchemyError as e:
        logger.error(f"USER_SERVICE: Database error while getting user by username '{username}': {str(e)}")
        return None

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Recupera un utente per email."""
    if not email or not email.strip():
        return None
    
    email = sanitize_string(email).lower()
    if not validate_email(email):
        logger.warning(f"USER_SERVICE: Invalid email format: '{email}'")
        return None
    
    try:
        return db.query(models.User).filter(models.User.email == email).first()
    except SQLAlchemyError as e:
        logger.error(f"USER_SERVICE: Database error while getting user by email '{email}': {str(e)}")
        return None

def get_or_create_user_oauth(db: Session, user_info: Dict[str, Any]) -> models.User:
    """
    Recupera un utente dal DB basandosi sulle informazioni di OAuth (es. Azure AD).
    Se l'utente non esiste, lo crea.
    user_info dovrebbe contenere 'preferred_username' o 'email', 'name', 'oid' (per user_id),
    e 'role'.
    """
    if not user_info:
        logger.error("USER_SERVICE: OAuth login failed - Empty user info provided.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user information provided by authentication provider."
        )

    # L'email è l'identificatore più comune e affidabile.
    # Azure AD la fornisce nel campo 'preferred_username' o 'email'.
    email = user_info.get("preferred_username") or user_info.get("email")
    if not email:
        logger.error("USER_SERVICE: OAuth login failed - Email not found in user info from provider.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not provided by the authentication provider."
        )
    
    email = sanitize_string(email).lower()
    if not validate_email(email):
        logger.error(f"USER_SERVICE: OAuth login failed - Invalid email format: '{email}'")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format provided by authentication provider."
        )
    
    oid = sanitize_string(user_info.get("oid", ""))  # Azure AD Object ID
    role = user_info.get("role", "user")  # Ruolo determinato da auth_router
    name = sanitize_string(user_info.get("name", ""))

    try:
        # 1. Cerca se un utente con questa email esiste già
        db_user = get_user_by_email(db, email=email)

        if db_user:
            logger.info(f"USER_SERVICE: OAuth user found with email '{email}'. User ID: {db_user.id}")
            # Assicurati che il campo user_id sia impostato se mancante.
            if db_user.user_id is None and oid:  # Se user_id non è impostato e abbiamo un OID
                setattr(db_user, 'user_id', oid)
                db.commit()
                db.refresh(db_user)
            return db_user
        else:
            # 2. Se l'utente non esiste, creane uno nuovo.
            logger.info(f"USER_SERVICE: No existing user with email '{email}'. Creating new OAuth user.")
            
            # Usa l'email come username di default, che è unico.
            username = email

            # Gli utenti OAuth non hanno una password gestita localmente.
            # Il campo hashed_password può essere lasciato nullo.
            new_user = models.User(
                username=username,
                email=email,
                name=name,
                hashed_password=None,  # Nessuna password locale
                user_id=oid,  # Usa OID come user_id
                is_active=True,
                role=role  # Usa il ruolo determinato da auth_router
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            logger.info(f"USER_SERVICE: New OAuth user '{new_user.username}' created successfully with ID: {new_user.id}")
            return new_user
            
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"USER_SERVICE: Database error during OAuth user creation for '{email}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during user creation."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"USER_SERVICE: Unexpected error during OAuth user creation for '{email}': {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error during user creation."
        )

def create_user(db: Session, user_in: UserCreate) -> models.User:
    """Crea un nuovo utente con validazioni complete."""
    if not user_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User data is required"
        )
    
    # Validazioni input
    username = sanitize_string(user_in.username).lower()
    if not username or len(username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters long"
        )
    
    if user_in.email:
        email = sanitize_string(user_in.email).lower()
        if not validate_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
    else:
        email = None
    
    name = sanitize_string(user_in.name) if user_in.name else ""
    
    if not user_in.password or len(user_in.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )

    logger.info(f"USER_SERVICE: Attempting to create user: '{username}' with email: '{email}'")
    
    try:
        # Controlla username esistente
        if get_user_by_username(db, username):
            logger.warning(f"USER_SERVICE: Username '{username}' already registered.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )
        
        # Controlla email esistente
        if email and get_user_by_email(db, email):
            logger.warning(f"USER_SERVICE: Email '{email}' already registered.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        hashed_password = get_password_hash(user_in.password)
        logger.debug(f"USER_SERVICE: Password for '{username}' hashed successfully")
        
        db_user = models.User(
            username=username,
            hashed_password=hashed_password,
            email=email,
            name=name,
            role=getattr(user_in, 'role', 'user'),
            is_active=getattr(user_in, 'is_active', True),
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"USER_SERVICE: User '{db_user.username}' created successfully with ID: {db_user.id}")
        return db_user
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"USER_SERVICE: Database error creating user '{username}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during user creation"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"USER_SERVICE: Unexpected error creating user '{username}': {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error during user creation"
        )

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """Recupera una lista di utenti con paginazione."""
    if skip < 0:
        skip = 0
    if limit <= 0 or limit > 1000:  # Limite massimo per sicurezza
        limit = 100
    
    try:
        return db.query(models.User).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"USER_SERVICE: Database error while getting users: {str(e)}")
        return []

def update_user(db: Session, user_id: int, user_in: UserUpdate) -> Optional[models.User]:
    """Aggiorna un utente esistente con validazioni complete."""
    if not user_id or user_id <= 0:
        return None
    
    if not user_in:
        return None
    
    try:
        user_db = get_user_by_id(db, user_id)
        if not user_db:
            return None

        update_data = user_in.model_dump(exclude_unset=True)
        
        # Validazione username se presente
        if "username" in update_data:
            new_username = sanitize_string(update_data["username"]).lower()
            if not new_username or len(new_username) < 3:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Username must be at least 3 characters long"
                )
            
            if new_username != user_db.username and get_user_by_username(db, new_username):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Username already taken"
                )
            update_data["username"] = new_username
        
        # Validazione email se presente
        if "email" in update_data and update_data["email"]:
            new_email = sanitize_string(update_data["email"]).lower()
            if not validate_email(new_email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Invalid email format"
                )
            
            if new_email != user_db.email and get_user_by_email(db, new_email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Email already taken"
                )
            update_data["email"] = new_email

        # Gestione password
        if "password" in update_data and update_data["password"]:
            if len(update_data["password"]) < 6:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Password must be at least 6 characters long"
                )
            hashed_password = get_password_hash(update_data["password"])
            setattr(user_db, 'hashed_password', hashed_password)
            del update_data["password"]

        # Sanitizza il nome se presente
        if "name" in update_data:
            update_data["name"] = sanitize_string(update_data["name"])

        # Applica le altre modifiche
        for field, value in update_data.items():
            if hasattr(user_db, field):
                setattr(user_db, field, value)
        
        db.add(user_db) 
        db.commit()
        db.refresh(user_db)
        logger.info(f"USER_SERVICE: User '{user_db.username}' updated successfully")
        return user_db
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"USER_SERVICE: Database error updating user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during user update"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"USER_SERVICE: Unexpected error updating user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error during user update"
        )

def delete_user(db: Session, user_id: int) -> Optional[models.User]:
    """Elimina un utente per ID."""
    if not user_id or user_id <= 0:
        return None
    
    try:
        user_db = get_user_by_id(db, user_id)
        if user_db:
            db.delete(user_db)
            db.commit()
            logger.info(f"USER_SERVICE: User '{user_db.username}' (ID: {user_id}) deleted successfully")
            return user_db
        return None
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"USER_SERVICE: Database error deleting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during user deletion"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"USER_SERVICE: Unexpected error deleting user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error during user deletion"
        )

def authenticate_user(db: Session, username: str, password_to_check: str) -> Optional[models.User]:
    """Autentica un utente con username e password."""
    if not username or not username.strip():
        logger.warning("USER_SERVICE: Authentication failed - Empty username provided.")
        return None
    
    if not password_to_check:
        logger.warning("USER_SERVICE: Authentication failed - Empty password provided.")
        return None
    
    username = sanitize_string(username).lower()
    
    try:
        user = get_user_by_username(db, username=username)
        if not user:
            logger.warning(f"USER_SERVICE: Authentication failed - User '{username}' not found in database.")
            return None
        
        logger.info(f"USER_SERVICE: User '{username}' found in database. ID: {user.id}. Proceeding to verify password.")
        
        # Controlla se l'utente ha una password (utenti OAuth potrebbero non averla)
        if user.hashed_password is None:
            logger.warning(f"USER_SERVICE: Authentication failed - User '{username}' has no password (OAuth user?).")
            return None
        
        # Rimuovi il logging della password per sicurezza
        logger.debug(f"USER_SERVICE: Verifying password for user '{username}'")

        if not verify_password(password_to_check, str(user.hashed_password)):
            logger.warning(f"USER_SERVICE: Authentication failed - Password mismatch for user '{username}'.")
            return None
        
        logger.info(f"USER_SERVICE: User '{username}' authenticated successfully.")
        return user
        
    except SQLAlchemyError as e:
        logger.error(f"USER_SERVICE: Database error during authentication for '{username}': {str(e)}")
        return None
    except Exception as e:
        logger.error(f"USER_SERVICE: Unexpected error during authentication for '{username}': {str(e)}", exc_info=True)
        return None

# Funzione di inizializzazione per creare un utente admin di default
def create_default_admin_user_if_not_exists(db: Session): 
    """Crea un utente admin di default se non esiste."""
    try:
        admin_username = getattr(settings, 'DEFAULT_ADMIN_USERNAME', None)
        admin_password = getattr(settings, 'DEFAULT_ADMIN_PASSWORD', None)
        admin_email = getattr(settings, 'DEFAULT_ADMIN_EMAIL', None)
        
        if not admin_username or not admin_password:
            logger.warning("USER_SERVICE: Default admin username or password not configured in settings. Skipping default admin creation.")
            return

        admin_username = sanitize_string(admin_username).lower()
        
        if not get_user_by_username(db, admin_username): 
            logger.info(f"USER_SERVICE: Default admin user '{admin_username}' not found. Creating...")
            
            # Assicurati che l'email sia fornita o gestisci il caso in cui sia None
            if admin_email:
                current_admin_email = sanitize_string(admin_email).lower()
                if not validate_email(current_admin_email):
                    current_admin_email = f"{admin_username}@admin.local"
            else:
                current_admin_email = f"{admin_username}@admin.local"

            admin_user_data = UserCreate(
                username=admin_username,
                password=admin_password,
                name="Administrator", 
                role="admin",
                is_active=True,
                email=current_admin_email
            )
            
            try:
                created_admin = create_user(db, admin_user_data) 
                logger.info(f"USER_SERVICE: Default admin user '{created_admin.username}' created successfully.")
            except HTTPException as e:
                logger.error(f"USER_SERVICE: HTTPException while creating default admin user '{admin_username}': {e.detail}")
            except Exception as e:
                logger.error(f"USER_SERVICE: Unexpected error while creating default admin user '{admin_username}': {str(e)}", exc_info=True)
        else:
            logger.info(f"USER_SERVICE: Default admin user '{admin_username}' already exists.")
            
    except Exception as e:
        logger.error(f"USER_SERVICE: Unexpected error during admin user creation check: {str(e)}", exc_info=True)
