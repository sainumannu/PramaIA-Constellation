# dependencies.py
from fastapi import Depends, HTTPException, status, Request
from typing import Optional
import jwt
import logging
from backend.schemas.user_schemas import UserInToken # Importa il nuovo modello Pydantic per l'utente nel token
# Importa le impostazioni di autenticazione centralizzate
from backend.core.config_auth import settings # Assicurati che questo percorso sia corretto

logger = logging.getLogger(__name__) # Configura un logger

def get_current_user(request: Request) -> UserInToken:
    auth_header: Optional[str] = request.headers.get("Authorization")
    logger.info(f"🔍 AUTH DEBUG: Authorization header: {auth_header[:50] if auth_header else 'None'}...")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("Tentativo di accesso senza token o header malformato.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token mancante")

    token = auth_header.split(" ")[1]
    logger.info(f"🔍 AUTH DEBUG: Token estratto: {token[:30]}...{token[-10:]} (lunghezza: {len(token)})")
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        logger.info(f"🔍 AUTH DEBUG: Token decodificato con successo. Payload: {payload}")
        # logger.debug(f"Decoded payload: {payload}") # Logga il payload per debug se necessario

        # Verifica che i campi necessari siano presenti nel payload
        username_from_token = payload.get("sub") # 'sub' contiene l'username
        user_name_from_token = payload.get("name")
        user_id_from_token = payload.get("user_id") # Aggiunto per coerenza con il token
        user_role_from_token = payload.get("role")

        if not all([username_from_token, user_role_from_token]): # name è opzionale
            logger.warning(f"Payload JWT incompleto: sub='{username_from_token}', name='{user_name_from_token}', role='{user_role_from_token}', user_id='{user_id_from_token}'")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Payload del token incompleto o malformato")

        return UserInToken(
            username=username_from_token, # Mappa 'sub' a 'username'
            email=payload.get("email"), # Se presente nel token (non lo è nel nostro esempio attuale)
            name=user_name_from_token,
            role=user_role_from_token
        )
    except jwt.ExpiredSignatureError:
        logger.info(f"Tentativo di accesso con token scaduto. Token: {token[:20]}...")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token scaduto")
    except jwt.InvalidTokenError:
        logger.warning(f"Tentativo di accesso con token non valido. Token: {token[:20]}...")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token non valido")
    except Exception as e: # Cattura altre eccezioni impreviste durante la decodifica
        logger.error(f"Errore imprevisto durante la decodifica del token: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Errore durante la validazione del token")

def get_current_user_optional(request: Request) -> Optional[UserInToken]:
    """
    Versione opzionale di get_current_user che restituisce None se non c'è autenticazione
    invece di sollevare un'eccezione. Utile per endpoint che accettano richieste sia
    autenticate che non autenticate.
    """
    auth_header: Optional[str] = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        # Nessun token fornito, restituisce None
        return None

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        
        username_from_token = payload.get("sub")
        user_name_from_token = payload.get("name")
        user_id_from_token = payload.get("user_id")
        user_role_from_token = payload.get("role")

        if not all([username_from_token, user_role_from_token]):
            logger.warning(f"Payload JWT incompleto in auth opzionale")
            return None

        return UserInToken(
            username=username_from_token,
            email=payload.get("email"),
            name=user_name_from_token,
            role=user_role_from_token
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        logger.info(f"Token non valido in auth opzionale: {type(e).__name__}")
        return None
    except Exception as e:
        logger.error(f"Errore imprevisto in auth opzionale: {e}")
        return None

def get_current_admin_user(current_user: UserInToken = Depends(get_current_user)):
    """
    Dipendenza che verifica se l'utente corrente è un amministratore.
    Altrimenti, solleva un'eccezione HTTP 403 Forbidden.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accesso riservato agli admin")
    return current_user

def is_admin_user(user: UserInToken) -> bool:
    """
    Verifica se un utente ha privilegi di amministratore
    """
    return user.role == "admin"
