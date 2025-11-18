"""
Client per l'interazione con il servizio VectorstoreService per la gestione degli hash dei file.
"""

import os
import logging
import hashlib
import requests
from typing import Tuple, Optional, Dict, Any

# Configurazione logger
logger = logging.getLogger(__name__)

class FileHashServiceClient:
    """
    Client per il servizio di gestione degli hash nel VectorstoreService.
    
    Questa classe permette l'interazione con l'API di gestione hash del VectorstoreService
    per verificare duplicati e salvare nuovi hash.
    """
    
    def __init__(self, vectorstore_url=None):
        """
        Inizializza il client per l'API del servizio hash file.
        
        Args:
            vectorstore_url: URL base del VectorstoreService. Se None, viene utilizzato l'URL da variabili d'ambiente.
        """
        self.vectorstore_url = vectorstore_url or os.getenv("VECTORSTORE_URL", "http://localhost:8090")
        self.hash_api_url = f"{self.vectorstore_url}/api/file-hashes"
        self.api_key = os.getenv("VECTORSTORE_API_KEY", "dev_api_key")
        
        # Rimuovi il trailing slash se presente
        if self.hash_api_url.endswith("/"):
            self.hash_api_url = self.hash_api_url[:-1]
            
        logger.info(f"Inizializzato client FileHashService con endpoint: {self.hash_api_url}")
    
    def check_duplicate(self, file_bytes: bytes, filename: str, client_id: str = "system", 
                       original_path: str = "") -> Tuple[bool, Optional[str], bool]:
        """
        Verifica se un file è un duplicato basandosi sull'hash.
        
        Args:
            file_bytes: I byte del file da verificare
            filename: Il nome del file
            client_id: ID del client che ha inviato il file
            original_path: Percorso originale del file nel sistema del client
            
        Returns:
            Tuple (is_duplicate, document_id, is_path_duplicate)
        """
        try:
            # Calcola l'hash MD5 del file
            file_hash = hashlib.md5(file_bytes).hexdigest()
            
            # Prepara la richiesta
            url = f"{self.hash_api_url}/check-duplicate"
            payload = {
                "file_hash": file_hash,
                "filename": filename,
                "client_id": client_id,
                "original_path": original_path
            }
            headers = {"x-api-key": self.api_key}
            
            # Invia la richiesta
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                is_duplicate = result.get("is_duplicate", False)
                document_id = result.get("document_id")
                is_path_duplicate = result.get("is_path_duplicate", False)
                
                if is_duplicate:
                    logger.info(f"Duplicato rilevato per il file '{filename}': document_id={document_id}, is_path_duplicate={is_path_duplicate}")
                else:
                    logger.info(f"File '{filename}' non è un duplicato")
                
                return is_duplicate, document_id, is_path_duplicate
            else:
                logger.warning(f"Errore durante la verifica dei duplicati (status {response.status_code}): {response.text}")
                # Fallback: considera il file come non duplicato in caso di errore
                return False, None, False
                
        except Exception as e:
            logger.error(f"Errore durante la verifica dei duplicati per il file '{filename}': {e}")
            # Fallback: considera il file come non duplicato in caso di errore
            return False, None, False
    
    def save_hash(self, file_bytes: bytes, filename: str, document_id: str, client_id: str = "system",
                 original_path: str = "", file_hash_override: Optional[str] = None) -> bool:
        """
        Salva l'hash di un file nel servizio.
        
        Args:
            file_bytes: I byte del file da salvare
            filename: Il nome del file
            document_id: L'ID del documento nel sistema
            client_id: ID del client che ha inviato il file
            original_path: Percorso originale del file nel sistema del client
            file_hash_override: Se specificato, usa questo hash invece di calcolarlo dai bytes
            
        Returns:
            bool: True se il salvataggio è avvenuto con successo, False altrimenti
        """
        try:
            # Usa l'hash fornito o calcola l'hash MD5 del file
            if file_hash_override:
                file_hash = file_hash_override
            else:
                file_hash = hashlib.md5(file_bytes).hexdigest()
            
            # Prepara la richiesta
            url = f"{self.hash_api_url}/save"
            payload = {
                "file_hash": file_hash,
                "filename": filename,
                "document_id": document_id,
                "client_id": client_id,
                "original_path": original_path
            }
            headers = {"x-api-key": self.api_key}
            
            # Invia la richiesta
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 201:
                logger.info(f"Hash salvato con successo per il file '{filename}', document_id: {document_id}")
                return True
            else:
                logger.warning(f"Errore durante il salvataggio dell'hash (status {response.status_code}): {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Errore durante il salvataggio dell'hash per il file '{filename}': {e}")
            return False
            
# Istanza condivisa del client
file_hash_service = FileHashServiceClient()