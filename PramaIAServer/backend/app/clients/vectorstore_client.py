"""
Client Python per il servizio VectorstoreService.
"""

import json
import os
import requests
import time
from typing import Dict, List, Any, Optional
import logging

class VectorstoreServiceClient:
    """
    Client per comunicare con il servizio VectorstoreService.
    Versione migliorata con gestione più robusta degli errori e retry automatici.
    """
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 10, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Inizializza il client.
        
        Args:
            base_url: URL base del servizio VectorstoreService
            timeout: Timeout per le richieste in secondi
            max_retries: Numero massimo di tentativi per le richieste
            retry_delay: Ritardo tra i tentativi in secondi
        """
        # Determina l'URL base con priorità: argomento -> variabile d'ambiente -> default
        default_url = "http://localhost:8090"
        env_url = os.getenv("VECTORSTORE_SERVICE_URL")
        
        if base_url:
            self.base_url = base_url.rstrip('/')
        elif env_url:
            self.base_url = env_url.rstrip('/')
        else:
            self.base_url = default_url
        
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger("vectorstore_client")
        
        self.logger.info(f"VectorstoreServiceClient inizializzato con URL: {self.base_url}")
        
        # Verifica connessione ma non sollevare eccezione se fallisce
        # per permettere l'inizializzazione anche se il servizio non è disponibile
        try:
            self._check_connection()
        except ConnectionError as e:
            self.logger.warning(f"Inizializzazione completata, ma il servizio VectorstoreService non è raggiungibile: {e}")
            # Non rilanciare l'eccezione per permettere l'inizializzazione
    
    def _check_connection(self) -> bool:
        """
        Verifica la connessione al servizio.
        
        Returns:
            True se la connessione è attiva, altrimenti solleva un'eccezione
        
        Raises:
            ConnectionError: Se non è possibile connettersi al servizio dopo tutti i tentativi
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(
                    f"{self.base_url}/health", 
                    timeout=self.timeout,
                    headers={"User-Agent": "VectorstoreServiceClient/1.1"}
                )
                response.raise_for_status()
                self.logger.info(f"Connessione a VectorstoreService stabilita: {self.base_url}")
                return True
            except requests.RequestException as e:
                self.logger.warning(
                    f"Tentativo {attempt}/{self.max_retries} fallito: {str(e)}"
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error(f"Impossibile connettersi al servizio VectorstoreService: {str(e)}")
                    raise ConnectionError(f"503: Servizio VectorstoreService non disponibile: {str(e)}")
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Esegue una richiesta HTTP al servizio con retry automatico.
        
        Args:
            method: Metodo HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint dell'API (senza base_url)
            data: Dati da inviare nel corpo della richiesta
            params: Parametri query string
            
        Returns:
            Risposta JSON dal servizio
            
        Raises:
            ConnectionError: Se non è possibile connettersi al servizio
            TimeoutError: Se la richiesta scade dopo tutti i tentativi
            requests.HTTPError: Se la richiesta fallisce dopo tutti i tentativi
            ValueError: Se il metodo HTTP non è supportato
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        self.logger.debug(f"Esecuzione richiesta {method} a {url}")
        
        # Headers di base
        headers = {
            "User-Agent": "VectorstoreServiceClient/1.1",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        for attempt in range(1, self.max_retries + 1):
            try:
                if method.upper() == "GET":
                    response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
                elif method.upper() == "POST":
                    response = requests.post(url, json=data, params=params, headers=headers, timeout=self.timeout)
                elif method.upper() == "PUT":
                    response = requests.put(url, json=data, params=params, headers=headers, timeout=self.timeout)
                elif method.upper() == "DELETE":
                    response = requests.delete(url, json=data, params=params, headers=headers, timeout=self.timeout)
                else:
                    raise ValueError(f"Metodo HTTP non supportato: {method}")
                
                # Log dettagliato in caso di errore
                if response.status_code >= 400:
                    self.logger.warning(
                        f"Richiesta fallita con status {response.status_code}: {url}\n"
                        f"Response: {response.text[:200]}..."
                    )
                
                response.raise_for_status()
                return response.json()
                
            except requests.RequestException as e:
                self.logger.warning(
                    f"Tentativo {attempt}/{self.max_retries} fallito per {url}: {str(e)}"
                )
                if attempt < self.max_retries:
                    # Backoff esponenziale con jitter
                    delay = self.retry_delay * (2 ** (attempt - 1)) * (0.9 + 0.2 * (time.time() % 1.0))
                    time.sleep(delay)
                else:
                    self.logger.error(f"Tutti i tentativi falliti per {url}: {str(e)}")
                    if isinstance(e, requests.ConnectionError):
                        raise ConnectionError(f"503: Servizio VectorstoreService non disponibile: {str(e)}")
                    elif isinstance(e, requests.Timeout):
                        raise TimeoutError(f"504: Timeout durante la connessione al VectorstoreService: {str(e)}")
                    else:
                        raise e
    
    # --- Metodi per le collezioni ---
    
    def list_collections(self) -> List[str]:
        """
        Elenca tutte le collezioni disponibili.
        
        Returns:
            Lista dei nomi delle collezioni
        """
        response = self._request("GET", "/collections")
        return response.get("collections", [])
    
    def create_collection(self, name: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Crea una nuova collezione.
        
        Args:
            name: Nome della collezione
            metadata: Metadati opzionali della collezione
            
        Returns:
            Informazioni sulla collezione creata
        """
        data = {
            "name": name,
            "metadata": metadata or {}
        }
        return self._request("POST", "/collections", data=data)
    
    def delete_collection(self, name: str) -> Dict:
        """
        Elimina una collezione.
        
        Args:
            name: Nome della collezione
            
        Returns:
            Esito dell'operazione
        """
        return self._request("DELETE", f"/collections/{name}")
    
    # --- Metodi per i documenti ---
    
    def list_documents(self, collection_name: str, limit: int = 100, offset: int = 0) -> Dict:
        """
        Elenca i documenti in una collezione.
        
        Args:
            collection_name: Nome della collezione
            limit: Numero massimo di documenti da restituire
            offset: Offset per la paginazione
            
        Returns:
            Documenti nella collezione
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        return self._request("GET", f"/documents/{collection_name}", params=params)
    
    def add_document(self, collection_name: str, document: Dict, metadata: Optional[Dict] = None) -> Dict:
        """
        Aggiunge un documento a una collezione.
        
        Args:
            collection_name: Nome della collezione
            document: Documento da aggiungere (deve contenere almeno il campo "text")
            metadata: Metadati opzionali del documento
            
        Returns:
            Esito dell'operazione
        """
        data = {
            "document": document,
            "metadata": metadata or {}
        }
        return self._request("POST", f"/documents/{collection_name}", data=data)
    
    def delete_document(self, collection_name: str, document_id: str) -> Dict:
        """
        Elimina un documento da una collezione.
        
        Args:
            collection_name: Nome della collezione
            document_id: ID del documento
            
        Returns:
            Esito dell'operazione
        """
        return self._request("DELETE", f"/documents/{collection_name}/{document_id}")
    
    def query(self, collection_name: str, query_text: str, top_k: int = 5, metadata_filter: Optional[Dict] = None) -> Dict:
        """
        Esegue una query in una collezione.
        
        Args:
            collection_name: Nome della collezione
            query_text: Testo della query
            top_k: Numero massimo di risultati
            metadata_filter: Filtro sui metadati
            
        Returns:
            Risultati della query
        """
        data = {
            "query_text": query_text,
            "top_k": top_k,
            "metadata_filter": metadata_filter or {}
        }
        return self._request("POST", f"/documents/{collection_name}/query", data=data)
    
    # --- Metodi per le statistiche ---
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Ottiene le statistiche generali del vectorstore.
        
        Returns:
            Statistiche del vectorstore
        """
        return self._request("GET", "/stats")
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Ottiene le statistiche di una collezione.
        
        Args:
            collection_name: Nome della collezione
            
        Returns:
            Statistiche della collezione
        """
        return self._request("GET", f"/stats/{collection_name}")
        
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Ottiene le statistiche di elaborazione documenti.
        
        Returns:
            Statistiche di elaborazione documenti
        """
        return self._request("GET", "/stats/processing")
    
    # --- Metodi per il frontend ---
    
    def get_vectorstore_documents(self) -> Dict[str, Any]:
        """
        Ottiene l'elenco dei documenti nel vectorstore in formato compatibile con il frontend.
        
        Returns:
            Documenti nel vectorstore formattati per il frontend
        """
        return self._request("GET", "/api/database-management/vectorstore/documents")
    
    def get_vectorstore_statistics(self) -> Dict[str, Any]:
        """
        Ottiene le statistiche del vectorstore in formato compatibile con il frontend.
        
        Returns:
            Statistiche formattate per il frontend
        """
        return self._request("GET", "/api/database-management/vectorstore/statistics")
    
    # --- Metodi per la riconciliazione ---
    
    def start_reconciliation(self, delete_missing: bool = False) -> Dict[str, Any]:
        """
        Avvia la riconciliazione tra filesystem e vectorstore.
        
        Args:
            delete_missing: Se True, elimina i documenti non più presenti nel filesystem
            
        Returns:
            Esito dell'operazione
        """
        data = {"delete_missing": delete_missing}
        return self._request("POST", "/reconciliation/start", data=data)
    
    def get_reconciliation_status(self) -> Dict[str, Any]:
        """
        Ottiene lo stato dell'ultima riconciliazione.
        
        Returns:
            Stato della riconciliazione
        """
        return self._request("GET", "/reconciliation/status")
        
    # --- Metodi per le impostazioni ---
    
    def get_settings(self) -> Dict[str, Any]:
        """
        Ottiene le impostazioni del vectorstore.
        
        Returns:
            Impostazioni del vectorstore
        """
        return self._request("GET", "/settings")
        
    def update_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggiorna le impostazioni del vectorstore.
        
        Args:
            settings: Nuove impostazioni
            
        Returns:
            Impostazioni aggiornate
        """
        return self._request("POST", "/settings", data=settings)
