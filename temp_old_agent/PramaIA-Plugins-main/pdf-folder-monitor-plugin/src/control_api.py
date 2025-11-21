
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    print("[LOG] PDF Folder Monitor Plugin avviato. FastAPI in ascolto.")

import os
# Leggi origins CORS da variabile d'ambiente (CORS_ORIGINS, separati da virgola)
cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173")
origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
class FolderPathConfig(BaseModel):
    folder_path: str

@app.post("/monitor/configure", tags=["Monitoring"])
def configure_folder(config: FolderPathConfig):
    """
    Aggiunge una path da monitorare e la salva subito in configurazione, senza avviare la scansione.
    """
    print(f"[LOG] Richiesta /monitor/configure ricevuta con payload: {config}")
    result = monitor.add_folder(config.folder_path)
    if result:
        print(f"[LOG] Path aggiunta: {config.folder_path}")
        return {"status": "success", "message": f"Path aggiunta e salvata: {config.folder_path}"}
    else:
        print(f"[LOG] Path NON aggiunta: {config.folder_path}")
        return {"status": "error", "message": f"Path non aggiunta: {config.folder_path}"}

from fastapi import HTTPException
from .folder_monitor import FolderMonitor
from .event_buffer import EventBuffer

monitor = FolderMonitor()
event_buffer = monitor.event_buffer
from typing import List, Optional

class MarkSentRequest(BaseModel):
    event_ids: List[int]

class EventStatusUpdate(BaseModel):
    event_id: int
    status: str
    document_id: Optional[str] = None
    error_message: Optional[str] = None

@app.get("/monitor/events", tags=["Monitoring"])
def get_unsent_events(limit: int = 100):
    """
    Restituisce gli eventi non ancora inviati al server (bufferizzati su SQLite).
    """
    return {"unsent_events": event_buffer.get_unsent_events(limit=limit)}

@app.get("/monitor/events/recent", tags=["Monitoring"])
def get_recent_events(limit: int = 100):
    """
    Restituisce gli eventi più recenti, inclusi quelli già inviati.
    """
    return {"events": event_buffer.get_recent_events(limit=limit)}

@app.post("/monitor/events/mark_sent", tags=["Monitoring"])
def mark_events_as_sent(req: MarkSentRequest):
    """
    Marca come inviati gli eventi con gli id specificati.
    """
    print(f"[LOG] Comando ricevuto dal server: marca come inviati gli eventi con id: {req.event_ids}")
    event_buffer.mark_events_as_sent(req.event_ids)
    return {"status": "ok", "marked": req.event_ids}

@app.post("/monitor/events/update_status", tags=["Monitoring"])
def update_event_status(update: EventStatusUpdate):
    """
    Aggiorna lo stato di elaborazione di un evento specifico.
    """
    print(f"[LOG] Aggiornamento stato evento {update.event_id} a '{update.status}'")
    success = event_buffer.update_event_status(
        update.event_id, 
        update.status, 
        update.document_id, 
        update.error_message
    )
    if not success:
        raise HTTPException(status_code=404, detail=f"Evento con id {update.event_id} non trovato")
    return {"status": "ok", "updated": update.event_id}

class FolderConfig(BaseModel):
    folder_paths: list[str]

@app.post("/monitor/start", tags=["Monitoring"])
def start_monitoring(config: FolderConfig):
    """
    Avvia il monitoraggio di una o più cartelle specifiche.
    """
    print(f"[LOG] Comando ricevuto dal server: avvia monitoraggio sulle cartelle: {config.folder_paths}")
    started = []
    errors = []
    for folder in config.folder_paths:
        if not os.path.isdir(folder):
            errors.append(folder)
            continue
        monitor.start(folder)
        started.append(folder)
    if errors:
        raise HTTPException(status_code=404, detail=f"Le seguenti cartelle non esistono: {errors}")
    return {"status": "success", "message": f"Monitoraggio avviato sulle cartelle: {started}"}

@app.post("/monitor/stop", tags=["Monitoring"])
def stop_monitoring():
    """
    Ferma il monitoraggio.
    """
    print("[LOG] Comando ricevuto dal server: stop monitoraggio.")
    monitor.stop()
    return {"status": "success", "message": "Monitoraggio fermato."}

@app.get("/monitor/status", tags=["Monitoring"])
def get_monitor_status():
    """
    Restituisce lo stato attuale del monitor, inclusa la lista dei PDF trovati.
    """
    print("[LOG] Comando ricevuto dal server: richiesta stato monitor.")
    return {
        "is_running": monitor.is_running(),
        "monitoring_folders": monitor.get_folders(),
        "detected_pdfs": monitor.get_pdfs(),
        "autostart_folders": monitor.get_autostart_folders()
    }

