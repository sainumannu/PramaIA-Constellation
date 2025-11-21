#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verifica lo stato dei trigger e tenta di attivare manualmente
"""
import requests
import json

BACKEND_URL = "http://localhost:8000"

print("=" * 80)
print("VERIFICA E DEBUG TRIGGER")
print("=" * 80)
print()

# STEP 1: Recupera i trigger configurati
print("[STEP 1] Recupera trigger configurati")
print("-" * 80)
try:
    resp = requests.get(f"{BACKEND_URL}/api/workflows/triggers/", timeout=5)
    
    if resp.status_code == 200:
        triggers = resp.json().get('data', [])
        print(f"✅ Trovati {len(triggers)} trigger:")
        for trigger in triggers:
            print(f"   - {trigger.get('name', '?')}")
            print(f"     Event: {trigger.get('event_type', '?')}")
            print(f"     Workflow: {trigger.get('workflow_id', '?')}")
            print(f"     Active: {trigger.get('active', '?')}")
            print(f"     Target Node: {trigger.get('target_node_id', '?')}")
    else:
        print(f"❌ Errore: {resp.status_code}")
        print(resp.text[:200])
        
except Exception as e:
    print(f"❌ Errore: {e}")

print()

# STEP 2: Simula un evento di file_added
print("[STEP 2] Simula evento file_added")
print("-" * 80)
try:
    event_payload = {
        "event_type": "pdf_file_added",
        "source": "pdf_monitor",
        "metadata": {
            "file_name": "test_document_20251119_164346.pdf",
            "file_path": r"D:\TestPramaIA\test_document_20251119_164346.pdf",
            "file_size": 2163,
            "upload_time": "2025-11-19T16:43:46.000Z"
        }
    }
    
    print(f"📤 Inviando evento...")
    print(json.dumps(event_payload, indent=2))
    
    resp = requests.post(f"{BACKEND_URL}/api/events/process", json=event_payload, timeout=10)
    
    if resp.status_code == 200:
        result = resp.json()
        print(f"\n✅ Evento processato!")
        print(f"   Response: {json.dumps(result, indent=2)}")
    else:
        print(f"\n⚠️  Status: {resp.status_code}")
        print(f"   Response: {resp.text[:300]}")
        
except Exception as e:
    print(f"❌ Errore: {e}")

print()

# STEP 3: Controlla health del backend
print("[STEP 3] Health check backend")
print("-" * 80)
try:
    resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
    if resp.status_code == 200:
        print(f"✅ Backend OK")
        print(f"   Response: {resp.json()}")
    else:
        print(f"⚠️  Status: {resp.status_code}")
except Exception as e:
    print(f"❌ Errore: {e}")

print()
print("=" * 80)
