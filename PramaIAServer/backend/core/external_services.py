"""
Configurazioni per la connessione ai servizi esterni.
"""

import os
from pathlib import Path

# Configurazione del servizio vectorstore
VECTORSTORE_URL = os.getenv("VECTORSTORE_URL", "http://localhost:8090")
VECTORSTORE_API_KEY = os.getenv("VECTORSTORE_API_KEY", "dev_api_key")