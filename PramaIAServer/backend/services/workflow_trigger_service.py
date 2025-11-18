import json
from backend.utils import get_logger
import os
import re
from typing import Dict, List, Optional, Union

import requests
from fastapi import UploadFile

logger = get_logger()


def evaluate_trigger_conditions(trigger: Dict, file: UploadFile) -> bool:
    """
    Valuta le condizioni di un trigger per un file specifico.
    
    Args:
        trigger: Dizionario contenente i dettagli del trigger, incluse le condizioni
        file: File caricato da valutare contro le condizioni
        
    Returns:
        bool: True se tutte le condizioni sono soddisfatte, False altrimenti
    """
    try:
        conditions = trigger.get("conditions", {})
        if not conditions:
            # Se non ci sono condizioni, il trigger è sempre valido
            return True

        # Filtro per nome file
        if "filename_pattern" in conditions:
            pattern = conditions["filename_pattern"]
            if file.filename is None or not isinstance(file.filename, str) or not re.match(pattern, file.filename):
                logger.info("File non corrisponde al pattern", details={"file": getattr(file, 'filename', None), "pattern": pattern})
                return False

        # Filtro per dimensione file (massima)
        if "max_size_kb" in conditions:
            max_size = conditions["max_size_kb"] * 1024  # Converti KB in bytes
            if hasattr(file, 'size') and file.size > max_size:
                logger.info("File supera dimensione massima", details={"file": getattr(file, 'filename', None), "max_size": max_size, "size": getattr(file, 'size', None)})
                return False

        # Filtro per dimensione file (minima)
        if "min_size_kb" in conditions:
            min_size = conditions["min_size_kb"] * 1024  # Converti KB in bytes
            if hasattr(file, 'size') and file.size < min_size:
                logger.info("File sotto dimensione minima", details={"file": getattr(file, 'filename', None), "min_size": min_size, "size": getattr(file, 'size', None)})
                return False

        # Filtro per tipo di contenuto
        if "content_type" in conditions:
            content_type_pattern = conditions["content_type"]
            content_type = getattr(file, "content_type", None)
            if content_type is None or not isinstance(content_type, str) or not re.match(content_type_pattern, content_type):
                logger.info("Content type non corrisponde", details={"file": getattr(file, 'filename', None), "content_type": content_type, "pattern": content_type_pattern})
                return False

        # Controllo dei metadati
        if "metadata_contains" in conditions:
            metadata_requirements = conditions["metadata_contains"]
            file_metadata = getattr(file, "metadata", {})
            if not isinstance(file_metadata, dict):
                file_metadata = {}
            for key, value in metadata_requirements.items():
                if key not in file_metadata or file_metadata[key] != value:
                    logger.info("Metadato mancante", details={"file": getattr(file, 'filename', None), "key": key, "expected_value": value, "metadata": file_metadata})
                    return False

        # Tutte le condizioni sono soddisfatte
        return True
    except Exception as e:
        logger.error("Errore nella valutazione condizioni trigger", details={"error": str(e)})
        # In caso di errore, è più sicuro non eseguire il workflow
        return False


async def execute_workflow_for_trigger(trigger: Dict, file: UploadFile) -> Dict:
    """
    Esegue un workflow specifico per un trigger.
    
    Args:
        trigger: Dizionario contenente i dettagli del trigger
        file: File da elaborare con il workflow
        
    Returns:
        Dict: Risultato dell'esecuzione del workflow
    """
    try:
        workflow_id = trigger["workflow_id"]
        
        # Ottiene il file come bytes
        file_position = file.file.tell()
        file_bytes = await file.read()
        file.file.seek(file_position)  # Reimposta il puntatore per riletture successive
        
        # Prepara il payload per il PDK
        PDK_URL = os.getenv("PDK_SERVER_URL", f"http://localhost:{os.getenv('PDK_SERVER_PORT', '3001')}")
        
        # Determina l'endpoint in base al target_node_id
        target_node_id = trigger.get("target_node_id")
        if target_node_id:
            # Esecuzione mirata a un nodo specifico
            PDK_WORKFLOW_ENDPOINT = f"{PDK_URL}/api/workflows/{workflow_id}/execute-node/{target_node_id}"
            logger.info("Esecuzione mirata nodo", details={"target_node_id": target_node_id, "workflow_id": workflow_id})
        else:
            # Esecuzione standard del workflow completo
            PDK_WORKFLOW_ENDPOINT = f"{PDK_URL}/api/workflows/{workflow_id}/execute"
            logger.info("Esecuzione standard workflow", details={"workflow_id": workflow_id})
        
        # Prepara i metadati
        metadata = {
            "filename": file.filename,
            "source": trigger["source"],
            "trigger_id": trigger["id"],
            "trigger_name": trigger["name"],
            "event_type": trigger["event_type"],
            "target_node_id": target_node_id  # Aggiungi target_node_id ai metadati
        }
        
        # Aggiungi metadati personalizzati se disponibili
        file_metadata = getattr(file, "metadata", {})
        if isinstance(file_metadata, dict):
            metadata.update(file_metadata)
        
        # Esegui il workflow
        response = requests.post(
            PDK_WORKFLOW_ENDPOINT,
            files={"file": (file.filename, file_bytes, getattr(file, "content_type", "application/octet-stream"))},
            data={"metadata": json.dumps(metadata)},
            timeout=60
        )
        
        if response.status_code == 200:
            return {
                "status": "success",
                "workflow_id": workflow_id,
                "trigger_id": trigger["id"],
                "result": response.json()
            }
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            logger.error("Errore esecuzione workflow", details={"workflow_id": workflow_id, "error": error_msg})
            return {
                "status": "error",
                "workflow_id": workflow_id,
                "trigger_id": trigger["id"],
                "error": error_msg
            }
    except Exception as e:
        error_msg = str(e)
        logger.error("Eccezione esecuzione workflow", details={"workflow_id": trigger['workflow_id'], "error": error_msg})
        return {
            "status": "error",
            "workflow_id": trigger["workflow_id"],
            "trigger_id": trigger["id"],
            "error": error_msg
        }


def extract_document_id(result: Dict) -> Optional[str]:
    """
    Estrae il document_id dal risultato dell'esecuzione di un workflow.
    
    Args:
        result: Risultato dell'esecuzione del workflow
        
    Returns:
        Optional[str]: document_id se trovato, None altrimenti
    """
    try:
        # Prova a estrarre dal risultato di primo livello
        if "document_id" in result:
            return result["document_id"]
        
        # Prova a estrarre dal campo 'result' se presente
        if "result" in result and isinstance(result["result"], dict):
            if "document_id" in result["result"]:
                return result["result"]["document_id"]
            
            # Prova a estrarre dai dati di output se presenti
            if "output" in result["result"] and isinstance(result["result"]["output"], dict):
                if "document_id" in result["result"]["output"]:
                    return result["result"]["output"]["document_id"]
                
                # Prova a cercare in profondità nei dati di output
                if "data" in result["result"]["output"] and isinstance(result["result"]["output"]["data"], dict):
                    if "document_id" in result["result"]["output"]["data"]:
                        return result["result"]["output"]["data"]["document_id"]
        
        # Se non è stato trovato, restituisci None
        return None
    
    except Exception as e:
        logger.error("Errore estrazione document_id", details={"error": str(e)})
        return None
