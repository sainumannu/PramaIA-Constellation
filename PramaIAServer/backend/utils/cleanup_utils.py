"""
Utility per la pulizia e manutenzione del database e degli eventi PDF.
Questo modulo contiene funzioni di cleanup e manutenzione per gestire
automaticamente gli eventi PDF e altri dati temporanei.
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from backend.core.config import PDF_EVENTS_MAX_AGE_HOURS, PDF_EVENTS_MAX_COUNT
from backend.utils import get_logger

logger = get_logger()

def cleanup_pdf_events(db_path: str, max_age_hours: int = PDF_EVENTS_MAX_AGE_HOURS, max_events: int = PDF_EVENTS_MAX_COUNT) -> Dict[str, Any]:
    """
    Pulisce automaticamente gli eventi PDF più vecchi di un certo periodo o in eccesso rispetto al limite massimo
    
    Args:
        db_path (str): Percorso del database
        max_age_hours (int): Età massima degli eventi in ore
        max_events (int): Numero massimo di eventi da mantenere
        
    Returns:
        dict: Statistiche del cleanup
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica se la tabella esiste
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pdf_monitor_events'")
        if not cursor.fetchone():
            conn.close()
            return {"success": False, "reason": "table_not_found"}
        
        # Conteggio iniziale
        cursor.execute("SELECT COUNT(*) FROM pdf_monitor_events")
        initial_count = cursor.fetchone()[0]
        
        # Timestamp minimo (eventi più vecchi di questo saranno eliminati)
        min_timestamp = (datetime.now() - timedelta(hours=max_age_hours)).strftime('%Y-%m-%dT%H:%M:%S')
        
        # 1. Prima eliminiamo per età
        cursor.execute(
            "DELETE FROM pdf_monitor_events WHERE timestamp < ?",
            (min_timestamp,)
        )
        deleted_by_age = cursor.rowcount
        
        # 2. Poi verifico quanti eventi rimangono
        cursor.execute("SELECT COUNT(*) FROM pdf_monitor_events")
        remaining_events = cursor.fetchone()[0]
        
        deleted_by_count = 0
        # 3. Se ci sono ancora troppi eventi, eliminiamo i più vecchi
        if remaining_events > max_events:
            # Troviamo il timestamp dell'evento N-esimo più recente
            cursor.execute(
                "SELECT timestamp FROM pdf_monitor_events ORDER BY timestamp DESC LIMIT 1 OFFSET ?", 
                (max_events,)
            )
            result = cursor.fetchone()
            if result:
                cutoff_timestamp = result[0]
                # Eliminiamo tutti gli eventi più vecchi di questo
                cursor.execute(
                    "DELETE FROM pdf_monitor_events WHERE timestamp <= ?",
                    (cutoff_timestamp,)
                )
                deleted_by_count = cursor.rowcount
        
        # Commit delle modifiche
        conn.commit()
        
        # Statistiche finali
        cursor.execute("SELECT COUNT(*) FROM pdf_monitor_events")
        final_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "success": True,
            "initial_count": initial_count,
            "deleted_by_age": deleted_by_age,
            "deleted_by_count": deleted_by_count,
            "final_count": final_count,
            "max_age_hours": max_age_hours,
            "max_events": max_events
        }
        
    except Exception as e:
        logger.error(
            "Errore durante cleanup eventi PDF",
            details={
                "error": str(e),
                "db_path": db_path,
                "max_age_hours": max_age_hours,
                "max_events": max_events
            },
            context={"component": "cleanup_utils", "action": "cleanup_pdf_events"},
            exc_info=True
        )
        return {"success": False, "error": str(e)}

