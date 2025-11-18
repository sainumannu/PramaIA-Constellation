"""
Servizio di sincronizzazione automatica tra cartelle monitorate e vectorstore.
Mantiene aggiornato il vectorstore con i cambiamenti nella struttura delle cartelle.
"""

import os
import time
import logging
from typing import Dict, Set, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from watchdog.observers import Observer
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

class FolderVectorstoreSyncHandler(FileSystemEventHandler):
    """
    Handler per eventi del file system che sincronizza automaticamente
    le modifiche con il vectorstore.
    """
    
    def __init__(self, user_id: str = "system"):
        self.user_id = user_id
        self.last_sync = {}  # Cache per evitare sync troppo frequenti
        self.sync_delay = 2  # Secondi di ritardo per evitare eventi multipli
    
    def on_created(self, event):
        """File o cartella creata"""
        if not event.is_directory:
            logger.info(f"File creato: {event.src_path}")
            self._schedule_file_sync(str(event.src_path), "created")
        else:
            logger.info(f"Cartella creata: {event.src_path}")
            self._schedule_folder_sync(str(event.src_path), "created")
    
    def on_deleted(self, event):
        """File o cartella eliminata"""
        logger.info(f"{'Cartella' if event.is_directory else 'File'} eliminato: {event.src_path}")
        self._schedule_removal(str(event.src_path))
    
    def on_modified(self, event):
        """File o cartella modificata"""
        if not event.is_directory:
            logger.info(f"File modificato: {event.src_path}")
            self._schedule_file_sync(str(event.src_path), "modified")
    
    def on_moved(self, event):
        """File o cartella spostata/rinominata"""
        logger.info(f"{'Cartella' if event.is_directory else 'File'} spostato: {event.src_path} -> {event.dest_path}")
        self._schedule_removal(str(event.src_path))
        if not event.is_directory:
            self._schedule_file_sync(str(event.dest_path), "moved")
        else:
            self._schedule_folder_sync(str(event.dest_path), "moved")
    
    def _schedule_file_sync(self, file_path: str, action: str):
        """Programma la sincronizzazione di un file"""
        current_time = time.time()
        
        # Evita sync troppo frequenti dello stesso file
        if file_path in self.last_sync and (current_time - self.last_sync[file_path]) < self.sync_delay:
            return
        
        self.last_sync[file_path] = current_time
        
        # Programma sync asincrona (in un thread separato)
        import threading
        threading.Thread(
            target=self._sync_file_to_vectorstore,
            args=(file_path, action),
            daemon=True
        ).start()
    
    def _schedule_folder_sync(self, folder_path: str, action: str):
        """Programma la sincronizzazione di una cartella"""
        import threading
        threading.Thread(
            target=self._sync_folder_structure,
            args=(folder_path, action),
            daemon=True
        ).start()
    
    def _schedule_removal(self, path: str):
        """Programma la rimozione dal vectorstore"""
        import threading
        threading.Thread(
            target=self._remove_from_vectorstore,
            args=(path,),
            daemon=True
        ).start()
    
    def _sync_file_to_vectorstore(self, file_path: str, action: str):
        """Sincronizza un singolo file con il vectorstore"""
        try:
            logger.debug(f"[FOLDER_SYNC_DEBUG] Sincronizzazione file '{file_path}' - Azione: {action}")
            time.sleep(self.sync_delay)  # Aspetta per evitare eventi multipli
            
            if not os.path.exists(file_path):
                logger.warning(f"[FOLDER_SYNC_DEBUG] File {file_path} non esiste più, skip sync")
                return
            
            from backend.core.rag_vectorstore import add_documents_to_vectorstore, remove_documents_from_vectorstore
            from backend.core.rag_chains_prompts import get_openai_embeddings
            from langchain.docstore.document import Document
            
            filename = os.path.basename(file_path)
            relative_path = os.path.relpath(file_path)
            
            logger.debug(f"[FOLDER_SYNC_DEBUG] Inizio sincronizzazione file: '{filename}', path: '{relative_path}'")
            
            # Se è una modifica, rimuovi prima la versione precedente
            if action == "modified":
                logger.debug(f"[FOLDER_SYNC_DEBUG] Rimozione versione precedente dal vectorstore: '{relative_path}'")
                removal_result = remove_documents_from_vectorstore(relative_path)
                logger.debug(f"[FOLDER_SYNC_DEBUG] Risultato rimozione: {removal_result}")
            
            # Leggi e sincronizza il file
            file_content = ""
            file_type = "unknown"
            file_ext = Path(file_path).suffix.lower()
            
            logger.debug(f"[FOLDER_SYNC_DEBUG] Tipo file rilevato: '{file_ext}'")
            
            if file_ext in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv']:
                file_type = "text"
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                        logger.debug(f"[FOLDER_SYNC_DEBUG] Contenuto file letto (utf-8): {len(file_content)} caratteri")
                except:
                    try:
                        with open(file_path, 'r', encoding='latin-1') as f:
                            file_content = f.read()
                            logger.debug(f"[FOLDER_SYNC_DEBUG] Contenuto file letto (latin-1): {len(file_content)} caratteri")
                    except Exception as e:
                        logger.error(f"[FOLDER_SYNC_DEBUG] Errore lettura file {file_path}: {e}")
                        file_content = "[Contenuto non leggibile]"
            elif file_ext == '.pdf':
                file_type = "pdf"
                file_content = "[File PDF - contenuto da elaborare separatamente]"
                logger.debug(f"[FOLDER_SYNC_DEBUG] File PDF rilevato, utilizzo placeholder per contenuto")
            else:
                file_type = "binary"
                file_content = "[File binario]"
                logger.debug(f"[FOLDER_SYNC_DEBUG] File binario rilevato, utilizzo placeholder per contenuto")
            
            # Crea documento
            doc = Document(
                page_content=f"File: {filename}\nPercorso: {relative_path}\nTipo: {file_type}\nAzione: {action}\nTimestamp: {datetime.now().isoformat()}\n\nContenuto:\n{file_content[:2000]}{'...' if len(file_content) > 2000 else ''}",
                metadata={
                    "source_filename": relative_path,
                    "document_type": "file_content_auto",
                    "file_type": file_type,
                    "file_extension": file_ext,
                    "sync_action": action,
                    "user_id": self.user_id,
                    "full_path": file_path,
                    "file_size": os.path.getsize(file_path),
                    "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                }
            )
            
            logger.debug(f"[FOLDER_SYNC_DEBUG] Documento preparato per vectorstore: {doc.metadata}")
            
            embeddings_service = get_openai_embeddings()
            logger.debug(f"[FOLDER_SYNC_DEBUG] Embedding service inizializzato: {type(embeddings_service).__name__}")
            
            add_result = add_documents_to_vectorstore(
                docs=[doc],
                embeddings_service=embeddings_service,
                filename=relative_path
            )
            
            if add_result is True:
                logger.info(f"✅ File {relative_path} sincronizzato automaticamente ({action})")
                logger.debug(f"[FOLDER_SYNC_DEBUG] Sincronizzazione completata con successo")
            else:
                logger.warning(f"[FOLDER_SYNC_DEBUG] La sincronizzazione ha restituito: {add_result}")
            
        except Exception as e:
            logger.error(f"[FOLDER_SYNC_DEBUG] ❌ Errore sincronizzazione automatica file {file_path}: {e}", exc_info=True)
    
    def _sync_folder_structure(self, folder_path: str, action: str):
        """Sincronizza la struttura di una cartella con metadati dettagliati"""
        try:
            logger.debug(f"[FOLDER_SYNC_DEBUG] Sincronizzazione struttura cartella '{folder_path}' - Azione: {action}")
            time.sleep(self.sync_delay)
            
            if not os.path.exists(folder_path):
                logger.warning(f"[FOLDER_SYNC_DEBUG] Cartella {folder_path} non esiste più, skip sync")
                return
            
            from backend.core.rag_vectorstore import add_documents_to_vectorstore
            from backend.core.rag_chains_prompts import get_openai_embeddings
            from langchain.docstore.document import Document
            
            relative_path = os.path.relpath(folder_path)
            logger.debug(f"[FOLDER_SYNC_DEBUG] Sincronizzazione struttura cartella: '{relative_path}'")
            
            # Calcola statistiche dettagliate della cartella
            stats = self._calculate_detailed_folder_stats(folder_path)
            logger.debug(f"[FOLDER_SYNC_DEBUG] Statistiche cartella calcolate: {stats}")
            
            # Crea contenuto descrittivo per embeddings semantici
            content_parts = [
                f"Cartella '{os.path.basename(folder_path)}' nel percorso '{relative_path}'",
                f"contiene {stats['total_files']} file totali"
            ]
            
            if stats['file_types']:
                type_details = []
                for ext, count in stats['file_types'].items():
                    file_type_name = self._get_file_type_name(ext)
                    type_details.append(f"{count} file {file_type_name}")
                content_parts.append("composti da: " + ", ".join(type_details))
            
            if stats['subdirs']:
                content_parts.append(f"Ha {len(stats['subdirs'])} sottocartelle: {', '.join(stats['subdirs'])}")
            
            if stats['total_size'] > 0:
                size_mb = stats['total_size'] / (1024 * 1024)
                if size_mb > 1024:
                    size_str = f"{size_mb/1024:.1f} GB"
                else:
                    size_str = f"{size_mb:.1f} MB"
                content_parts.append(f"Dimensione totale: {size_str}")
            
            content_parts.append(f"Ultimo aggiornamento: {datetime.now().isoformat()}")
            
            page_content = ". ".join(content_parts) + "."
            logger.debug(f"[FOLDER_SYNC_DEBUG] Contenuto descrittivo creato: {page_content}")
            
            # Crea documento per la struttura con metadati ricchi
            doc = Document(
                page_content=page_content,
                metadata={
                    "source_filename": f"folder_metadata_{relative_path.replace(os.sep, '_')}",
                    "document_type": "directory_metadata",
                    "folder_path": relative_path,
                    "sync_action": action,
                    "user_id": self.user_id,
                    "full_path": folder_path,
                    "subdirs": stats['subdirs'],
                    "files": stats['files'],
                    "total_files": stats['total_files'],
                    "file_types": stats['file_types'],
                    "total_size": stats['total_size'],
                    "last_modified": stats.get('last_modified'),
                    "created_at": datetime.now().isoformat()
                }
            )
            
            logger.debug(f"[FOLDER_SYNC_DEBUG] Documento struttura cartella preparato con metadati: {doc.metadata}")
            
            embeddings_service = get_openai_embeddings()
            logger.debug(f"[FOLDER_SYNC_DEBUG] Embedding service inizializzato: {type(embeddings_service).__name__}")
            
            add_result = add_documents_to_vectorstore(
                docs=[doc],
                embeddings_service=embeddings_service,
                filename=f"folder_metadata_{relative_path.replace(os.sep, '_')}"
            )
            
            if add_result is True:
                logger.info(f"✅ Metadati cartella {relative_path} sincronizzati ({action})")
                logger.debug(f"[FOLDER_SYNC_DEBUG] Sincronizzazione metadati cartella completata con successo")
            else:
                logger.warning(f"[FOLDER_SYNC_DEBUG] La sincronizzazione metadati cartella ha restituito: {add_result}")
            
        except Exception as e:
            logger.error(f"[FOLDER_SYNC_DEBUG] ❌ Errore sincronizzazione automatica cartella {folder_path}: {e}", exc_info=True)
    
    def _calculate_detailed_folder_stats(self, folder_path: str) -> dict:
        """Calcola statistiche dettagliate di una cartella"""
        stats = {
            'subdirs': [],
            'files': [],
            'total_files': 0,
            'file_types': {},
            'total_size': 0,
            'last_modified': None
        }
        
        try:
            for item_name in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item_name)
                
                if os.path.isdir(item_path):
                    stats['subdirs'].append(item_name)
                elif os.path.isfile(item_path):
                    stats['files'].append(item_name)
                    stats['total_files'] += 1
                    
                    # Estensione file
                    ext = Path(item_path).suffix.lower()
                    if ext:
                        stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
                    
                    # Dimensione file
                    try:
                        size = os.path.getsize(item_path)
                        stats['total_size'] += size
                    except:
                        pass
                    
                    # Data modifica più recente
                    try:
                        mtime = os.path.getmtime(item_path)
                        mtime_iso = datetime.fromtimestamp(mtime).isoformat()
                        if stats['last_modified'] is None:
                            stats['last_modified'] = mtime_iso
                        else:
                            # Confronta timestamp numerici
                            current_timestamp = datetime.fromisoformat(stats['last_modified']).timestamp()
                            if mtime > current_timestamp:
                                stats['last_modified'] = mtime_iso
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"Errore calcolo statistiche cartella {folder_path}: {e}")
            
        return stats
    
    def _get_file_type_name(self, extension: str) -> str:
        """Converte estensione in nome comprensibile"""
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
    
    def _remove_from_vectorstore(self, path: str):
        """Rimuove un elemento dal vectorstore"""
        try:
            logger.debug(f"[FOLDER_SYNC_DEBUG] Rimozione elemento '{path}' dal vectorstore")
            time.sleep(self.sync_delay)
            
            from backend.core.rag_vectorstore import remove_documents_from_vectorstore
            
            relative_path = os.path.relpath(path)
            logger.debug(f"[FOLDER_SYNC_DEBUG] Rimozione elemento dal vectorstore: '{relative_path}'")
            
            # Rimuovi sia come file che come struttura cartella
            logger.debug(f"[FOLDER_SYNC_DEBUG] Tentativo rimozione come file: '{relative_path}'")
            success1 = remove_documents_from_vectorstore(relative_path)
            
            folder_metadata_name = f"folder_metadata_{relative_path.replace(os.sep, '_')}"
            logger.debug(f"[FOLDER_SYNC_DEBUG] Tentativo rimozione come struttura cartella: '{folder_metadata_name}'")
            success2 = remove_documents_from_vectorstore(folder_metadata_name)
            
            if success1 or success2:
                logger.info(f"✅ Elemento {relative_path} rimosso automaticamente dal vectorstore")
                logger.debug(f"[FOLDER_SYNC_DEBUG] Rimozione completata con successo: file={success1}, cartella={success2}")
            else:
                logger.warning(f"[FOLDER_SYNC_DEBUG] Elemento {relative_path} non trovato nel vectorstore per rimozione")
                
        except Exception as e:
            logger.error(f"[FOLDER_SYNC_DEBUG] ❌ Errore rimozione automatica {path}: {e}", exc_info=True)


