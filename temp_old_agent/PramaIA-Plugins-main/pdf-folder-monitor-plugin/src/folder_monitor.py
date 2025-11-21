import threading
import time
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from .event_buffer import EventBuffer

class PDFHandler(FileSystemEventHandler):
    def __init__(self, pdf_list, folder, event_buffer):
        self.pdf_list = pdf_list
        self.folder = folder
        self.event_buffer = event_buffer

    def on_created(self, event):
        if event.is_directory:
            return
        if str(event.src_path).lower().endswith('.pdf'):
            file_name = os.path.basename(event.src_path)
            print(f"Nuovo PDF rilevato: {event.src_path}")
            self.pdf_list.append(file_name)
            
            # Aggiungi l'evento al buffer
            self.event_buffer.add_event('created', file_name, self.folder)
            
            # Cerca l'ID dell'evento appena creato
            event_id = self.event_buffer.find_event_by_filename(file_name)
            
            # Invio automatico del PDF al backend
            try:
                # Aggiorna stato: in elaborazione
                if event_id:
                    self.event_buffer.update_event_status(event_id, 'processing')
                
                import requests
                BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
                BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", f"http://localhost:{BACKEND_PORT}")
                UPLOAD_URL = f"{BACKEND_BASE_URL}/api/pdf-monitor/upload/"
                with open(event.src_path, "rb") as f:
                    files = {"file": (file_name, f)}
                    resp = requests.post(UPLOAD_URL, files=files, timeout=30)  # type: ignore
                
                if resp.status_code == 200:
                    print(f"✅ PDF '{file_name}' inviato al backend con successo.")
                    # Estrai l'ID del documento dalla risposta, se disponibile
                    document_id = None
                    try:
                        result = resp.json()
                        print(f"[DEBUG] Risposta backend: {result}")
                        
                        # Cerca il document_id in diversi possibili percorsi nella risposta
                        if 'document_id' in result:
                            document_id = result['document_id']
                            print(f"[DEBUG] Document ID trovato direttamente: {document_id}")
                        elif 'result' in result and isinstance(result['result'], dict):
                            # Cerca nel campo 'result' che potrebbe contenere il document_id
                            if 'document_id' in result['result']:
                                document_id = result['result']['document_id']
                                print(f"[DEBUG] Document ID trovato in result: {document_id}")
                        elif 'workflow_result' in result and isinstance(result['workflow_result'], dict):
                            if 'document_id' in result['workflow_result']:
                                document_id = result['workflow_result']['document_id']
                                print(f"[DEBUG] Document ID trovato in workflow_result: {document_id}")
                        else:
                            print(f"[DEBUG] Nessun Document ID trovato nella risposta: {result.keys()}")
                            
                    except Exception as ex:
                        print(f"[DEBUG] Errore nell'estrazione del document_id: {ex}")
                    
                    # Aggiorna stato: completato
                    if event_id:
                        self.event_buffer.update_event_status(event_id, 'completed', document_id)
                        print(f"[DEBUG] Evento {event_id} aggiornato con document_id: {document_id}")
                    else:
                        print(f"[DEBUG] Nessun evento trovato per il file {file_name}")
                else:
                    print(f"❌ Errore invio PDF '{file_name}' al backend: {resp.status_code} {resp.text}")
                    # Aggiorna stato: errore
                    if event_id:
                        self.event_buffer.update_event_status(event_id, 'error', None, f"HTTP {resp.status_code}: {resp.text}")
            except Exception as e:
                print(f"❌ Errore durante l'invio automatico del PDF '{file_name}' al backend: {e}")
                # Aggiorna stato: errore
                if event_id:
                    self.event_buffer.update_event_status(event_id, 'error', None, str(e))


