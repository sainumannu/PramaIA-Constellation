"""
Script per verificare lo stato del watchdog nel monitor agent
"""
import requests
import json

def check_monitor_status():
    """Verifica lo stato del monitor tramite API"""
    try:
        response = requests.get("http://127.0.0.1:8001/monitor/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("\n=== STATO MONITOR AGENT ===")
            print(f"Running: {data.get('is_running')}")
            print(f"Monitoring Folders: {data.get('monitoring_folders')}")
            print(f"Detected Documents: {len(data.get('detected_documents', []))}")
            print(f"Autostart Folders: {data.get('autostart_folders')}")
            return True
        else:
            print(f"Errore API: {response.status_code}")
            return False
    except Exception as e:
        print(f"Errore connessione: {e}")
        return False

def check_observer_internals():
    """Verifica gli observer interni tramite endpoint dedicato se disponibile"""
    try:
        # Prova un endpoint di debug se esiste
        response = requests.get("http://127.0.0.1:8001/monitor/debug/observers", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("\n=== DEBUG OBSERVERS ===")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"\nEndpoint debug observers non disponibile (404)")
            return False
    except Exception as e:
        print(f"Endpoint debug non disponibile: {e}")
        return False

def trigger_manual_scan():
    """Forza una scansione manuale"""
    try:
        print("\n=== TRIGGER SCANSIONE MANUALE ===")
        response = requests.post("http://127.0.0.1:8001/monitor/scan", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"Scansione completata: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"Errore: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Errore trigger scan: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("VERIFICA STATO WATCHDOG - DOCUMENT MONITOR AGENT")
    print("=" * 70)
    
    # 1. Verifica stato base
    if not check_monitor_status():
        print("\nMonitor agent non raggiungibile!")
        exit(1)
    
    # 2. Verifica observer interni
    check_observer_internals()
    
    # 3. Trigger scansione manuale
    print("\n" + "=" * 70)
    input("Premi INVIO per triggerare una scansione manuale...")
    trigger_manual_scan()
    
    print("\n" + "=" * 70)
    print("Verifica completata")
