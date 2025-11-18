#!/usr/bin/env python3
"""
Script per inserire il workflow PDF Semantic Processing Pipeline nel database PramaIA
"""

import json
import requests
import sys
import os
from pathlib import Path

# Configurazione
API_BASE_URL = "http://localhost:8000"
WORKFLOW_FILE = "PramaIA-PDK/workflows/pdf_semantic_processing_pipeline.json"

def load_workflow_json(file_path: str) -> dict:
    """Carica il workflow JSON dal file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)
        print(f"✅ Caricato workflow da: {file_path}")
        print(f"   Nome: {workflow_data.get('name', 'N/A')}")
        print(f"   Nodi: {len(workflow_data.get('nodes', []))}")
        print(f"   Connessioni: {len(workflow_data.get('connections', []))}")
        return workflow_data
    except Exception as e:
        print(f"❌ Errore nel caricamento del workflow: {e}")
        sys.exit(1)

def authenticate(username: str = "admin", password: str = "admin") -> str:
    """Autentica e ottiene il token JWT"""
    try:
        auth_url = f"{API_BASE_URL}/auth/token/local"
        auth_data = {
            "username": username,
            "password": password
        }
        
        response = requests.post(auth_url, data=auth_data)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print(f"✅ Autenticato come: {username}")
            return access_token
        else:
            print(f"❌ Errore autenticazione: {response.status_code} - {response.text}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Errore durante l'autenticazione: {e}")
        sys.exit(1)

def check_existing_workflow(token: str, workflow_id: str) -> bool:
    """Verifica se il workflow esiste già nel database"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{API_BASE_URL}/api/workflows/{workflow_id}"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            print(f"⚠️  Workflow '{workflow_id}' già esistente nel database")
            return True
        elif response.status_code == 404:
            print(f"✅ Workflow '{workflow_id}' non presente, procedo con l'inserimento")
            return False
        else:
            print(f"❓ Risposta inaspettata dal server: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"⚠️  Errore durante la verifica: {e}, procedo comunque")
        return False

def create_workflow(token: str, workflow_data: dict) -> bool:
    """Crea il workflow nel database tramite API"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        url = f"{API_BASE_URL}/api/workflows/"
        
        # Prepara i dati per l'API
        api_data = {
            "name": workflow_data["name"],
            "description": workflow_data["description"],
            "is_active": workflow_data.get("is_active", True),
            "is_public": workflow_data.get("is_public", True),
            "assigned_groups": [],
            "category": workflow_data.get("category", "RAG"),
            "tags": workflow_data.get("tags", []),
            "view_state": workflow_data.get("view_state", {}),
            "nodes": workflow_data.get("nodes", []),
            "connections": workflow_data.get("connections", []),
            "metadata": workflow_data.get("metadata", {})
        }
        
        print(f"📤 Invio richiesta di creazione workflow...")
        print(f"   URL: {url}")
        print(f"   Dati: {len(json.dumps(api_data))} caratteri")
        
        response = requests.post(url, json=api_data, headers=headers)
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            print(f"✅ Workflow creato con successo!")
            print(f"   ID: {result.get('workflow_id', 'N/A')}")
            print(f"   Nome: {result.get('name', 'N/A')}")
            return True
        else:
            print(f"❌ Errore nella creazione del workflow:")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Errore durante la creazione del workflow: {e}")
        return False

def verify_workflow_creation(token: str, workflow_data: dict) -> bool:
    """Verifica che il workflow sia stato creato correttamente"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{API_BASE_URL}/api/workflows/"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            workflows = response.json()
            workflow_name = workflow_data["name"]
            
            # Cerca il workflow per nome
            found_workflow = None
            for wf in workflows:
                if wf.get("name") == workflow_name:
                    found_workflow = wf
                    break
            
            if found_workflow:
                print(f"✅ Verifica completata - Workflow trovato nel database:")
                print(f"   ID: {found_workflow.get('workflow_id')}")
                print(f"   Nome: {found_workflow.get('name')}")
                print(f"   Attivo: {found_workflow.get('is_active')}")
                return True
            else:
                print(f"❌ Workflow '{workflow_name}' non trovato nel database")
                return False
        else:
            print(f"❌ Errore durante la verifica: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Errore durante la verifica: {e}")
        return False

def main():
    """Funzione principale dello script"""
    print("🚀 PramaIA - Inserimento Workflow PDF Semantic Processing Pipeline")
    print("=" * 70)
    
    # 1. Carica il workflow JSON
    workflow_data = load_workflow_json(WORKFLOW_FILE)
    
    # 2. Autentica
    print("\n📝 Autenticazione...")
    token = authenticate()
    
    # 3. Verifica se esiste già
    print(f"\n🔍 Verifica esistenza workflow...")
    workflow_id = workflow_data.get("workflow_id", "pdf_semantic_processing")
    if check_existing_workflow(token, workflow_id):
        response = input("Il workflow esiste già. Continuare comunque? [y/N]: ")
        if response.lower() != 'y':
            print("❌ Operazione annullata dall'utente")
            sys.exit(0)
    
    # 4. Crea il workflow
    print(f"\n🔧 Creazione workflow...")
    if create_workflow(token, workflow_data):
        # 5. Verifica la creazione
        print(f"\n✅ Verifica finale...")
        if verify_workflow_creation(token, workflow_data):
            print(f"\n🎉 Workflow PDF Semantic Processing Pipeline inserito con successo!")
            print(f"\n📖 Prossimi passi:")
            print(f"   1. Vai al frontend: http://localhost:3000")
            print(f"   2. Apri la sezione Workflows")
            print(f"   3. Trova '{workflow_data['name']}'")
            print(f"   4. Testa l'esecuzione del workflow")
        else:
            print(f"\n⚠️  Workflow creato ma verifica fallita")
    else:
        print(f"\n❌ Fallimento nella creazione del workflow")
        sys.exit(1)

if __name__ == "__main__":
    main()