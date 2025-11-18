import json
from datetime import datetime
from pathlib import Path
import shutil
import logging # Aggiungi logging
from backend.core.config import DATA_INDEX_PATH, DATA_DIR, INDEXES_DIR # Importa da config
from backend.core.rag_engine import ingest_pdf # Potrebbe rimanere qui o parte della logica spostata

logger = logging.getLogger(__name__) # Crea un logger per questo modulo

def save_file_metadata(filename: str, owner: str, size_bytes: int, is_public: bool = False):
    logger.info(f"Attempting to save metadata for: {filename}, owner: {owner}, size: {size_bytes} bytes, is_public: {is_public}")
    logger.debug(f"DATA_INDEX_PATH is: {DATA_INDEX_PATH}")
    DATA_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    if DATA_INDEX_PATH.exists():
        try:
            entries = json.loads(DATA_INDEX_PATH.read_text(encoding='utf-8'))
            logger.info(f"Loaded {len(entries)} existing entries from {DATA_INDEX_PATH}.")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {DATA_INDEX_PATH}: {e}. Starting with empty entries list.")
            entries = [] # Inizia con una lista vuota se il file è corrotto
    
    # Log prima della deduplicazione
    # logger.debug(f"Entries before deduplication for '{filename}': {entries}")
    
    entries_before_dedup_count = len(entries)
    entries = [e for e in entries if e["filename"] != filename]  # deduplica
    if len(entries) < entries_before_dedup_count:
        logger.info(f"Removed existing entry for '{filename}' during deduplication.")

    new_entry = {
        "filename": filename,
        "owner": owner,
        "timestamp": datetime.utcnow().isoformat(),
        "size": size_bytes, # Aggiungi la dimensione del file
        "is_public": is_public # Aggiungi il flag di visibilità
    }
    entries.append(new_entry)
    logger.info(f"Appended new entry for '{filename}'. Total entries now: {len(entries)}.")
    # logger.debug(f"Entries to be written: {entries}")

    try:
        DATA_INDEX_PATH.write_text(json.dumps(entries, indent=2), encoding='utf-8')
        logger.info(f"Successfully wrote {len(entries)} entries to {DATA_INDEX_PATH}.")
    except Exception as e:
        logger.error(f"Failed to write entries to {DATA_INDEX_PATH}: {e}", exc_info=True)


def load_file_metadata(user_id: str, user_role: str):
    """
    Carica i metadati dei file.
    NUOVO COMPORTAMENTO MISTO: 
    - Admin vede tutti i documenti
    - Utenti normali vedono i loro documenti privati + tutti i documenti pubblici
    """
    logger.info(f"Loading file metadata for user_id: '{user_id}', user_role: '{user_role}' (MIXED MODE)")
    logger.debug(f"DATA_INDEX_PATH is: {DATA_INDEX_PATH}")
    if not DATA_INDEX_PATH.exists():
        logger.warning(f"{DATA_INDEX_PATH} does not exist. Returning empty list.")
        return []
    
    try:
        entries = json.loads(DATA_INDEX_PATH.read_text(encoding='utf-8'))
        logger.info(f"Read {len(entries)} entries from {DATA_INDEX_PATH}.")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {DATA_INDEX_PATH} in load_file_metadata: {e}. Returning empty list.")
        return []
    
    processed_entries = []
    for i, entry in enumerate(entries):
        logger.debug(f"Processing entry {i+1}/{len(entries)}: {entry.get('filename')}, owner: {entry.get('owner')}")
        
        # Gestisci i file più vecchi che potrebbero non avere il campo 'size' o 'is_public'
        if "size" not in entry:
            file_on_disk = DATA_DIR / entry.get("filename", "") # Aggiunto default per get
            if file_on_disk.exists():
                entry["size"] = file_on_disk.stat().st_size
                logger.debug(f"Size for '{entry.get('filename')}' (from disk): {entry['size']}")
            else:
                entry["size"] = 0 # Default se il file non esiste più
                logger.debug(f"File '{entry.get('filename')}' not found on disk, size set to 0.")
        
        # Gestisci i file più vecchi che potrebbero non avere il campo 'is_public'
        if "is_public" not in entry:
            entry["is_public"] = False  # Default per retrocompatibilità
            logger.debug(f"Field 'is_public' missing for '{entry.get('filename')}', set to False.")
        
        # Logica di visibilità
        is_visible = False
        if user_role == "admin":
            # Admin vede tutto
            is_visible = True
        elif entry.get("is_public", False):
            # Documento pubblico - visibile a tutti
            is_visible = True
        elif entry.get("owner") == user_id:
            # Documento privato del proprietario
            is_visible = True
        
        if is_visible:
            processed_entries.append(entry)
            logger.debug(f"Entry '{entry.get('filename')}' is visible to user {user_id}")
        else:
            logger.debug(f"Entry '{entry.get('filename')}' is NOT visible to user {user_id} (private document of {entry.get('owner')})")
            
    logger.info(f"Returning {len(processed_entries)} processed entries for user '{user_id}' (mixed mode).")
    return processed_entries


