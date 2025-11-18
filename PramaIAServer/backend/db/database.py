"""
Database setup per PramaIAServer.
Definisce la connessione al database e fornisce oggetti di base per ORM.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Ottieni il percorso del database
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "database.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Crea l'engine con SQLAlchemy
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Necessario solo per SQLite
)

# Crea una factory per le sessioni
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe base per i modelli ORM
Base = declarative_base()

# Dependency per ottenere una sessione DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