def get_pdf_events_statistics(db_path: str) -> Dict[str, Any]:
    """
    Ottiene statistiche dettagliate sugli eventi PDF memorizzati nel database.
    
    Args:
        db_path (str): Percorso del database
        
    Returns:
        dict: Statistiche degli eventi PDF
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica se la tabella esiste
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pdf_monitor_events'")
        if not cursor.fetchone():
            conn.close()
            return {
                "success": False,
                "error": "Tabella pdf_monitor_events non trovata"
            }
        
        # Conteggio totale eventi
        cursor.execute("SELECT COUNT(*) FROM pdf_monitor_events")
        total_events = cursor.fetchone()[0]
        
        # Eventi per tipo di operazione
        cursor.execute("""
            SELECT operation, COUNT(*) as count 
            FROM pdf_monitor_events 
            GROUP BY operation 
            ORDER BY count DESC
        """)
        events_by_operation = cursor.fetchall()
        
        # Eventi recenti (ultimo giorno)
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S')
        cursor.execute("SELECT COUNT(*) FROM pdf_monitor_events WHERE timestamp > ?", (yesterday,))
        recent_events = cursor.fetchone()[0]
        
        # Evento più vecchio e più recente
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM pdf_monitor_events")
        oldest, newest = cursor.fetchone()
        
        # File PDF coinvolti
        cursor.execute("SELECT COUNT(DISTINCT file_path) FROM pdf_monitor_events")
        unique_files = cursor.fetchone()[0]
        
        # Errori recenti
        cursor.execute("""
            SELECT COUNT(*) FROM pdf_monitor_events 
            WHERE status = 'error' AND timestamp > ?
        """, (yesterday,))
        recent_errors = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "success": True,
            "statistics": {
                "total_events": total_events,
                "events_by_operation": [{"operation": op, "count": count} for op, count in events_by_operation],
                "recent_events_24h": recent_events,
                "recent_errors_24h": recent_errors,
                "unique_files": unique_files,
                "oldest_event": oldest,
                "newest_event": newest,
                "time_range_days": None if not oldest or not newest else (
                    datetime.fromisoformat(newest.replace('T', ' ')) - 
                    datetime.fromisoformat(oldest.replace('T', ' '))
                ).days
            }
        }
        
    except Exception as e:
        logger.error(
            "Errore nel recupero delle statistiche eventi PDF",
            details={"error": str(e), "db_path": db_path},
            context={"component": "cleanup_utils", "action": "get_pdf_events_statistics"},
            exc_info=True
        )
        return {
            "success": False,
            "error": str(e)
        }

def find_database_path() -> Optional[str]:
    """
    Trova il percorso corretto del database principale.
    
    Returns:
        str: Percorso del database se trovato, None altrimenti
    """
    possible_paths = [
        "backend/db/database.db",
        "backend/data/database.db", 
        "database.db",
        "data/database.db"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(
                "Database trovato",
                details={"path": path},
                context={"component": "cleanup_utils", "action": "find_database_path"}
            )
            return path
    
    logger.warning(
        "Database principale non trovato",
        details={"paths_checked": possible_paths},
        context={"component": "cleanup_utils", "action": "find_database_path"}
    )
    return None

def validate_database_structure(db_path: str) -> Dict[str, Any]:
    """
    Valida la struttura del database e verifica l'esistenza delle tabelle necessarie.
    
    Args:
        db_path (str): Percorso del database
        
    Returns:
        dict: Risultati della validazione
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Ottieni lista delle tabelle
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        validation_results = {
            "success": True,
            "database_path": db_path,
            "total_tables": len(tables),
            "tables": tables,
            "required_tables": {
                "pdf_monitor_events": "pdf_monitor_events" in tables,
                "users": "users" in tables,
                "workflows": "workflows" in tables if "workflows" in tables else False
            }
        }
        
        # Verifica schema tabella pdf_monitor_events se esiste
        if "pdf_monitor_events" in tables:
            cursor.execute("PRAGMA table_info(pdf_monitor_events)")
            columns = [{"name": col[1], "type": col[2], "nullable": not col[3]} for col in cursor.fetchall()]
            validation_results["pdf_monitor_events_schema"] = columns
        
        conn.close()
        
        return validation_results
        
    except Exception as e:
        logger.error(
            "Errore nella validazione del database",
            details={"error": str(e), "db_path": db_path},
            context={"component": "cleanup_utils", "action": "validate_database_structure"},
            exc_info=True
        )
        return {
            "success": False,
            "error": str(e),
            "database_path": db_path
        }

def cleanup_temporary_files(temp_directories: Optional[list[str]] = None) -> Dict[str, Any]:
    """
    Pulisce i file temporanei dalle directory specificate.
    
    Args:
        temp_directories (list): Lista di directory temporanee da pulire
        
    Returns:
        dict: Risultati del cleanup
    """
    if temp_directories is None:
        temp_directories = [
            "temp_files",
            "PramaIAServer/temp_files", 
            "temp",
            "c:/PramaIA/temp"
        ]
    
    cleanup_results = {
        "success": True,
        "directories_processed": 0,
        "files_deleted": 0,
        "total_size_freed": 0,
        "errors": []
    }
    
    for temp_dir in temp_directories:
        try:
            if not os.path.exists(temp_dir):
                continue
                
            cleanup_results["directories_processed"] += 1
            dir_files_deleted = 0
            dir_size_freed = 0
            
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                
                try:
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        
                        # Verifica se il file è più vecchio di 24 ore
                        file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if datetime.now() - file_modified > timedelta(hours=24):
                            os.remove(file_path)
                            dir_files_deleted += 1
                            dir_size_freed += file_size
                            
                except Exception as file_error:
                    cleanup_results["errors"].append(f"Errore con file {file_path}: {file_error}")
            
            cleanup_results["files_deleted"] += dir_files_deleted
            cleanup_results["total_size_freed"] += dir_size_freed
            
            logger.info(
                "Pulizia directory temporanea completata",
                details={
                    "dir_path": temp_dir,
                    "files_deleted": dir_files_deleted,
                    "bytes_freed": dir_size_freed
                },
                context={"component": "cleanup_utils", "action": "cleanup_temporary_files"}
            )
            
        except Exception as dir_error:
            cleanup_results["errors"].append(f"Errore con directory {temp_dir}: {dir_error}")
            logger.error(
                "Errore nel cleanup della directory temporanea",
                details={
                    "dir_path": temp_dir,
                    "error": str(dir_error)
                },
                context={"component": "cleanup_utils", "action": "cleanup_temporary_files"},
                exc_info=True
            )
    
    if cleanup_results["errors"]:
        cleanup_results["success"] = False
    
    return cleanup_results