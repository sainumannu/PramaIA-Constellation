from backend.db.database import Base, engine
from backend.db import models
from backend.db import workflow_models  # Import dei modelli workflow
from backend.db import group_models     # Import dei modelli gruppi
from backend.db import token_models     # Import dei modelli token

# Copia il database dalla vecchia posizione se esiste
import os
import shutil
from pathlib import Path

old_db_path = Path("backend/data/database.db")
new_db_path = Path("backend/db/database.db")

if old_db_path.exists() and not new_db_path.exists():
    print(f"🔄 Trovato database in posizione legacy. Migrazione in corso...")
    # Assicurati che la directory di destinazione esista
    os.makedirs(os.path.dirname(new_db_path), exist_ok=True)
    # Copia il database
    shutil.copy2(old_db_path, new_db_path)
    print(f"✅ Database migrato con successo da {old_db_path} a {new_db_path}")

print("📦 Creazione tabelle...")
Base.metadata.create_all(bind=engine)
print("✅ Database inizializzato con tabelle workflow, gruppi e token.")