def delete_file_metadata(filename: str):
    if DATA_INDEX_PATH.exists():
        entries = json.loads(DATA_INDEX_PATH.read_text(encoding='utf-8'))
        entries = [e for e in entries if e["filename"] != filename]
        DATA_INDEX_PATH.write_text(json.dumps(entries, indent=2), encoding='utf-8')

def get_file_details(filename: str):
    """
    Recupera i dettagli di un file specifico dai metadati.
    Restituisce un dizionario con i dettagli del file se trovato, altrimenti None.
    """
    if not DATA_INDEX_PATH.exists():
        return None
    entries = json.loads(DATA_INDEX_PATH.read_text(encoding='utf-8'))
    for entry in entries:
        if entry["filename"] == filename:
            return entry
    return None

async def process_uploaded_file(file_content: bytes, filename: str, user_id: str, is_public: bool = False):
    filepath = DATA_DIR / filename
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    file_size_bytes = len(file_content) # Ottieni la dimensione del file
    with open(filepath, "wb") as f:
        f.write(file_content)
    
    # La chiamata a ingest_pdf potrebbe essere fatta qui o il router potrebbe coordinare
    ingest_pdf(str(filepath), filename) # ingest_pdf dovrebbe usare percorsi da config
    save_file_metadata(filename, user_id, file_size_bytes, is_public) # Passa la dimensione e visibilità del file

def update_file_visibility(filename: str, is_public: bool, user_id: str, user_role: str):
    """
    Aggiorna la visibilità di un documento esistente.
    Solo il proprietario o l'admin possono modificare la visibilità.
    """
    logger.info(f"Attempting to update visibility for '{filename}' to is_public={is_public} by user {user_id}")
    
    if not DATA_INDEX_PATH.exists():
        logger.error("Data index file not found")
        return False, "File di metadati non trovato"
    
    try:
        entries = json.loads(DATA_INDEX_PATH.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
        return False, "Errore nella lettura dei metadati"
    
    # Trova il documento
    target_entry = None
    for entry in entries:
        if entry["filename"] == filename:
            target_entry = entry
            break
    
    if not target_entry:
        logger.error(f"Document '{filename}' not found in metadata")
        return False, "Documento non trovato"
    
    # Verifica autorizzazioni
    if user_role != "admin" and target_entry.get("owner") != user_id:
        logger.error(f"User {user_id} not authorized to modify '{filename}' (owner: {target_entry.get('owner')})")
        return False, "Non autorizzato a modificare questo documento"
    
    # Aggiorna la visibilità
    target_entry["is_public"] = is_public
    target_entry["visibility_updated_at"] = datetime.utcnow().isoformat()
    target_entry["visibility_updated_by"] = user_id
    
    try:
        DATA_INDEX_PATH.write_text(json.dumps(entries, indent=2), encoding='utf-8')
        logger.info(f"Successfully updated visibility for '{filename}' to is_public={is_public}")
        return True, f"Visibilità del documento aggiornata a {'pubblico' if is_public else 'privato'}"
    except Exception as e:
        logger.error(f"Error writing updated metadata: {e}")
        return False, "Errore nel salvataggio dei metadati"