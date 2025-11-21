#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT RIASSUNTIVO: Test rapido della pipeline
Da eseguire dopo che sono state applicate le correzioni
"""

import requests
import sqlite3
import os

BACKEND = "http://localhost:8000"
MONITOR = "http://localhost:8001"
DB = r"PramaIAServer\backend\db\database.db"

print("\n[CHECK] Pipeline PramaIA - Diagnostica Rapida\n")

# 1. Servizi
print("1. Servizi online?")
try:
    requests.get(f"{MONITOR}/monitor/status", timeout=2)
    print("   Monitor: OK")
except:
    print("   Monitor: OFFLINE")

try:
    requests.get(f"{BACKEND}/openapi.json", timeout=2)
    print("   Backend: OK")
except:
    print("   Backend: OFFLINE")

# 2. Database
print("\n2. Database")
if os.path.exists(DB):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM workflow_triggers WHERE active=1")
    triggers = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM workflow_executions")
    execs = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM pdf_monitor_events")
    events = c.fetchone()[0]
    
    print(f"   Trigger attivi: {triggers}")
    print(f"   Workflow esecuzioni: {execs}")
    print(f"   Monitor eventi: {events}")
    
    conn.close()

# 3. File test
print("\n3. File test")
test_file = r"D:\TestPramaIA\test_document_20251119_164346.pdf"
if os.path.exists(test_file):
    print(f"   Test PDF: OK ({os.path.getsize(test_file)} bytes)")
else:
    print(f"   Test PDF: NON TROVATO")

print("\n" + "="*50)
print("Leggi final_diagnostic_report.py per details")
print("="*50 + "\n")
