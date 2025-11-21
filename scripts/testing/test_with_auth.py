#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST E2E CON AUTENTICAZIONE
Autentica al backend e poi esegui il test completo
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

# Credenziali di test
TEST_USER = "user@example.com"
TEST_PASSWORD = "password123"

print("=" * 100)
print("TEST E2E CON AUTENTICAZIONE")
print("=" * 100)
print()

# =====================================================================
# AUTENTICAZIONE
# =====================================================================
print("[AUTH] Autenticazione al backend")
print("-" * 100)

try:
    # Prova prima il login locale
    resp = requests.post(
        f"{BACKEND_URL}/auth/token/local",
        data={"username": TEST_USER, "password": TEST_PASSWORD},
        timeout=5
    )
    
    if resp.status_code == 200:
        auth_data = resp.json()
        access_token = auth_data.get('access_token')
        print(f"[OK] Autenticazione riuscita")
        print(f"   Token ottenuto: {access_token[:20]}...")
    elif resp.status_code == 422:
        print(f"[ERROR] Validazione fallita - provo registrazione...")
        
        # Prova registrazione
        resp_reg = requests.post(
            f"{BACKEND_URL}/auth/register",
            json={"email": TEST_USER, "password": TEST_PASSWORD, "full_name": "Test User"},
            timeout=5
        )
        
        if resp_reg.status_code == 200:
            print(f"[OK] Utente registrato!")
            reg_data = resp_reg.json()
            access_token = reg_data.get('access_token')
            print(f"   Token: {access_token[:20]}...")
        else:
            print(f"[ERROR] Registrazione fallita: {resp_reg.status_code}")
            print(f"   {resp_reg.text[:200]}")
            exit(1)
    else:
        print(f"[ERROR] Login fallito: {resp.status_code}")
        print(f"   {resp.text[:200]}")
        exit(1)
        
except Exception as e:
    print(f"[ERROR] Errore autenticazione: {e}")
    exit(1)

print()

# =====================================================================
# UPLOAD CON TOKEN
# =====================================================================
print("[UPLOAD] Carica il documento al backend")
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
        print(f"   Response completo: {json.dumps(result, indent=2)}")
        
        # Estrai info dal documento caricato
        uploaded = result.get('uploaded_files', [{}])[0]
        doc_id = uploaded.get('id') or uploaded.get('filename')
        print(f"   Document ID/Name: {doc_id}")
    else:
        print(f"[ERROR] Upload fallito: {resp.status_code}")
        print(f"   Response: {resp.text}")
        
except Exception as e:
    print(f"[ERROR] Errore upload: {e}")

print()
time.sleep(2)

# =====================================================================
# VERIFICA NEL DATABASE
# =====================================================================
print("[DATABASE] Verifica nel database")
print("-" * 100)

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Conta esecuzioni workflow
    cursor.execute("SELECT COUNT(*) FROM workflow_executions")
    exec_count = cursor.fetchone()[0]
    
    print(f"Workflow eseguiti: {exec_count}")
    
    if exec_count > 0:
        cursor.execute("""
            SELECT id, workflow_id, status, started_at
            FROM workflow_executions
            ORDER BY started_at DESC
            LIMIT 3
        """)
        
        print("Ultimi workflow:")
        for exec_row in cursor.fetchall():
            print(f"  - ID: {exec_row[0]} | Status: {exec_row[2]} | Started: {exec_row[3]}")
    
    conn.close()
except Exception as e:
    print(f"[ERROR] Errore database: {e}")

print()
print("=" * 100)
print("TEST COMPLETATO")
print("=" * 100)
