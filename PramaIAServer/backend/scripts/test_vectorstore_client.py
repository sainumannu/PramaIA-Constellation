"""
Script di test per il client VectorstoreService.
"""
import os
import sys
import logging
from datetime import datetime
import requests

# Aggiungi la directory principale del progetto al percorso di ricerca dei moduli
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vectorstore_test")

# Importa il client
from backend.app.clients.vectorstore_client import VectorstoreServiceClient

def test_connection():
    """Testa la connessione al servizio"""
    logger.info("=== Test di connessione al VectorstoreService ===")
    
    # Test con diversi URL
    urls = [
        None,  # Default
        "http://localhost:8090",
        "http://localhost:8091",  # URL sbagliato
        "http://invalid-host:8090",  # Host invalido
    ]
    
    results = []
    
    for url in urls:
        url_str = url or "default (http://localhost:8090)"
        logger.info(f"Test connessione con URL: {url_str}")
        
        try:
            # Usa un timeout ridotto per il test
            client = VectorstoreServiceClient(base_url=url, timeout=2)
            health = client._request("GET", "/health")
            logger.info(f"✅ Connessione riuscita! Risposta: {health}")
            results.append(f"URL: {url_str} - OK - {health}")
        except Exception as e:
            logger.error(f"❌ Connessione fallita: {e}")
            results.append(f"URL: {url_str} - FALLITO - {str(e)}")
    
    return results

def test_endpoints():
    """Testa gli endpoint principali"""
    logger.info("=== Test degli endpoint del VectorstoreService ===")
    
    try:
        client = VectorstoreServiceClient()
        
        # Test dell'endpoint documenti
        logger.info("Test endpoint documents")
        try:
            docs = client.get_vectorstore_documents()
            logger.info(f"✅ Endpoint documents OK: trovati {len(docs.get('documents', []))} documenti")
        except Exception as e:
            logger.error(f"❌ Endpoint documents fallito: {e}")
        
        # Test dell'endpoint statistiche
        logger.info("Test endpoint statistics")
        try:
            stats = client.get_vectorstore_statistics()
            logger.info(f"✅ Endpoint statistics OK: {stats}")
        except Exception as e:
            logger.error(f"❌ Endpoint statistics fallito: {e}")
        
        # Test dell'endpoint impostazioni
        logger.info("Test endpoint settings")
        try:
            settings = client.get_settings()
            logger.info(f"✅ Endpoint settings OK: {settings}")
        except Exception as e:
            logger.error(f"❌ Endpoint settings fallito: {e}")
        
        return "Test endpoint completati"
    except Exception as e:
        logger.error(f"Errore generale nei test: {e}")
        return f"Test falliti: {str(e)}"

def main():
    """Funzione principale"""
    logger.info("Avvio dei test per il client VectorstoreService")
    
    connection_results = test_connection()
    
    print("\n=== Risultati dei test di connessione ===")
    for result in connection_results:
        print(f"  {result}")
    
    endpoint_result = test_endpoints()
    print(f"\n=== Risultato dei test degli endpoint ===\n  {endpoint_result}")
    
if __name__ == "__main__":
    main()