class FolderMonitorService:
    """
    Servizio per monitorare cartelle e mantenere sincronizzato il vectorstore.
    """
    
    def __init__(self):
        self.observers = {}  # Dict[str, Observer]
        self.monitored_folders = {}  # Dict[str, str] - path -> user_id
    
    def start_monitoring(self, folder_path: str, user_id: str = "system") -> bool:
        """
        Inizia il monitoraggio di una cartella.
        """
        try:
            if not os.path.exists(folder_path):
                logger.error(f"Cartella {folder_path} non esiste")
                return False
            
            if folder_path in self.observers:
                logger.warning(f"Cartella {folder_path} già monitorata")
                return True
            
            # Crea handler e observer
            handler = FolderVectorstoreSyncHandler(user_id)
            observer = Observer()
            observer.schedule(handler, folder_path, recursive=True)
            
            # Avvia il monitoraggio
            observer.start()
            
            # Salva riferimenti
            self.observers[folder_path] = observer
            self.monitored_folders[folder_path] = user_id
            
            logger.info(f"✅ Monitoraggio iniziato per cartella: {folder_path} (utente: {user_id})")
            return True
            
        except Exception as e:
            logger.error(f"Errore avvio monitoraggio cartella {folder_path}: {e}")
            return False
    
    def stop_monitoring(self, folder_path: str) -> bool:
        """
        Ferma il monitoraggio di una cartella.
        """
        try:
            if folder_path not in self.observers:
                logger.warning(f"Cartella {folder_path} non è monitorata")
                return False
            
            observer = self.observers[folder_path]
            observer.stop()
            observer.join()
            
            del self.observers[folder_path]
            del self.monitored_folders[folder_path]
            
            logger.info(f"✅ Monitoraggio fermato per cartella: {folder_path}")
            return True
            
        except Exception as e:
            logger.error(f"Errore stop monitoraggio cartella {folder_path}: {e}")
            return False
    
    def get_monitored_folders(self) -> Dict[str, str]:
        """
        Restituisce la lista delle cartelle monitorate.
        """
        return self.monitored_folders.copy()
    
    def stop_all_monitoring(self):
        """
        Ferma il monitoraggio di tutte le cartelle.
        """
        for folder_path in list(self.observers.keys()):
            self.stop_monitoring(folder_path)
        
        logger.info("✅ Monitoraggio fermato per tutte le cartelle")


