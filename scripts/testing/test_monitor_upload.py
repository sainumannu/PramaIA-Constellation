#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STRATEGIA ALTERNATIVA: Upload diretto via PDF Monitor
Il Monitor dovrebbe avere endpoint pubblici per l'upload senza autenticazione
"""

import requests
import json
import time
import sqlite3
import os

# Configurazione
MONITOR_URL = "http://localhost:8001"
BACKEND_URL = "http://localhost:8000"
DB_PATH = r"PramaIAServer\backend\db\database.db"
TEST_FILE = r"D:\TestPramaIA\test_document_20251119_164346.pdf"

print("=" * 100)
print("TEST: UPLOAD VIA PDF MONITOR (Pubblico)")
print("=" * 100)
print()

# =====================================================================
# STEP 1: Controlla endpoint Monitor per upload
# =====================================================================
print("[STEP 1] Controlla endpoint Monitor disponibili")
print("-" * 100)

try:
    resp = requests.get(f"{MONITOR_URL}/openapi.json", timeout=5)
    if resp.status_code == 200:
        spec = resp.json()
        paths = spec.get('paths', {})
        
        # Cerca endpoint di upload
        upload_endpoints = [p for p in paths if 'upload' in p.lower()]
        print(f"Endpoint upload trovati nel Monitor: {len(upload_endpoints)}")
        for ep in upload_endpoints:
            print(f"  - {ep}")
            for method in paths[ep].keys():
                print(f"    {method.upper()}")
    else:
        print(f"[WARN] OpenAPI non disponibile: {resp.status_code}")
except Exception as e:
    print(f"[ERROR] Errore: {e}")

print()

# =====================================================================
# STEP 2: Prova endpoint pubblico di upload
# =====================================================================
print("[STEP 2] Prova upload al Monitor (se disponibile)")
print("-" * 100)

try:
    # Prova /monitor/upload
    with open(TEST_FILE, 'rb') as f:
        files = {'file': (os.path.basename(TEST_FILE), f)}
        resp = requests.post(
            f"{MONITOR_URL}/monitor/upload",
            files=files,
            timeout=30
        )
    
    print(f"POST /monitor/upload → {resp.status_code}")
    if resp.status_code == 200:
        print(f"[OK] Upload riuscito!")
        print(f"   Response: {json.dumps(resp.json())[:200]}")
    elif resp.status_code == 404:
        print(f"[WARN] Endpoint non trovato")
    else:
        print(f"   Response: {resp.text[:200]}")
        
except Exception as e:
    print(f"[ERROR] Errore: {e}")

print()

# =====================================================================
# STEP 3: Controlla backend endpoint pubblico
# =====================================================================
print("[STEP 3] Controlla endpoint backend senza autenticazione")
print("-" * 100)

try:
    # Prova gli endpoint senza autenticazione
    upload_endpoints = [
        "/api/pdf-monitor/upload/",
        "/api/documents/upload/",
    ]
    
    for endpoint in upload_endpoints:
        try:
            # Prova OPTIONS per vedere se accetta preflight CORS
            resp = requests.options(f"{BACKEND_URL}{endpoint}", timeout=5)
            print(f"OPTIONS {endpoint} → {resp.status_code}")
        except:
            pass

except Exception as e:
    print(f"[ERROR] Errore: {e}")

print()

# =====================================================================
# STEP 4: Sommario database
# =====================================================================
print("[STEP 4] Stato database")
print("-" * 100)

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM workflow_executions")
    exec_count = cursor.fetchone()[0]
    
    print(f"Workflow executions: {exec_count}")
    
    conn.close()
except Exception as e:
    print(f"[ERROR] Errore database: {e}")

print()
print("=" * 100)
print("FINE TEST")
print("=" * 100)