class FolderMonitor:
    def remove_folder(self, folder):
        """
        Rimuove una cartella dal monitoraggio e dalla configurazione.
        """
        if folder in self.folders:
            self.folders.remove(folder)
            self._save_config()
            self._notify_server()
            print(f"[LOG] Path rimossa dalla configurazione: {folder}")
            return True
        print(f"[LOG] Path non trovata in configurazione: {folder}")
        return False
    def add_folder(self, folder):
        """
        Aggiunge una cartella da monitorare e la salva subito in configurazione, senza avviare la scansione.
        """
        if not os.path.isdir(folder):
            print(f"Errore: La cartella '{folder}' non esiste.")
            return False
        if folder not in self.folders:
            self.folders.append(folder)
            self._save_config()
            print(f"[LOG] Path aggiunta e salvata in configurazione: {folder}")
            self._notify_server()
            return True
        print(f"[LOG] Path già presente in configurazione: {folder}")
        return False
    import json
    CONFIG_FILE = "monitor_config.json"
    def __init__(self):
        self.folders = []  # lista di cartelle monitorate
        self.autostart_folders = []  # lista di cartelle con autostart abilitato
        self.pdf_list = []
        self.observers = []
        self.running = False
        self.event_buffer = EventBuffer()
        self._load_config()

    def _load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.folders = data.get("folders", [])
                    # Carica le configurazioni di autostart, se presenti
                    self.autostart_folders = data.get("autostart_folders", [])
            except Exception as e:
                print(f"Errore caricamento config: {e}")
        else:
            self.folders = []
            self.autostart_folders = []

    def _save_config(self):
        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "folders": self.folders,
                    "autostart_folders": self.autostart_folders
                }, f)
        except Exception as e:
            print(f"Errore salvataggio config: {e}")

    def start(self, folder):
        if not os.path.isdir(folder):
            print(f"Errore: La cartella '{folder}' non esiste.")
            return
        if folder not in self.folders:
            self.folders.append(folder)
            self._save_config()
            self._notify_server()
        print(f"Avvio monitoraggio su: {folder}")
        self.pdf_list += [f for f in os.listdir(folder) if f.lower().endswith((".pdf",))]
        event_handler = PDFHandler(self.pdf_list, folder, self.event_buffer)
        observer = Observer()
        observer.schedule(event_handler, folder, recursive=False)
        observer.start()
        self.observers.append(observer)
        self.running = True
        print("Monitoraggio avviato.")

    def stop(self):
        for observer in self.observers:
            if observer.is_alive():
                observer.stop()
                observer.join()
        self.observers = []
        print("Monitoraggio fermato.")
        self.running = False
        # Notifica al server che il monitoraggio è stato fermato (percorsi aggiornati)
        self._notify_server()
    def _notify_server(self):
        # Import qui per evitare dipendenze circolari
        try:
            import requests
            import os
            
            # Configurazione centralizzata delle porte e URL
            BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
            PLUGIN_PORT = os.getenv("PLUGIN_PDF_MONITOR_PORT", "8001")
            BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", f"http://localhost:{BACKEND_PORT}")
            PLUGIN_BASE_URL = os.getenv("PLUGIN_PDF_MONITOR_BASE_URL", f"http://localhost:{PLUGIN_PORT}")
            
            SERVER_URL = f"{BACKEND_BASE_URL}/api/pdf-monitor/clients/register"
            CLIENT_ID = "pdf-monitor-001"
            CLIENT_NAME = "PDF Folder Monitor"
            CLIENT_ENDPOINT = PLUGIN_BASE_URL
            payload = {
                "id": CLIENT_ID,
                "name": CLIENT_NAME,
                "endpoint": CLIENT_ENDPOINT,
                "scanPaths": self.get_folders(),
                "online": True
            }
            resp = requests.post(SERVER_URL, json=payload, timeout=5)
            if resp.status_code == 200:
                print("✅ Stato client aggiornato al server.")
            else:
                print(f"❌ Errore aggiornamento stato client: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"❌ Errore invio stato client: {e}")

    def set_folder_autostart(self, folder, autostart=True):
        """
        Imposta o rimuove l'autostart per una cartella specifica.
        """
        if folder not in self.folders:
            print(f"Errore: La cartella '{folder}' non è configurata.")
            return False
        
        if autostart and folder not in self.autostart_folders:
            self.autostart_folders.append(folder)
            self._save_config()
            print(f"[LOG] Autostart abilitato per: {folder}")
            self._notify_server()
            return True
        elif not autostart and folder in self.autostart_folders:
            self.autostart_folders.remove(folder)
            self._save_config()
            print(f"[LOG] Autostart disabilitato per: {folder}")
            self._notify_server()
            return True
        
        print(f"[LOG] Nessuna modifica all'autostart per: {folder}")
        return False
    
    def is_folder_autostart(self, folder):
        """
        Verifica se una cartella ha l'autostart abilitato.
        """
        return folder in self.autostart_folders
    
    def get_autostart_folders(self):
        """
        Restituisce la lista delle cartelle con autostart abilitato.
        """
        return list(self.autostart_folders)
    
    def start_autostart_folders(self):
        """
        Avvia il monitoraggio di tutte le cartelle configurate con autostart.
        """
        print(f"[LOG] Avvio monitoraggio cartelle autostart: {self.autostart_folders}")
        for folder in self.autostart_folders:
            if os.path.isdir(folder):
                self.start(folder)
            else:
                print(f"[WARN] Cartella autostart non trovata: {folder}")
        
        return len([obs for obs in self.observers if obs.is_alive()])

    def get_pdfs(self):
        return list(set(self.pdf_list))

    def is_running(self):
        return self.running

    def get_folders(self):
        return list(self.folders)