# Istanza globale del servizio
folder_monitor_service = FolderMonitorService()


def query_folder_information(query: str) -> dict:
    """
    Query specializzata per informazioni strutturali su cartelle
    Es: "quanti file ci sono nella cartella documenti?"
    
    Args:
        query: Query dell'utente
        
    Returns:
        Risposta con informazioni strutturali
    """
    try:
        from backend.core.rag_vectorstore import get_vectorstore
        
        vectorstore = get_vectorstore()
        if not vectorstore:
            return {
                "status": "error",
                "message": "Vectorstore non disponibile",
                "query": query
            }
        
        # Ricerca focalizzata sui metadati directory
        results = vectorstore.similarity_search(
            query=query,
            k=5,
            filter={"document_type": "directory_metadata"}
        )
        
        if not results:
            return {
                "status": "no_results",
                "message": "Nessuna informazione di cartella trovata per questa query",
                "query": query
            }
        
        # Estrai informazioni strutturali dai risultati
        folder_info = []
        for doc in results:
            metadata = doc.metadata or {}
            folder_info.append({
                "folder_path": metadata.get("folder_path"),
                "total_files": metadata.get("total_files", 0),
                "file_types": metadata.get("file_types", {}),
                "subdirs": metadata.get("subdirs", []),
                "total_size": metadata.get("total_size", 0),
                "last_modified": metadata.get("last_modified"),
                "description": doc.page_content
            })
        
        return {
            "status": "success",
            "query": query,
            "folder_info": folder_info,
            "count": len(folder_info)
        }
        
    except Exception as e:
        logger.error(f"❌ Errore query folder info '{query}': {e}")
        return {
            "status": "error",
            "message": f"Errore nella query: {str(e)}",
            "query": query
        }