class AutostartConfig(BaseModel):
    folder_path: str
    autostart: bool = True

@app.post("/monitor/autostart", tags=["Monitoring"])
def set_folder_autostart(config: AutostartConfig):
    """
    Imposta o rimuove l'autostart per una cartella specifica.
    """
    print(f"[LOG] Comando ricevuto: {'abilita' if config.autostart else 'disabilita'} autostart per {config.folder_path}")
    
    result = monitor.set_folder_autostart(config.folder_path, config.autostart)
    
    if result:
        action = "abilitato" if config.autostart else "disabilitato"
        return {"status": "success", "message": f"Autostart {action} per {config.folder_path}"}
    else:
        return {"status": "error", "message": f"Impossibile modificare autostart per {config.folder_path}"}

@app.delete("/monitor/events/{event_id}", tags=["Monitoring"])
def delete_event(event_id: int):
    """
    Elimina un evento dal buffer.
    """
    print(f"[LOG] Comando ricevuto: elimina evento {event_id}")
    
    # Verifica prima se l'evento esiste
    with sqlite3.connect(event_buffer.db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM events WHERE id = ?", (event_id,))
        if not c.fetchone():
            raise HTTPException(status_code=404, detail=f"Evento con id {event_id} non trovato")
        
        # Elimina l'evento
        c.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
    
    return {"status": "success", "message": f"Evento {event_id} eliminato"}

@app.post("/monitor/events/{event_id}/retry", tags=["Monitoring"])
def retry_event(event_id: int):
    """
    Riprova l'elaborazione di un evento in errore.
    """
    print(f"[LOG] Comando ricevuto: riprova elaborazione evento {event_id}")
    
    # Verifica prima se l'evento esiste e recupera i dettagli
    with sqlite3.connect(event_buffer.db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT file_name, folder FROM events WHERE id = ?", (event_id,))
        event_data = c.fetchone()
        
        if not event_data:
            raise HTTPException(status_code=404, detail=f"Evento con id {event_id} non trovato")
        
        file_name, folder = event_data
        file_path = os.path.join(folder, file_name)
        
        # Verifica se il file esiste ancora
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File {file_path} non trovato")
        
        # Aggiorna lo stato dell'evento a 'processing'
        event_buffer.update_event_status(event_id, 'processing')
    
    # Invia il file al backend
    try:
        import requests
        BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
        BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", f"http://localhost:{BACKEND_PORT}")
        UPLOAD_URL = f"{BACKEND_BASE_URL}/api/pdf-monitor/upload/"
        
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f)}
            resp = requests.post(UPLOAD_URL, files=files, timeout=30)
        
        if resp.status_code == 200:
            print(f"✅ PDF '{file_name}' reinviato al backend con successo.")
            
            # Estrai l'ID del documento dalla risposta
            document_id = None
            try:
                result = resp.json()
                print(f"[DEBUG] Risposta backend: {result}")
                
                if 'document_id' in result:
                    document_id = result['document_id']
                elif 'result' in result and isinstance(result['result'], dict) and 'document_id' in result['result']:
                    document_id = result['result']['document_id']
                elif 'workflow_result' in result and isinstance(result['workflow_result'], dict) and 'document_id' in result['workflow_result']:
                    document_id = result['workflow_result']['document_id']
            except Exception as ex:
                print(f"[DEBUG] Errore nell'estrazione del document_id: {ex}")
            
            # Aggiorna stato: completato
            event_buffer.update_event_status(event_id, 'completed', document_id)
            return {"status": "success", "message": f"Evento {event_id} rielaborato con successo", "document_id": document_id}
        else:
            error_msg = f"HTTP {resp.status_code}: {resp.text}"
            event_buffer.update_event_status(event_id, 'error', None, error_msg)
            return {"status": "error", "message": f"Errore reinvio: {error_msg}"}
    
    except Exception as e:
        error_msg = str(e)
        event_buffer.update_event_status(event_id, 'error', None, error_msg)
        return {"status": "error", "message": f"Errore durante la rielaborazione: {error_msg}"}

@app.post("/monitor/remove_folder", tags=["Monitoring"])
def remove_folder(config: FolderPathConfig):
    """
    Rimuove una cartella dal monitoraggio.
    """
    print(f"[LOG] Comando ricevuto: rimuovi cartella {config.folder_path}")
    
    result = monitor.remove_folder(config.folder_path)
    
    if result:
        return {"status": "success", "message": f"Cartella rimossa: {config.folder_path}"}
    else:
        return {"status": "error", "message": f"Impossibile rimuovere cartella: {config.folder_path}"}

