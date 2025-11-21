#!/usr/bin/env python3
"""
Test end-to-end per verificare:
1. Rilevamento del file da parte del Monitor
2. Vettorizzazione nel VectorStore
3. Memorizzazione corretta dei metadati
"""

import requests
import json
import time
import sqlite3
from datetime import datetime

# Configurazione
BACKEND_URL = "http://localhost:8000"
MONITOR_URL = "http://localhost:8001"
VECTORSTORE_URL = "http://localhost:8090"
DB_PATH = r"PramaIAServer\backend\db\database.db"

print("=" * 80)
print("TEST END-TO-END: VERIFICA VETTORIZZAZIONE E METADATI")
print("=" * 80)
print()

# STEP 1: Verifica stato del Monitor
print("[STEP 1] Verifica stato del PDF Monitor Agent")
print("-" * 80)
try:
    resp = requests.get(f"{MONITOR_URL}/monitor/status", timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Monitor è ONLINE")
        print(f"   Cartelle monitorate: {data.get('monitoring_folders', [])}")
        print(f"   Auto-start folders: {data.get('autostart_folders', [])}")
        print(f"   Running: {data.get('is_running', False)}")
    else:
        print(f"❌ Monitor non risponde: {resp.status_code}")
except Exception as e:
    print(f"❌ Errore contatto Monitor: {e}")

print()

# STEP 2: Verifica eventi bufferizzati nel Monitor
print("[STEP 2] Verifica eventi nel buffer del Monitor")
print("-" * 80)
try:
    resp = requests.get(f"{MONITOR_URL}/monitor/events/recent?limit=10", timeout=5)
    if resp.status_code == 200:
        events = resp.json().get('events', [])
        print(f"✅ Trovati {len(events)} eventi recenti nel buffer:")
        for event in events[-5:]:  # Mostra ultimi 5
            print(f"   - {event.get('type', '?')} | {event.get('file_name', '?')} | Status: {event.get('status', '?')}")
    else:
        print(f"⚠️  Nessun evento trovato nel buffer")
except Exception as e:
    print(f"❌ Errore nel recupero degli eventi: {e}")

print()

# STEP 3: Verifica database events nel backend
print("[STEP 3] Verifica eventi nel database del backend")
print("-" * 80)
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verifica se la tabella esiste
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pdf_monitor_events'")
    if cursor.fetchone():
        # Conta eventi
        cursor.execute("SELECT COUNT(*) FROM pdf_monitor_events")
        total_events = cursor.fetchone()[0]
        
        # Eventi recenti
        cursor.execute("""
            SELECT id, file_name, event_type, status, document_id, timestamp
            FROM pdf_monitor_events
            ORDER BY timestamp DESC
            LIMIT 5
        """)
        recent_events = cursor.fetchall()
        
        print(f"✅ Tabella pdf_monitor_events trovata")
        print(f"   Totale eventi: {total_events}")
        print(f"   Eventi recenti:")
        for evt in recent_events:
            print(f"      ID: {evt[0]}")
            print(f"         File: {evt[1]} | Type: {evt[2]} | Status: {evt[3]}")
            print(f"         DocID: {evt[4]} | Time: {evt[5]}")
    else:
        print(f"❌ Tabella pdf_monitor_events non trovata")
    
    conn.close()
except Exception as e:
    print(f"❌ Errore accesso database: {e}")

print()

# STEP 4: Verifica VectorStore status
print("[STEP 4] Verifica status del VectorStore")
print("-" * 80)
try:
    resp = requests.get(f"{VECTORSTORE_URL}/health", timeout=5)
    if resp.status_code == 200:
        health = resp.json()
        print(f"✅ VectorStore è ONLINE")
        print(f"   Status: {health.get('status', '?')}")
        print(f"   Version: {health.get('version', '?')}")
    else:
        print(f"❌ VectorStore non risponde: {resp.status_code}")
except Exception as e:
    print(f"❌ Errore contatto VectorStore: {e}")

print()

# STEP 5: Verifica documenti nel VectorStore
print("[STEP 5] Verifica documenti vettorizzati nel VectorStore")
print("-" * 80)
try:
    # Usa l'endpoint per ottenere statistiche
    resp = requests.get(f"{VECTORSTORE_URL}/status", timeout=5)
    if resp.status_code == 200:
        status = resp.json()
        print(f"✅ Status VectorStore:")
        print(f"   Stato: {status.get('status', '?')}")
        print(f"   Documenti in indice: {status.get('documents_in_index', 0)}")
        print(f"   Collections: {list(status.get('collections', {}).keys())}")
        
        # Mostra statistiche per collezione
        for coll_name, coll_stats in status.get('collections', {}).items():
            print(f"      - {coll_name}: {coll_stats.get('document_count', 0)} documenti")
    else:
        print(f"❌ Impossibile recuperare status VectorStore: {resp.status_code}")
except Exception as e:
    print(f"❌ Errore nel recupero status VectorStore: {e}")

print()

# STEP 6: Query diretto al VectorStore per documenti
print("[STEP 6] Dettagli documenti vettorizzati")
print("-" * 80)
try:
    resp = requests.get(f"{VECTORSTORE_URL}/collections", timeout=5)
    if resp.status_code == 200:
        collections = resp.json().get('collections', [])
        print(f"✅ Collezioni disponibili: {collections}")
        
        # Per ogni collezione, ottieni documenti
        for coll in collections:
            try:
                resp_docs = requests.get(f"{VECTORSTORE_URL}/collections/{coll}/documents?limit=5", timeout=5)
                if resp_docs.status_code == 200:
                    docs = resp_docs.json().get('documents', [])
                    print(f"\n   Collezione: {coll} ({len(docs)} documenti)")
                    for doc in docs[-3:]:  # Mostra ultimi 3
                        print(f"      - ID: {doc.get('id', '?')}")
                        print(f"        Metadata: {doc.get('metadata', {})}")
            except:
                pass
    else:
        print(f"⚠️  Impossibile recuperare collezioni")
except Exception as e:
    print(f"⚠️  Errore nel recupero documenti: {e}")

print()

# STEP 7: Verifica metadati nel database workflow_executions
print("[STEP 7] Verifica esecuzioni workflow nel database")
print("-" * 80)
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verifica se la tabella esiste
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_executions'")
    if cursor.fetchone():
        cursor.execute("""
            SELECT id, workflow_id, status, output_data, started_at
            FROM workflow_executions
            ORDER BY started_at DESC
            LIMIT 3
        """)
        executions = cursor.fetchall()
        
        if executions:
            print(f"✅ Trovate {len(executions)} esecuzioni workflow:")
            for exec_row in executions:
                print(f"   ID: {exec_row[0]} | Workflow: {exec_row[1]} | Status: {exec_row[2]}")
                print(f"      Output: {exec_row[3]}")
                print(f"      Started: {exec_row[4]}")
        else:
            print(f"⚠️  Nessuna esecuzione workflow trovata")
    else:
        print(f"❌ Tabella workflow_executions non trovata")
    
    conn.close()
except Exception as e:
    print(f"⚠️  Errore nel recupero workflow_executions: {e}")

print()

# STEP 8: Verifica trigger configuration
print("[STEP 8] Verifica configurazione Trigger")
print("-" * 80)
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name, event_type, workflow_id, target_node_id, active
        FROM workflow_triggers
    """)
    triggers = cursor.fetchall()
    
    print(f"✅ Trovati {len(triggers)} trigger configurati:")
    for trigger in triggers:
        active_status = "✓ ACTIVE" if trigger[4] else "✗ INACTIVE"
        print(f"   Nome: {trigger[0]} {active_status}")
        print(f"      Event: {trigger[1]}")
        print(f"      Workflow: {trigger[2]}")
        print(f"      Target Node: {trigger[3]}")
    
    conn.close()
except Exception as e:
    print(f"❌ Errore nel recupero trigger: {e}")

print()
print("=" * 80)
print("TEST COMPLETATO")
print("=" * 80)