def get_folder_statistics(folder_path: Optional[str] = None) -> dict:
    """
    Ottieni statistiche complete di una cartella specifica o di tutte
    
    Args:
        folder_path: Percorso della cartella (None = tutte)
        
    Returns:
        Statistiche dettagliate
    """
    try:
        from backend.core.rag_vectorstore import get_vectorstore
        
        vectorstore = get_vectorstore()
        if not vectorstore:
            return {
                "status": "error",
                "message": "Vectorstore non disponibile",
                "folder_path": folder_path
            }
        
        # Costruisci filtro
        filter_criteria = {"document_type": "directory_metadata"}
        if folder_path:
            filter_criteria["folder_path"] = folder_path
        
        # Query per ottenere tutti i metadati directory
        results = vectorstore.similarity_search(
            query="cartella directory folder",  # Query generica per metadati
            k=100,
            filter=filter_criteria
        )
        
        if not results:
            return {
                "status": "no_data", 
                "message": "Nessuna cartella monitorata trovata",
                "folder_path": folder_path
            }
        
        # Aggrega statistiche
        total_folders = len(results)
        total_files = 0
        total_size = 0
        all_file_types = {}
        folders_details = []
        
        for doc in results:
            metadata = doc.metadata or {}
            
            files_count = metadata.get("total_files", 0)
            size = metadata.get("total_size", 0)
            file_types = metadata.get("file_types", {})
            
            total_files += files_count
            total_size += size
            
            # Aggrega tipi di file
            for ext, count in file_types.items():
                all_file_types[ext] = all_file_types.get(ext, 0) + count
            
            folders_details.append({
                "path": metadata.get("folder_path"),
                "files": files_count,
                "types": file_types,
                "size": size,
                "subdirs": metadata.get("subdirs", []),
                "last_modified": metadata.get("last_modified")
            })
        
        return {
            "status": "success",
            "folder_path": folder_path,
            "total_folders": total_folders,
            "total_files": total_files,
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_types_distribution": all_file_types,
            "folders": folders_details
        }
        
    except Exception as e:
        logger.error(f"❌ Errore ottenimento statistiche cartella '{folder_path}': {e}")
        return {
            "status": "error",
            "message": f"Errore nell'ottenimento delle statistiche: {str(e)}",
            "folder_path": folder_path
        }


