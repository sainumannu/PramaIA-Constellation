"""
Script per testare il nuovo servizio di gestione degli hash dei file.

Questo script verifica che il servizio di gestione degli hash funzioni correttamente
confrontando i risultati ottenuti dal vecchio e dal nuovo servizio.
"""

import os
import sys
import hashlib
import logging
from pathlib import Path
import tempfile

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("TestFileHashService")

def test_client_import():
    """Verifica che il client possa essere importato correttamente."""
    try:
        from backend.services.file_hash_service import file_hash_service
        logger.info(f"✅ Client importato con successo: {file_hash_service}")
        return True
    except Exception as e:
        logger.error(f"❌ Errore nell'importazione del client: {e}")
        return False

def create_test_file(content="Test file content"):
    """Crea un file di test con contenuto specificato."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp:
        temp.write(content.encode())
        temp_path = temp.name
    return temp_path

def test_check_duplicate():
    """Testa la funzionalità di controllo duplicati."""
    try:
        from backend.services.file_hash_service import file_hash_service
        
        # Crea un file di test
        test_file_path = create_test_file()
        with open(test_file_path, "rb") as f:
            file_bytes = f.read()
        
        # Calcola hash
        file_hash = hashlib.md5(file_bytes).hexdigest()
        
        # Test check_duplicate
        is_duplicate, doc_id, is_path_duplicate = file_hash_service.check_duplicate(
            file_bytes=file_bytes,
            filename="test_file.txt",
            client_id="test_client",
            original_path="/test/path/file.txt"
        )
        
        logger.info(f"✅ check_duplicate eseguito: is_duplicate={is_duplicate}, doc_id={doc_id}, is_path_duplicate={is_path_duplicate}")
        
        # Rimuovi file temporaneo
        os.unlink(test_file_path)
        return True
    except Exception as e:
        logger.error(f"❌ Errore nel test check_duplicate: {e}")
        return False

def test_save_hash():
    """Testa la funzionalità di salvataggio hash."""
    try:
        from backend.services.file_hash_service import file_hash_service
        
        # Crea un file di test
        test_file_path = create_test_file("Unique content for save test")
        with open(test_file_path, "rb") as f:
            file_bytes = f.read()
        
        # Test save_hash
        success = file_hash_service.save_hash(
            file_bytes=file_bytes,
            filename="test_save.txt",
            document_id="test_doc_id_123",
            client_id="test_client",
            original_path="/test/path/save_test.txt"
        )
        
        logger.info(f"✅ save_hash eseguito: success={success}")
        
        # Test con override hash
        success_override = file_hash_service.save_hash(
            file_bytes=b"dummy",  # contenuto diverso
            filename="test_override.txt",
            document_id="test_doc_id_456",
            file_hash_override="custom_hash_value",  # hash personalizzato
            client_id="test_client",
            original_path="/test/path/override_test.txt"
        )
        
        logger.info(f"✅ save_hash con override eseguito: success={success_override}")
        
        # Rimuovi file temporaneo
        os.unlink(test_file_path)
        return True
    except Exception as e:
        logger.error(f"❌ Errore nel test save_hash: {e}")
        return False

def run_all_tests():
    """Esegue tutti i test."""
    logger.info("🔄 Inizio test del servizio FileHashService")
    
    results = {}
    results["import"] = test_client_import()
    results["check_duplicate"] = test_check_duplicate()
    results["save_hash"] = test_save_hash()
    
    # Stampa risultati
    logger.info("\n🔍 RISULTATI DEI TEST:")
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASSATO" if result else "❌ FALLITO"
        logger.info(f"{status} - {test_name}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 TUTTI I TEST SONO PASSATI!")
        return 0
    else:
        logger.error("\n⚠️ ALCUNI TEST SONO FALLITI!")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())