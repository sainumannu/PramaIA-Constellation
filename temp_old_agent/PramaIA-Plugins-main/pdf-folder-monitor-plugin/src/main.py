
import uvicorn
import os

"""
ATTENZIONE:
Avvia il server SOLO con il comando:
    uvicorn src.main:app --reload --port $PLUGIN_PDF_MONITOR_PORT
Non usare 'python src/main.py' su Windows, altrimenti rischi di avviare più istanze o avere comportamenti inattesi.
Questo file serve solo come entrypoint per uvicorn.
"""
from .control_api import app, monitor

import threading
import time
import requests

# Configurazione centralizzata delle porte e URL tramite variabili d'ambiente

BACKEND_PORT = os.getenv("BACKEND_PORT") or "8000"
BACKEND_HOST = os.getenv("BACKEND_HOST") or "localhost"
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL") or f"http://{BACKEND_HOST}:{BACKEND_PORT}"

PLUGIN_PORT = os.getenv("PLUGIN_PDF_MONITOR_PORT") or "8001"
PLUGIN_HOST = os.getenv("PLUGIN_PDF_MONITOR_HOST") or "localhost"
PLUGIN_BASE_URL = os.getenv("PLUGIN_PDF_MONITOR_BASE_URL") or f"http://{PLUGIN_HOST}:{PLUGIN_PORT}"

SERVER_URL = f"{BACKEND_BASE_URL}/api/pdf-monitor/clients/register"
CLIENT_ID = os.getenv("PLUGIN_CLIENT_ID") or "pdf-monitor-001"  # personalizza se necessario
CLIENT_NAME = os.getenv("PLUGIN_CLIENT_NAME") or "PDF Folder Monitor"
CLIENT_ENDPOINT = PLUGIN_BASE_URL
def get_scan_paths():
    try:
        return monitor.get_folders()
    except Exception:
        return []

def try_register(online=True):
    payload = {
        "id": CLIENT_ID,
        "name": CLIENT_NAME,
        "endpoint": CLIENT_ENDPOINT,
        "scanPaths": get_scan_paths(),
        "online": online
    }
    try:
        resp = requests.post(SERVER_URL, json=payload, timeout=5)
        if resp.status_code == 200:
            print(f"✅ Stato client inviato: online={online}")
            return True
        else:
            print(f"❌ Errore invio stato client: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Connessione al server fallita: {e}")
        return False

def registration_loop():
    while True:
        if try_register():
            break
        print("Riprovo tra 60 secondi...")
        time.sleep(60)

def start_registration_thread():
    t = threading.Thread(target=registration_loop, daemon=True)
    t.start()

import atexit
# Avvia la registrazione automatica all'avvio
start_registration_thread()

# Invio stato offline al server alla chiusura del plugin
def send_offline():
    try_register(online=False)
atexit.register(send_offline)

# --- Endpoint per forzare la sincronizzazione dal server ---
from fastapi import Request
@app.post("/monitor/force-sync")
async def force_sync(request: Request):
    """
    Endpoint chiamato dal server per forzare la trasmissione degli eventi aggiornati.
    """
    # Qui dovresti implementare la logica per inviare gli eventi non ancora trasmessi
    # Ad esempio: chiama una funzione che invia gli eventi bufferizzati al backend
    # send_events_to_backend()
    print("[LOG] Comando ricevuto dal server: richiesta di sincronizzazione forzata.")
    return {"status": "sync_triggered"}

# Funzione per avviare il monitoraggio delle cartelle configurate con autostart
def start_autostart_monitoring():
    print("[LOG] Avvio monitoraggio cartelle autostart...")
    try:
        num_started = monitor.start_autostart_folders()
        if num_started > 0:
            print(f"✅ Avviate {num_started} cartelle con autostart")
        else:
            print("ℹ️ Nessuna cartella autostart configurata")
    except Exception as e:
        print(f"❌ Errore durante l'avvio delle cartelle autostart: {e}")

# Avvia il monitoraggio delle cartelle autostart dopo un breve ritardo
def delayed_autostart():
    # Aspetta 5 secondi per dare tempo al sistema di inizializzarsi
    time.sleep(5)
    start_autostart_monitoring()

# Avvia un thread separato per l'autostart
def start_autostart_thread():
    t = threading.Thread(target=delayed_autostart, daemon=True)
    t.start()

# Avvia l'autostart all'avvio del plugin
start_autostart_thread()

# Qui potrai aggiungere altre route FastAPI (es: /semantic-search, /events, ...)

if __name__ == "__main__":
    uvicorn.run("src.main:app", host=os.getenv("PLUGIN_PDF_MONITOR_HOST", "0.0.0.0"), port=int(PLUGIN_PORT), reload=True)
