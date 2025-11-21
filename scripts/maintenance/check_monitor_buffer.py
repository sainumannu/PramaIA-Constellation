#!/usr/bin/env python3
"""
Verifica gli eventi nel buffer del Monitor
"""
import requests
import json
from datetime import datetime

MONITOR_URL = "http://localhost:8001"

print("=" * 80)
print("VERIFICA EVENTI NEL BUFFER DEL MONITOR")
print("=" * 80)
print()

try:
    # Recupera gli eventi recenti
    resp = requests.get(f"{MONITOR_URL}/monitor/events/recent?limit=30&include_history=true", timeout=5)
    
    if resp.status_code == 200:
        data = resp.json()
        events = data.get('events', [])
        
        print(f"✅ Recuperati {len(events)} eventi dal buffer")
        print()
        
        # Mostra tutti gli eventi
        for i, evt in enumerate(events, 1):
            print(f"[{i}]")
            print(f"    ID: {evt.get('id', '?')}")
            print(f"    File: {evt.get('file_name', '?')}")
            print(f"    Type: {evt.get('type', '?')}")
            print(f"    Status: {evt.get('status', '?')}")
            print(f"    Folder: {evt.get('folder', '?')}")
            print(f"    Timestamp: {evt.get('timestamp', '?')}")
            if evt.get('document_id'):
                print(f"    Document ID: {evt.get('document_id')}")
            if evt.get('error_message'):
                print(f"    Error: {evt.get('error_message')}")
            print()
    else:
        print(f"❌ Errore: {resp.status_code}")
        print(resp.text)
        
except Exception as e:
    print(f"❌ Errore: {e}")

print("=" * 80)
