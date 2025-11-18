# generate_hash.py
import logging
import sys # Per sys.exit

# --- Absolute first lines of executable code ---
print("--- SCRIPT generate_hash.py: INIZIO RAW PRINT ---") # Raw print

# Configure basic logging as early as possible
logging.basicConfig(
    level=logging.DEBUG, # Set to DEBUG to catch everything
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout) # Explicitly direct to stdout
    ]
)
# Get a logger for this module.
logger_script = logging.getLogger("generate_hash_script") # Use a specific name for this script's logger
logger_script.info("Logging configurato per generate_hash_script.")

# Now proceed with other imports and logic
from dotenv import load_dotenv, find_dotenv
from sqlalchemy.orm import Session

# The dotenv loading block
dotenv_path_found = find_dotenv(usecwd=True)
if dotenv_path_found:
    logger_script.info(f"Trovato file .env in: {dotenv_path_found}")
    load_dotenv(dotenv_path_found, override=True)
    logger_script.info("File .env caricato esplicitamente.")
else:
    logger_script.warning("File .env non trovato nella directory di lavoro corrente.")

# Importa i componenti necessari dal tuo backend
# Assicurati che i percorsi di importazione siano corretti rispetto alla posizione di questo script
try:
    from backend.db.database import SessionLocal
    from backend.db import models # Importa il modulo models che contiene la definizione di User
    from backend.security.password_utils import get_password_hash
    from backend.schemas.user_schemas import UserCreate # Per creare l'utente se non esiste
    # Modificato l'import da create_user_internal a create_user
    from backend.services.user_service import create_user # Per la logica di creazione utente
    from backend.core.config_auth import settings # Per leggere DEFAULT_ADMIN_USERNAME e DEFAULT_ADMIN_PASSWORD
except ImportError as e:
    logger_script.error(f"Errore durante l'importazione dei moduli: {e}", exc_info=True)
    print(f"Errore fatale durante l'importazione dei moduli: {e}")
    print("Assicurati di eseguire questo script dalla directory principale del progetto (PramaIA 2.0)")
    print("e che il tuo ambiente virtuale sia attivo.")
    sys.exit(1)

# Usa il logger specifico dello script o il logger del modulo __name__
# logger = logging.getLogger(__name__) # Non più necessario se usiamo logger_script ovunque

def update_admin_hash_in_db():
    """
    Legge la password dell'admin dalle impostazioni, genera il suo hash
    e aggiorna l'hash nel database per l'utente admin.
    Se l'utente admin non esiste, lo crea.
    """
    logger_script.debug("Entrato in update_admin_hash_in_db()")
    admin_username = settings.DEFAULT_ADMIN_USERNAME
    admin_password_from_env = settings.DEFAULT_ADMIN_PASSWORD

    if not admin_username or not admin_password_from_env:
        logger_script.error("DEFAULT_ADMIN_USERNAME o DEFAULT_ADMIN_PASSWORD non sono definiti o sono vuoti nelle impostazioni (.env).")
        return

    logger_script.info(f"Tentativo di aggiornare/creare l'utente admin: '{admin_username}'")
    logger_script.info(f"Password letta da .env (per hashing/creazione): '{admin_password_from_env}' (lunghezza: {len(admin_password_from_env)})")

    try:
        new_hashed_password = get_password_hash(admin_password_from_env)
        logger_script.info(f"Hash generato per la password: {new_hashed_password[:10]}... (lunghezza: {len(new_hashed_password)})")

        db: Session = SessionLocal()
        logger_script.debug("Sessione DB creata.")
        try:
            admin_user = db.query(models.User).filter(models.User.username == admin_username).first()

            if admin_user:
                logger_script.info(f"Utente admin '{admin_username}' trovato nel database. Aggiornamento hash password...")
                admin_user.hashed_password = new_hashed_password
                db.commit()
                logger_script.debug("Commit eseguito per aggiornamento password.")
                db.refresh(admin_user) # Opzionale, per aggiornare l'istanza admin_user con i dati dal DB
                logger_script.info(f"Hash della password per l'utente '{admin_username}' aggiornato con successo nel database.")
            else:
                logger_script.info(f"Utente admin '{admin_username}' NON trovato nel database. Tentativo di creazione...")
                # Prepara i dati per il nuovo utente admin
                admin_email = f"{admin_username.lower()}@example.com" # Email di default
                user_in = UserCreate(
                    username=admin_username,
                    email=admin_email,
                    password=admin_password_from_env, # Passa la password in chiaro, create_user la hasherà
                    name=admin_username.capitalize(), # Nome di default
                    role="admin", # Ruolo admin di default
                    is_active=True
                )
                # Modificata la chiamata da create_user_internal a create_user
                created_user = create_user(db=db, user_in=user_in)
                if created_user:
                    logger_script.info(f"Utente admin '{created_user.username}' creato con successo con ruolo '{created_user.role}'.")
                else:
                    logger_script.error(f"Fallimento durante la creazione dell'utente admin '{admin_username}'.")

        finally:
            db.close()
            logger_script.debug("Connessione al database chiusa.")

    except Exception as e:
        logger_script.error(f"Errore durante il processo di aggiornamento/creazione dell'hash: {e}", exc_info=True)
    logger_script.debug("Uscito da update_admin_hash_in_db()")

if __name__ == "__main__":
    logger_script.info("Blocco __main__ raggiunto. Esecuzione script per aggiornare/creare l'hash della password dell'admin nel DB...")
    # Istruzioni:
    # 1. Assicurati che il file .env contenga DEFAULT_ADMIN_USERNAME e DEFAULT_ADMIN_PASSWORD corretti.
    # 2. Attiva il tuo ambiente virtuale: .\venv\Scripts\activate
    # 3. Esegui questo script dalla directory principale del progetto usando:
    #    python -m backend.security.generate_hash
    update_admin_hash_in_db()
    logger_script.info("--- SCRIPT generate_hash.py: FINE ESECUZIONE ---")
