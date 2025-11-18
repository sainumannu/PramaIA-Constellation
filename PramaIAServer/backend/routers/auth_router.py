from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from msal import ConfidentialClientApplication
import uuid, jwt, requests, os
from urllib.parse import quote
from datetime import datetime, timedelta
from sqlalchemy.orm import Session # Importa Session

# Importa le impostazioni configurate
from backend.core.config_auth import settings
from backend.schemas.token import Token # Assicurati che questo schema esista
from backend.schemas.user_schemas import UserCreate # Importa lo schema per la creazione dell'utente
from backend.services import user_service # Importa il nuovo user_service
from backend.db.database import get_db # Importa get_db per la sessione
from backend.utils import get_logger # Importa il logger unificato
  
logger = get_logger()

router = APIRouter()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


# --- NUOVO ENDPOINT PER LOGIN USERNAME/PASSWORD ---
# Il path è stato cambiato in "/token/local" per corrispondere a quanto probabilmente
# chiama il frontend e per distinguerlo da un potenziale endpoint /token generico.
@router.post("/token/local", response_model=Token, tags=["Authentication"])
async def login_for_access_token_local( # Nome funzione aggiornato per chiarezza
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db) # Aggiungi la dipendenza dalla sessione DB
):
    """
    Autentica l'utente con username e password e restituisce un token JWT.
    """
    logger.info(
        "Ricevuta richiesta di login locale",
        details={"username": form_data.username},
        context={"component": "auth_router", "endpoint": "/token/local"}
    )
    # Passa db alla funzione di autenticazione
    user = user_service.authenticate_user(db, username=form_data.username, password_to_check=form_data.password)
    logger.info(
        f"Risultato autenticazione: {'Utente trovato' if user else 'Utente NON trovato'}",
        details={"username": form_data.username, "success": user is not None},
        context={"component": "auth_router", "endpoint": "/token/local"}
    )

    if not user:
        logger.warning(
            "Tentativo di login fallito",
            details={"username": form_data.username, "reason": "credenziali_errate"},
            context={"component": "auth_router", "endpoint": "/token/local", "security_event": True}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.is_active is not True:
        logger.warning(
            "Tentativo di login con utente inattivo",
            details={"username": form_data.username, "user_id": user.user_id, "reason": "utente_inattivo"},
            context={"component": "auth_router", "endpoint": "/token/local", "security_event": True}
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + access_token_expires
    to_encode = {
        "sub": user.username, # Usiamo username come 'subject' del token
        "name": user.name or user.username,
        "role": user.role,
        "user_id": user.user_id, # Aggiungi user_id al token
        "exp": expire
    }
    logger.info(
        f"Utente autenticato con successo",
        details={
            "username": user.username,
            "user_id": user.user_id,
            "role": user.role,
            "token_expiry": expire.isoformat()
        },
        context={"component": "auth_router", "endpoint": "/token/local", "security_event": True}
    )
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    logger.info(
        f"Token creato e pronto per l'invio",
        details={"username": user.username, "user_id": user.user_id},
        context={"component": "auth_router", "endpoint": "/token/local"}
    )
    return {"access_token": encoded_jwt, "token_type": "bearer"}

# --- Endpoint per Microsoft Login ---
# Se il router è montato con prefix="/auth" in main.py,
# il frontend chiamerà /auth/login, quindi il path qui deve essere solo "/login".
@router.get("/login", tags=["Authentication"])
def login_microsoft(): # Nome funzione aggiornato per chiarezza
    logger.info(
        "Richiesta di login Microsoft ricevuta",
        context={"component": "auth_router", "endpoint": "/login", "auth_type": "microsoft"}
    )
    try:
        logger.debug(
            "Configurazione auth Microsoft",
            details={
                "client_id": settings.CLIENT_ID,
                "authority": settings.AUTHORITY,
                "redirect_uri": str(settings.REDIRECT_URI),
                "scope": settings.SCOPE
            },
            context={"component": "auth_router", "endpoint": "/login"}
        )

        session_id = str(uuid.uuid4()) # Usato come 'state' per prevenire CSRF
        logger.info(
            "Generato session_id per la richiesta di autorizzazione",
            details={"session_id": session_id},
            context={"component": "auth_router", "endpoint": "/login", "security_event": True}
        )

        msal_app = ConfidentialClientApplication(
            client_id=settings.CLIENT_ID,
            client_credential=settings.CLIENT_SECRET,
            authority=settings.AUTHORITY,
        )
        logger.info(
            "Istanza MSAL creata per autorizzazione Microsoft",
            context={"component": "auth_router", "endpoint": "/login"}
        )

        auth_url = msal_app.get_authorization_request_url(
            scopes=settings.SCOPE,
            redirect_uri=str(settings.REDIRECT_URI),
            state=session_id, # Passa lo state
        )
        logger.info(
            "URL di autorizzazione generato",
            details={"auth_url_preview": auth_url[:100] + "..."},
            context={"component": "auth_router", "endpoint": "/login"}
        )
        return RedirectResponse(auth_url)
    except Exception as e:
        logger.error(
            "Errore durante la generazione dell'URL di login Microsoft",
            details={"error": str(e)},
            context={"component": "auth_router", "endpoint": "/login", "error_type": "auth_url_generation"},
            exc_info=True
        )
        error_redirect_url = f"{str(settings.FRONTEND_URL)}/login-error?error=backend_login_init_failed&description={quote(str(e))}"
        return RedirectResponse(error_redirect_url)

# Se il router è montato con prefix="/auth" in main.py,
# il frontend si aspetterà /auth/callback, quindi il path qui deve essere solo "/callback".
@router.get("/callback", tags=["Authentication"])

# --- NUOVO ENDPOINT PER REGISTRAZIONE UTENTE ---
@router.post("/register", tags=["Authentication"])
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Registra un nuovo utente con username, password, email e altre informazioni.
    """
    logger.info(
        "Ricevuta richiesta di registrazione",
        details={
            "username": user_data.username,
            "email": user_data.email
        },
        context={"component": "auth_router", "endpoint": "/register"}
    )
    
    try:
        # Usa il servizio utente per creare il nuovo utente
        user = user_service.create_user(db, user_data)
        logger.info(
            "Utente registrato con successo",
            details={
                "username": user.username,
                "user_id": user.user_id,
                "role": user.role
            },
            context={"component": "auth_router", "endpoint": "/register", "security_event": True}
        )
        
        # Dopo la registrazione, generiamo subito un token di accesso
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + access_token_expires
        to_encode = {
            "sub": user.username,
            "name": user.name or user.username,
            "role": user.role,
            "user_id": user.user_id,
            "exp": expire
        }
        
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        
        return {
            "status": "success",
            "message": "Utente registrato con successo",
            "access_token": encoded_jwt,
            "token_type": "bearer",
            "user": {
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "role": user.role
            }
        }
    except HTTPException as e:
        # Rilanciamo le eccezioni HTTP per preservare il codice di stato e il messaggio
        raise e
    except Exception as e:
        logger.error(
            "Errore durante la registrazione dell'utente",
            details={
                "username": user_data.username,
                "email": user_data.email,
                "error": str(e)
            },
            context={"component": "auth_router", "endpoint": "/register", "error_type": "registration_failed"},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la registrazione: {str(e)}"
        )
def callback_microsoft(request: Request, db: Session = Depends(get_db)): # Nome funzione aggiornato e aggiunta sessione DB
    code = request.query_params.get("code")
    state_from_request = request.query_params.get("state") # MSAL dovrebbe gestire la validazione dello state internamente se lo usi

    # Qui dovresti validare lo 'state' se lo hai salvato in sessione o cookie
    # per prevenire attacchi CSRF. Per semplicità, questo esempio lo omette,
    # ma MSAL potrebbe gestirlo.

    if not code:
        logger.warning(
            "Authorization code mancante nella risposta di callback Microsoft",
            details={"state": state_from_request},
            context={"component": "auth_router", "endpoint": "/callback", "security_event": True}
        )
        return RedirectResponse(f"{str(settings.FRONTEND_URL)}/login-error?error=missing_auth_code")

    msal_app = ConfidentialClientApplication(
        client_id=settings.CLIENT_ID,
        client_credential=settings.CLIENT_SECRET,
        authority=settings.AUTHORITY,
    )
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=settings.SCOPE,
        redirect_uri=str(settings.REDIRECT_URI)
    )

    if "id_token_claims" in result:
        logger.info(
            "Token Microsoft acquisito con successo",
            details={
                "has_id_token": True,
                "token_type": result.get("token_type", "unknown")
            },
            context={"component": "auth_router", "endpoint": "/callback", "auth_type": "microsoft"}
        )
        user_info = result["id_token_claims"]

        # Estrai informazioni utente dal token Microsoft
        name = user_info.get("name", "unknown")
        email = user_info.get("preferred_username")
        oid = user_info.get("oid") # Object ID da Azure AD, ottimo come user_id univoco
        
        # Assegna il ruolo basandosi sul dominio configurato
        role = "user" # Default a user
        if settings.ADMIN_EMAIL_DOMAIN and email and email.endswith(f"@{settings.ADMIN_EMAIL_DOMAIN}"):
            role = "admin"

        # Qui dovresti creare/aggiornare l'utente nel tuo DB locale
        # usando user_service.get_or_create_user_oauth o una funzione simile.
        # Questo assicura che l'utente esista nel tuo sistema e abbia un user_id locale.
        # Per ora, assumiamo che user_service possa gestire questo.
        # Esempio (da adattare al tuo user_service):
        user_info_for_db = {
            "preferred_username": email,
            "email": email,
            "name": name,
            "oid": oid,
            "role": role
        }
        db_user = user_service.get_or_create_user_oauth(db=db, user_info=user_info_for_db)
        if not db_user:
             logger.error(
                 "Impossibile creare o recuperare l'utente dal DB dopo il login OAuth",
                 details={"email": email, "name": name, "oid": oid},
                 context={"component": "auth_router", "endpoint": "/callback", "error_type": "user_db_sync_failed"}
             )
             return RedirectResponse(f"{str(settings.FRONTEND_URL)}/login-error?error=user_db_sync_failed")


        # Crea JWT personalizzato
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + access_token_expires
        payload = {
            "sub": db_user.username, # O email, o db_user.user_id se preferisci
            "name": db_user.name,
            "role": db_user.role,
            "user_id": db_user.user_id, # ID univoco dal tuo DB (che dovrebbe essere l'OID)
            "exp": expire
        }
        logger.info(
            "Utente Microsoft autenticato con successo",
            details={
                "email": email,
                "user_id": db_user.user_id,
                "role": db_user.role,
                "name": db_user.name,
                "token_expiry": expire.isoformat()
            },
            context={"component": "auth_router", "endpoint": "/callback", "auth_type": "microsoft", "security_event": True}
        )
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        # Redirect al frontend con token in querystring
        redirect_url = f"{str(settings.FRONTEND_URL)}?token={token}"
        return RedirectResponse(redirect_url)
    else:
        error_description = result.get("error_description", "Errore sconosciuto durante l'acquisizione del token Microsoft.")
        error_code = result.get("error", "unknown_microsoft_error")
        logger.error(
            "Fallimento nell'acquisire il token Microsoft",
            details={
                "error_code": error_code,
                "error_description": error_description,
                "result": {k: v for k, v in result.items() if k not in ["id_token_claims"]} # Esclude dati sensibili
            },
            context={"component": "auth_router", "endpoint": "/callback", "error_type": "microsoft_token_acquisition_failed"}
        )
        encoded_error_desc = quote(error_description)
        return RedirectResponse(f"{str(settings.FRONTEND_URL)}/login-error?error={quote(error_code)}&description={encoded_error_desc}")


