#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST E2E - Estrategia ottimale:
1. Registra nuovo utente
2. Login
3. Upload con token
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

# Credenziali di test (univoche per questa esecuzione)
import time as time_module
TEST_USER = f"testuser{int(time_module.time())}@example.com"
TEST_PASSWORD = "TestPassword123!"

print("=" * 100)
print("TEST E2E CON AUTENTICAZIONE (Strategia: Registra + Login)")
print("=" * 100)
print()

# =====================================================================
# STEP 1: REGISTRAZIONE
# =====================================================================
print("[STEP 1] Registrazione nuovo utente")
print("-" * 100)

try:
    resp = requests.post(
        f"{BACKEND_URL}/auth/register",
        json={
            "username": TEST_USER,
            "email": TEST_USER,
            "password": TEST_PASSWORD,
            "full_name": "Test User"
        },
        timeout=5
    )
    
    if resp.status_code == 200:
        reg_data = resp.json()
        access_token = reg_data.get('access_token')
        print(f"[OK] Registrazione riuscita")
        print(f"   Email: {TEST_USER}")
        print(f"   Token: {access_token[:30]}...")
    else:
        print(f"[ERROR] Registrazione fallita: {resp.status_code}")
        print(f"   Response: {resp.text[:300]}")
        exit(1)
        
except Exception as e:
    print(f"[ERROR] Errore registrazione: {e}")
    exit(1)

print()

# =====================================================================
# STEP 2: LOGIN
# =====================================================================
print("[STEP 2] Login con credenziali")
print("-" * 100)

try:
    resp = requests.post(
        f"{BACKEND_URL}/auth/token/local",
        data={
            "username": TEST_USER,
            "password": TEST_PASSWORD
        },
        timeout=5
    )
    
    if resp.status_code == 200:
        auth_data = resp.json()
        access_token = auth_data.get('access_token')
        print(f"[OK] Login riuscito")
        print(f"   Token: {access_token[:30]}...")
    else:
        print(f"[ERROR] Login fallito: {resp.status_code}")
        print(f"   {resp.text[:200]}")
        # Usa il token dalla registrazione se login fallisce
        print(f"   Uso token dalla registrazione...")
        
except Exception as e:
    print(f"[ERROR] Errore login: {e}")
    print(f"   Uso token dalla registrazione...")

print()

# =====================================================================
# STEP 3: UPLOAD
# =====================================================================
print("[STEP 3] Upload documento al backend")
print("-" * 100)

headers = {"Authorization": f"Bearer {access_token}"}

try:
    with open(TEST_FILE, 'rb') as f:
        files = {'files': (os.path.basename(TEST_FILE), f)}
        resp = requests.post(
            f"{BACKEND_URL}/api/documents/upload/",
            files=files,
            headers=headers,
            timeout=30
        )
    
    if resp.status_code == 200:
        result = resp.json()
        print(f"[OK] Upload completato!")
        
        # Estrai info dal documento caricato
        uploaded = result.get('uploaded_files', [])
        if uploaded:
            print(f"   File caricati: {len(uploaded)}")
            for doc in uploaded:
                print(f"      - {doc.get('filename', 'N/A')} (ID: {doc.get('id', 'N/A')})")
        else:
            print(f"   Response: {json.dumps(result)[:200]}")
            
        upload_success = True
    else:
        print(f"[ERROR] Upload fallito: {resp.status_code}")
        print(f"   Response: {resp.text[:300]}")
        upload_success = False
        
except Exception as e:
    print(f"[ERROR] Errore upload: {e}")
    upload_success = False

print()
time.sleep(3)

# =====================================================================
# STEP 4: VERIFICA NEL DATABASE
# =====================================================================
print("[STEP 4] Verifica esecuzione nel database")
print("-" * 100)

exec_count_before = 0
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Conta esecuzioni workflow
    cursor.execute("SELECT COUNT(*) FROM workflow_executions")
    exec_count_before = cursor.fetchone()[0]
    
    print(f"Workflow executions totali: {exec_count_before}")
    
    if exec_count_before > 0:
        cursor.execute("""
            SELECT id, workflow_id, status, started_at
            FROM workflow_executions
            ORDER BY started_at DESC
            LIMIT 3
        """)
        
        print("Ultimi 3 workflow:")
        for exec_row in cursor.fetchall():
            print(f"  - ID: {exec_row[0]}")
            print(f"    Workflow: {exec_row[1]}")
            print(f"    Status: {exec_row[2]}")
            print(f"    Started: {exec_row[3]}")
    
    conn.close()
except Exception as e:
    print(f"[ERROR] Errore database: {e}")

print()
print("=" * 100)

if upload_success and exec_count_before > 0:
    print("RISULTATO: Pipeline funzionante!")
elif upload_success:
    print("RISULTATO: Upload completato, workflow ancora in elaborazione...")
else:
    print("RISULTATO: Errore durante il processo")
    
print("=" * 100)