def search_files_by_path(path_query: str) -> dict:
    """
    Cerca file basandosi sul percorso/nome
    Es: "trova tutti i file nella cartella documenti/2025"
    
    Args:
        path_query: Query relativa al percorso
        
    Returns:
        Lista di file trovati
    """
    try:
        from backend.core.rag_vectorstore import get_vectorstore
        
        vectorstore = get_vectorstore()
        if not vectorstore:
            return {
                "status": "error",
                "message": "Vectorstore non disponibile",
                "query": path_query
            }
        
        # Ricerca sui file con focus sui path
        results = vectorstore.similarity_search(
            query=path_query,
            k=20,
            filter={"document_type": "file_content_auto"}
        )
        
        if not results:
            return {
                "status": "no_results",
                "message": "Nessun file trovato per questo percorso",
                "query": path_query
            }
        
        # Estrai informazioni dei file
        files_found = []
        for doc in results:
            metadata = doc.metadata or {}
            files_found.append({
                "filename": os.path.basename(metadata.get("source_filename", "")),
                "full_path": metadata.get("source_filename"),
                "file_type": metadata.get("file_type"),
                "file_extension": metadata.get("file_extension"),
                "size": metadata.get("file_size"),
                "last_modified": metadata.get("last_modified"),
                "content_preview": doc.page_content[:200] + "..."
            })
        
        return {
            "status": "success",
            "query": path_query,
            "files_found": files_found,
            "count": len(files_found)
        }
        
    except Exception as e:
        logger.error(f"❌ Errore ricerca file per path '{path_query}': {e}")
        return {
            "status": "error",
            "message": f"Errore nella ricerca: {str(e)}",
            "query": path_query
        }
