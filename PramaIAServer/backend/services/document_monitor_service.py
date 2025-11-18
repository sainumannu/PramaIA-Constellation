"""
Servizio per gestire l'elaborazione dei documenti, rilevamento duplicati e operazioni sul vectorstore.
Separa la logica di business dalla gestione delle richieste API.
"""

import os
import json
import tempfile
import uuid
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
import requests

# Configurazione logger unificato
from backend.utils import get_logger
logger = get_logger()

async def check_file_duplicate(file_bytes: bytes, filename: str, client_id: str = "system", original_path: str = "") -> tuple:
    """
    Verifica se un file è un duplicato basandosi sul contenuto.
    
    Args:
        file_bytes: I byte del contenuto del file
        filename: Il nome del file
        client_id: L'identificativo del client che ha inviato il file
        original_path: Il percorso originale del file nel sistema del client
        
    Returns:
        Tuple (is_duplicate, original_document_id, is_path_duplicate)
    """
    try:
        # Calcola l'hash MD5 del file
        file_hash = hashlib.md5(file_bytes).hexdigest()
        
        # Importa la configurazione
        from backend.core.config import DB_DIR
        
        # Usa il percorso definito in config.py
        db_path = os.path.join(DB_DIR, "database.db")

        try:
            # Verifica se la tabella file_hashes esiste e creala se necessario
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Crea la tabella se non esiste (ora file_hash + client_id + original_path sono chiave primaria)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_hashes (
                    file_hash TEXT,
                    file_name TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_path TEXT NOT NULL,
                    client_id TEXT DEFAULT 'system',
                    original_path TEXT DEFAULT '',
                    PRIMARY KEY (file_hash, client_id, original_path)
                )
            ''')
            conn.commit()

            # Verifica se la colonna file_path esiste nella tabella
            try:
                cursor.execute("PRAGMA table_info(file_hashes)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                # Verifica se le colonne client_id e original_path esistono nella tabella
                if 'file_path' not in column_names:
                    logger.info(
                        "Aggiunta colonna mancante alla tabella file_hashes",
                        details={"column_name": "file_path", "table": "file_hashes", "action": "add_column"},
                        context={"component": "document_monitor_service", "database": db_path}
                    )
                    cursor.execute("ALTER TABLE file_hashes ADD COLUMN file_path TEXT DEFAULT ''")
                    conn.commit()
                    logger.info(
                        "Colonna aggiunta con successo",
                        details={"column_name": "file_path", "table": "file_hashes"},
                        context={"component": "document_monitor_service", "database": db_path}
                    )
                
                # Aggiungi la colonna client_id se non esiste
                if 'client_id' not in column_names:
                    logger.info(
                        "Aggiunta colonna mancante alla tabella file_hashes",
                        details={"column_name": "client_id", "table": "file_hashes", "action": "add_column"},
                        context={"component": "document_monitor_service", "database": db_path}
                    )
                    cursor.execute("ALTER TABLE file_hashes ADD COLUMN client_id TEXT DEFAULT 'system'")
                    conn.commit()
                    logger.info(
                        "Colonna aggiunta con successo",
                        details={"column_name": "client_id", "table": "file_hashes"},
                        context={"component": "document_monitor_service", "database": db_path}
                    )
                
                # Aggiungi la colonna original_path se non esiste
                if 'original_path' not in column_names:
                    logger.info(
                        "Aggiunta colonna mancante alla tabella file_hashes",
                        details={"column_name": "original_path", "table": "file_hashes", "action": "add_column"},
                        context={"component": "document_monitor_service", "database": db_path}
                    )
                    cursor.execute("ALTER TABLE file_hashes ADD COLUMN original_path TEXT DEFAULT ''")
                    conn.commit()
                    logger.info(
                        "Colonna aggiunta con successo",
                        details={"column_name": "original_path", "table": "file_hashes"},
                        context={"component": "document_monitor_service", "database": db_path}
                    )
            except Exception as column_error:
                logger.error(
                    "Errore durante la verifica o aggiunta delle colonne",
                    details={"error": str(column_error), "table": "file_hashes"},
                    context={"component": "document_monitor_service", "database": db_path},
                    exc_info=True
                )

            # Cerca prima il file con lo stesso hash, client_id e percorso originale (duplicato esatto)
            try:
                cursor.execute(
                    "SELECT document_id FROM file_hashes WHERE file_hash = ? AND client_id = ? AND original_path = ?", 
                    (file_hash, client_id, original_path)
                )
                result = cursor.fetchone()
                
                if result:
                    # Duplicato esatto trovato (stesso hash, stesso client, stesso percorso)
                    document_id = result[0]
                    logger.lifecycle(
                        "Duplicato esatto rilevato durante il caricamento",
                        details={
                            "lifecycle_event": "DOCUMENT_DUPLICATE",
                            "file_name": filename,
                            "file_hash": file_hash,
                            "document_id": document_id,
                            "client_id": client_id,
                            "original_path": original_path,
                            "duplicate_type": "exact",
                            "status": "blocked"
                        },
                        context={"component": "document_monitor_service", "action": "check_duplicate"}
                    )
                    conn.close()
                    return True, document_id, True
                
                # Se non è un duplicato esatto, cerca un duplicato di contenuto (stesso hash, client diverso o percorso diverso)
                cursor.execute(
                    "SELECT document_id FROM file_hashes WHERE file_hash = ? LIMIT 1", 
                    (file_hash,)
                )
                result = cursor.fetchone()
                
                if result:
                    # Duplicato di contenuto trovato
                    document_id = result[0]
                    logger.lifecycle(
                        "Duplicato di contenuto rilevato durante il caricamento",
                        details={
                            "lifecycle_event": "DOCUMENT_DUPLICATE",
                            "file_name": filename,
                            "file_hash": file_hash,
                            "document_id": document_id,
                            "client_id": client_id,
                            "original_path": original_path,
                            "duplicate_type": "content",
                            "status": "tracked"
                        },
                        context={"component": "document_monitor_service", "action": "check_duplicate"}
                    )
                    conn.close()
                    return True, document_id, False
                
            except sqlite3.OperationalError as op_error:
                # Gestione per retrocompatibilità
                if "no such column: client_id" in str(op_error) or "no such column: original_path" in str(op_error):
                    logger.warning("Usando query alternativa senza client_id/original_path per la retrocompatibilità")
                    cursor.execute("SELECT document_id FROM file_hashes WHERE file_hash = ? LIMIT 1", (file_hash,))
                    result = cursor.fetchone()
                    
                    if result:
                        document_id = result[0]
                        logger.info(f"Duplicato rilevato per il file '{filename}' (query legacy), document_id: {document_id}")
                        conn.close()
                        return True, document_id, False
                else:
                    raise

            logger.info(f"DEBUG DUPLICATO: File '{filename}' non è un duplicato, hash={file_hash}")
            conn.close()
            return False, None, False

        except Exception as db_error:
            logger.error(f"Errore durante il controllo dei duplicati nel database: {db_error}")
            return False, None
            
    except Exception as e:
        logger.error(f"Errore durante il controllo dei duplicati per il file '{filename}': {e}")
        return False, None

def save_file_hash(file_hash: str, filename: str, document_id: str, client_id: str = "system", original_path: str = ""):
    """
    Salva l'hash di un file nel database.
    
    Args:
        file_hash: L'hash MD5 del file
        filename: Il nome del file
        document_id: L'ID del documento nel sistema
        client_id: L'identificativo del client che ha inviato il file
        original_path: Il percorso originale del file nel sistema del client
        
    Returns:
        bool: True se il salvataggio è avvenuto con successo, False altrimenti
    """
    try:
        # Importa la configurazione
        from backend.core.config import DB_DIR
        
        # Usa il percorso definito in config.py
        db_path = os.path.join(DB_DIR, "database.db")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # Verifica se la colonna file_path esiste nella tabella
            cursor.execute("PRAGMA table_info(file_hashes)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Se non esiste la colonna file_path, aggiungiamola
            if 'file_path' not in column_names:
                logger.info("La colonna file_path non esiste nella tabella file_hashes. Aggiungendola...")
                cursor.execute("ALTER TABLE file_hashes ADD COLUMN file_path TEXT DEFAULT ''")
                conn.commit()
                logger.info("Colonna file_path aggiunta con successo")
                
            # Controlla se la combinazione di hash, client_id e original_path è già presente
            try:
                cursor.execute(
                    "SELECT 1 FROM file_hashes WHERE file_hash = ? AND client_id = ? AND original_path = ?", 
                    (file_hash, client_id, original_path)
                )
                if cursor.fetchone():
                    logger.info(f"Combinazione hash/client/path già presente per il file '{filename}', document_id: {document_id}. Nessun salvataggio effettuato.")
                    conn.close()
                    return False

                # Inserisci i dati con client_id e original_path
                try:
                    cursor.execute(
                        "INSERT INTO file_hashes (file_hash, file_name, document_id, file_path, client_id, original_path) VALUES (?, ?, ?, ?, ?, ?)",
                        (file_hash, filename, document_id, filename, client_id, original_path)
                    )
                except sqlite3.OperationalError as op_error:
                    # Gestione retrocompatibilità se le colonne non esistono ancora
                    if "no such column: client_id" in str(op_error) or "no such column: original_path" in str(op_error):
                        logger.warning("Usando query di inserimento senza client_id e original_path per la retrocompatibilità")
                        try:
                            cursor.execute(
                                "INSERT INTO file_hashes (file_hash, file_name, document_id, file_path) VALUES (?, ?, ?, ?)",
                                (file_hash, filename, document_id, filename)
                            )
                        except sqlite3.OperationalError as inner_error:
                            if "no such column: file_path" in str(inner_error):
                                logger.warning("Usando query di inserimento senza file_path per la retrocompatibilità")
                                cursor.execute(
                                    "INSERT INTO file_hashes (file_hash, file_name, document_id) VALUES (?, ?, ?)",
                                    (file_hash, filename, document_id)
                                )
                            else:
                                raise
                    else:
                        raise
                
                conn.commit()
                conn.close()
                logger.info(f"Hash salvato per il file '{filename}', document_id: {document_id}, client_id: {client_id}, path: {original_path}")
                return True
            except sqlite3.OperationalError as op_error:
                # Gestione della retrocompatibilità per query di selezione
                if "no such column: client_id" in str(op_error) or "no such column: original_path" in str(op_error):
                    logger.warning("Usando query di selezione senza client_id e original_path per la retrocompatibilità")
                    try:
                        cursor.execute("SELECT 1 FROM file_hashes WHERE file_hash = ? AND file_path = ?", (file_hash, filename))
                    except sqlite3.OperationalError as inner_error:
                        if "no such column: file_path" in str(inner_error):
                            logger.warning("Usando query alternativa senza file_path per la retrocompatibilità")
                            cursor.execute("SELECT 1 FROM file_hashes WHERE file_hash = ?", (file_hash,))
                        else:
                            raise
                        
                    if cursor.fetchone():
                        logger.info(f"Hash già presente per il file '{filename}', document_id: {document_id}. Nessun salvataggio effettuato.")
                        conn.close()
                        return False
                    
                    # Tentativo di inserimento con schema vecchio
                    try:
                        cursor.execute(
                            "INSERT INTO file_hashes (file_hash, file_name, document_id, file_path) VALUES (?, ?, ?, ?)",
                            (file_hash, filename, document_id, filename)
                        )
                    except sqlite3.OperationalError as inner_error:
                        if "no such column: file_path" in str(inner_error):
                            logger.warning("Usando query di inserimento senza file_path per la retrocompatibilità")
                            cursor.execute(
                                "INSERT INTO file_hashes (file_hash, file_name, document_id) VALUES (?, ?, ?)",
                                (file_hash, filename, document_id)
                            )
                        else:
                            raise
                    
                    conn.commit()
                    conn.close()
                    logger.info(f"Hash salvato per il file '{filename}', document_id: {document_id} (schema vecchio)")
                    return True
                else:
                    logger.error(f"Errore durante l'operazione sul database: {op_error}")
                    conn.close()
                    raise
        except Exception as e:
            logger.error(f"Errore durante il salvataggio dell'hash: {e}")
            return False
    except Exception as e:
        logger.error(f"Errore durante il salvataggio dell'hash: {e}")
        return False

async def process_document_with_pdk(file_bytes: bytes, filename: str, client_id: str = "system", original_path: str = ""):
    """
    Elabora un documento utilizzando il PDK e il plugin document-semantic-complete.
    
    Args:
        file_bytes: I byte del documento
        filename: Il nome del file
        client_id: L'identificativo del client che ha inviato il file
        original_path: Il percorso originale del file nel sistema del client
        
    Returns:
        dict: Risultato dell'elaborazione con document_id e stato
    """
    try:
        logger.lifecycle(
            "Inizio elaborazione documento",
            details={
                "lifecycle_event": "DOCUMENT_PROCESSING",
                "file_name": filename,
                "file_size": len(file_bytes),
                "client_id": client_id,
                "original_path": original_path,
                "status": "processing"
            },
            context={"component": "document_monitor_service", "action": "process_document"}
        )
        
        # Configurazione PDK
        PDK_PORT = int(os.getenv("PDK_SERVER_PORT", "3001"))
        PDK_URL = os.getenv("PDK_SERVER_URL", f"http://localhost:{PDK_PORT}")
        
        # Usa il nodo di input del plugin document-semantic-complete
        PLUGIN_ID = "document-semantic-complete-plugin"
        NODE_ID = "document_input_node"
        PDK_ENDPOINT = f"{PDK_URL}/plugins/{PLUGIN_ID}/execute"
        
        # Log dettagliato per debug
        logger.debug(
            "Configurazione PDK per l'elaborazione",
            details={
                "pdk_url": PDK_URL,
                "endpoint": PDK_ENDPOINT,
                "plugin_id": PLUGIN_ID,
                "node_id": NODE_ID,
                "file_name": filename
            },
            context={"component": "document_monitor_service", "action": "process_document"}
        )
        
        # Verifica se il file è un duplicato
        is_duplicate, original_document_id, is_path_duplicate = await check_file_duplicate(file_bytes, filename, client_id, original_path)
        logger.debug(f"[PDK_VECTORSTORE_DEBUG] Risultato controllo duplicati: {is_duplicate}, document_id originale: {original_document_id or 'N/A'}, is_path_duplicate: {is_path_duplicate}")

        # Salva temporaneamente il file per fornire un file_path al nodo
        # Crea una directory temporanea se non esiste
        temp_dir = os.path.join(os.getcwd(), "temp_files")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Genera un nome di file univoco
        temp_filename = f"{uuid.uuid4()}_{filename}"
        temp_filepath = os.path.join(temp_dir, temp_filename)
        
        # Salva il file
        with open(temp_filepath, "wb") as f:
            f.write(file_bytes)
            
        logger.debug(f"[PDK_VECTORSTORE_DEBUG] File temporaneo salvato in: {temp_filepath}")

        # Prepara i dati per il nodo Document Input
        # Il nodo document_input_node del plugin document-semantic-complete-plugin richiede:
        # - nodeId: ID del nodo da eseguire
        # - inputs: oggetto vuoto (il nodo prende input dal file)
        # - config: opzioni di configurazione per il nodo
        
        # Normalizza il percorso del file per evitare problemi di escape
        normalized_path = os.path.normpath(temp_filepath)
        
        # Includi informazioni sul client e sul percorso originale nei metadati
        payload = {
            "nodeId": NODE_ID,
            "inputs": {},
            "config": {
                "file_path": normalized_path.replace("\\", "/"),
                "extract_text": True,
                "extract_images": False,
                "pages": "all",
                "metadata": {
                    "source": "document-monitor-plugin",
                    "user_id": client_id,  # Usa il client_id fornito
                    "filename": filename,
                    "original_path": original_path,  # Includi il percorso originale
                    "upload_timestamp": datetime.now().isoformat()
                }
            }
        }
        
        # Per i file con JSON in multipart/form-data, dobbiamo convertire il payload in stringa
        # e inviarlo come parte del form
        # Usiamo ensure_ascii=False per evitare problemi con i caratteri non ASCII
        payload_str = json.dumps(payload, ensure_ascii=False)
        
        # Invia sia il file che il payload JSON come parti del form multipart
        # Determina il tipo MIME dal nome file
        import mimetypes
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = "application/octet-stream"
            
        files = {"file": (filename, file_bytes, mime_type)}
        form_data = {"json": payload_str}
        
        logger.debug(f"[PDK_VECTORSTORE_DEBUG] Invio richiesta PDK con payload: {payload}")
        
        # Registra l'inizio della chiamata al PDK
        pdk_request_start = datetime.now()
        resp = requests.post(PDK_ENDPOINT, files=files, data=form_data, timeout=60)
        pdk_request_end = datetime.now()
        pdk_duration = (pdk_request_end - pdk_request_start).total_seconds()
        
        logger.debug(f"[PDK_VECTORSTORE_DEBUG] Risposta PDK ricevuta in {pdk_duration:.2f} secondi - Status: {resp.status_code}")
        
        # Pulizia: rimuovi il file temporaneo
        try:
            os.remove(temp_filepath)
            logger.debug(f"[PDK_VECTORSTORE_DEBUG] File temporaneo rimosso: {temp_filepath}")
        except Exception as e:
            logger.warning(f"[PDK_VECTORSTORE_DEBUG] Impossibile rimuovere il file temporaneo {temp_filepath}: {e}")
        
        if resp.status_code != 200:
            logger.error(f"[PDK_VECTORSTORE_DEBUG] PDK non disponibile o workflow non trovato - Status code: {resp.status_code}")
            if resp.text:
                logger.error(f"[PDK_VECTORSTORE_DEBUG] Dettagli errore PDK: {resp.text[:500]}")
            
            return {
                "status": "error",
                "message": f"PDK non disponibile o workflow non trovato (status {resp.status_code})",
                "is_duplicate": False
            }
        
        # Processo la risposta
        result = resp.json()
        logger.debug(f"[PDK_VECTORSTORE_DEBUG] Risposta completa dal PDK: {json.dumps(result, indent=2)}")
        
        # Estraiamo l'ID del documento - potrebbe essere in posizioni diverse nella risposta
        document_id = None
        if 'result' in result and isinstance(result['result'], dict):
            # Cerca l'ID nelle possibili posizioni
            if 'id' in result['result']:
                document_id = result['result']['id']
            elif 'document_id' in result['result']:
                document_id = result['result']['document_id']
            elif 'output' in result['result'] and isinstance(result['result']['output'], dict):
                if 'id' in result['result']['output']:
                    document_id = result['result']['output']['id']
                elif 'document_id' in result['result']['output']:
                    document_id = result['result']['output']['document_id']
        
        # Log dettagliato sul document_id
        if document_id:
            logger.debug(f"[PDK_VECTORSTORE_DEBUG] Document ID estratto dalla risposta PDK: {document_id}")
        else:
            logger.warning(f"[PDK_VECTORSTORE_DEBUG] Nessun Document ID trovato nella risposta PDK!")
            
        logger.info(f"✅ Documento '{filename}' processato dal workflow PDK con successo. Document ID: {document_id or 'N/A'}")
        
        # Se il file non è un duplicato o è un duplicato di contenuto ma non di percorso, salva l'hash nel database
        if document_id and (not is_duplicate or (is_duplicate and not is_path_duplicate)):
            # Calcola l'hash per salvarlo
            file_hash = hashlib.md5(file_bytes).hexdigest()
            success = save_file_hash(file_hash, filename, document_id if not is_duplicate else original_document_id, client_id, original_path)
            logger.debug(f"[PDK_VECTORSTORE_DEBUG] Hash salvato nel database: {success}, hash={file_hash}, filename={filename}, document_id={document_id}, client_id={client_id}")
        
        # Se è un duplicato, usa il document_id dell'originale
        if is_duplicate:
            document_id = original_document_id
            logger.debug(f"[PDK_VECTORSTORE_DEBUG] Invio risposta con status=duplicate per '{filename}'")
            
            # Distingui tra duplicato esatto e duplicato di contenuto
            duplicate_type = "exact_duplicate" if is_path_duplicate else "content_duplicate"
            logger.warning(f"DUPLICATO RILEVATO: File '{filename}' è un {duplicate_type}! Document ID originale: {document_id}")
            
            # Invia una risposta più esplicita per i duplicati
            duplicate_response = {
                "status": "duplicate",
                "message": f"Il documento '{filename}' è un duplicato di un file esistente.",
                "document_id": document_id,
                "is_duplicate": True,
                "duplicate_type": duplicate_type,
                "duplicate_detection_method": "md5_hash",
                "client_id": client_id,
                "original_path": original_path
            }
            
            logger.debug(f"[PDK_VECTORSTORE_DEBUG] Risposta per duplicato: {duplicate_response}")
            return duplicate_response
        
        # Verifica post-elaborazione se il documento è stato inserito nel vectorstore
        try:
            from backend.core.rag_vectorstore import get_vectorstore_status
            vectorstore_status = get_vectorstore_status()
            logger.debug(f"[PDK_VECTORSTORE_DEBUG] Stato vectorstore dopo elaborazione: {vectorstore_status}")
        except Exception as vs_error:
            logger.error(f"[PDK_VECTORSTORE_DEBUG] Errore verifica stato vectorstore: {vs_error}")
        
        logger.debug(f"[PDK_VECTORSTORE_DEBUG] Elaborazione documento completata con successo - Documento: '{filename}', Document ID: {document_id}, Client: {client_id}")
        
        return {
            "status": "success", 
            "message": f"Documento '{filename}' ricevuto e processato dal workflow PDK.", 
            "document_id": document_id,
            "workflow_result": result,
            "is_duplicate": False,
            "client_id": client_id,
            "original_path": original_path
        }
        
    except Exception as e:
        logger.lifecycle(
            "Errore durante l'elaborazione del documento",
            details={
                "lifecycle_event": "DOCUMENT_ERROR",
                "file_name": filename,
                "client_id": client_id,
                "original_path": original_path,
                "error": str(e),
                "status": "error"
            },
            context={"component": "document_monitor_service", "action": "process_document"},
            exc_info=True
        )
        return {
            "status": "error",
            "message": f"Errore durante l'elaborazione del documento: {str(e)}",
            "is_duplicate": False,
            "client_id": client_id,
            "original_path": original_path
        }

async def query_document_semantic_search(query: str, top_k: int = 3, client_id: str = "system"):
    """
    Esegue una query semantica sui documenti indicizzati.
    
    Args:
        query: La query testuale da cercare
        top_k: Numero di risultati da restituire
        client_id: ID del client che esegue la query
        
    Returns:
        dict: Risultati della ricerca
    """
    try:
        PDK_PORT = int(os.getenv("PDK_SERVER_PORT", "3001"))
        PDK_URL = os.getenv("PDK_SERVER_URL", f"http://localhost:{PDK_PORT}")
        
        # Usa il nodo di query del plugin document-semantic-complete
        PLUGIN_ID = "document-semantic-complete-plugin"
        NODE_ID = "query_input_node"
        PDK_ENDPOINT = f"{PDK_URL}/plugins/{PLUGIN_ID}/execute"

        logger.info(
            "Esecuzione query semantica",
            details={
                "query": query,
                "top_k": top_k,
                "client_id": client_id,
                "plugin_id": PLUGIN_ID,
                "node_id": NODE_ID
            },
            context={"component": "document_monitor_service", "action": "semantic_search"}
        )
        
        # Prepara i dati per il nodo di query
        data = {
            "nodeId": NODE_ID,
            "inputs": {},
            "config": {
                "default_query": query,
                "top_k": top_k,
                "user_id": client_id
            }
        }
        
        resp = requests.post(PDK_ENDPOINT, json=data, timeout=30)
        
        if resp.status_code != 200:
            logger.error(
                "Query semantica fallita",
                details={
                    "status_code": resp.status_code,
                    "query": query,
                    "client_id": client_id,
                    "response_text": resp.text[:300] if resp.text else None
                },
                context={"component": "document_monitor_service", "action": "semantic_search", "error_type": "pdk_query_failed"}
            )
            return {
                "status": "error",
                "message": f"PDK query fallita (status {resp.status_code})",
                "query": query,
                "client_id": client_id
            }
        
        result = resp.json()
        results_count = len(result.get('documents', []))
        logger.info(
            "Query semantica completata",
            details={
                "query": query,
                "results_count": results_count,
                "client_id": client_id
            },
            context={"component": "document_monitor_service", "action": "semantic_search"}
        )
        
        return {
            "status": "success",
            "query": query,
            "results": result,
            "client_id": client_id
        }
        
    except Exception as e:
        logger.error(
            "Errore durante l'interrogazione semantica",
            details={
                "error": str(e),
                "query": query,
                "client_id": client_id
            },
            context={"component": "document_monitor_service", "action": "semantic_search", "error_type": "query_exception"},
            exc_info=True
        )
        return {
            "status": "error",
            "message": f"Errore durante l'interrogazione semantica: {str(e)}",
            "query": query,
            "client_id": client_id
        }

def get_registered_files_count():
    """
    Conta il numero di file registrati nel database nella tabella file_hashes.
    
    Returns:
        int: Numero di file registrati nel database
    """
    try:
        # Trova il percorso del database
        db_path = os.path.join("backend", "db", "database.db")
        if not os.path.exists(db_path):
            db_path = os.path.join("backend", "data", "database.db")
        if not os.path.exists(db_path):
            db_path = os.path.join(".", "backend", "data", "database.db")
        if not os.path.exists(db_path):
            db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "database.db"))

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Conta il numero di file unici (per document_id)
        cursor.execute("SELECT COUNT(DISTINCT document_id) FROM file_hashes")
        count = cursor.fetchone()[0]
        
        # Conta anche il numero totale di record (inclusi duplicati di contenuto)
        cursor.execute("SELECT COUNT(*) FROM file_hashes")
        total_entries = cursor.fetchone()[0]
        
        conn.close()
        return {
            "unique_files": count,
            "total_entries": total_entries
        }
    except Exception as e:
        db_path_info = "percorso sconosciuto" # Valore di fallback sicuro
        logger.error(
            "Errore durante il conteggio dei file registrati",
            details={"error": str(e), "db_path_attempted": db_path_info},
            context={"component": "document_monitor_service", "action": "get_registered_files_count"},
            exc_info=True
        )
        return {"unique_files": 0, "total_entries": 0}

def get_vectorstore_status():
    """
    Ottiene lo stato attuale del vectorstore.
    
    Returns:
        dict: Informazioni sullo stato del vectorstore e file registrati
    """
    try:
        from backend.core.rag_vectorstore import get_vectorstore_status as core_get_status
        vectorstore_status = core_get_status()
        
        # Ottieni anche i conteggi dei file registrati
        registered_files = get_registered_files_count()
        
        # Combina le informazioni
        combined_status = {
            **vectorstore_status,
            "registered_files": registered_files
        }
        
        return combined_status
    except Exception as e:
        logger.error(
            "Errore nel recupero dello stato del vectorstore",
            details={"error": str(e)},
            context={"component": "document_monitor_service", "action": "get_vectorstore_status"},
            exc_info=True
        )
        return {"error": str(e)}

def _get_file_type_name(extension: str) -> str:
    """
    Converte l'estensione del file in un nome comprensibile.
    
    Args:
        extension: Estensione del file (.pdf, .txt, ecc.)
        
    Returns:
        str: Nome del tipo di file
    """
    type_map = {
        '.pdf': 'PDF',
        '.txt': 'testo',
        '.docx': 'Word',
        '.doc': 'Word',
        '.md': 'Markdown',
        '.xlsx': 'Excel',
        '.xls': 'Excel',
        '.pptx': 'PowerPoint',
        '.ppt': 'PowerPoint',
        '.jpg': 'immagine JPEG',
        '.jpeg': 'immagine JPEG',
        '.png': 'immagine PNG',
        '.gif': 'immagine GIF',
        '.py': 'Python',
        '.js': 'JavaScript',
        '.html': 'HTML',
        '.css': 'CSS',
        '.json': 'JSON'
    }
    return type_map.get(extension.lower(), extension.upper())
