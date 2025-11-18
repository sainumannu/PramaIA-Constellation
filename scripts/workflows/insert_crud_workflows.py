#!/usr/bin/env python3
"""
Script per inserire tutti e 4 i workflow CRUD completi per PDF nel database PramaIA
"""

import json
import requests
import sys
import os
from pathlib import Path

# Configurazione
API_BASE_URL = "http://localhost:8000"
WORKFLOWS_DIR = "PramaIA-PDK/workflows/"

# Lista dei workflow CRUD da inserire
CRUD_WORKFLOWS = [
    {
        "file": "pdf_document_create_pipeline.json",
        "name": "PDF Document CREATE Pipeline"
    },
    {
        "file": "pdf_document_read_pipeline.json", 
        "name": "PDF Document READ Pipeline"
    },
    {
        "file": "pdf_document_update_pipeline.json",
        "name": "PDF Document UPDATE Pipeline"
    },
    {
        "file": "pdf_document_delete_pipeline.json",
        "name": "PDF Document DELETE Pipeline"
    }
]

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

def load_workflow_json(file_path: str) -> dict:
    """Carica il workflow JSON dal file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)
        return workflow_data
    except Exception as e:
        print(f"❌ Errore nel caricamento del workflow {file_path}: {e}")
        return None

def check_existing_workflow(token: str, workflow_name: str) -> bool:
    """Verifica se il workflow esiste già nel database"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{API_BASE_URL}/api/workflows/"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            workflows = response.json()
            for wf in workflows:
                if wf.get("name") == workflow_name:
                    return True
            return False
        else:
            return False
            
    except Exception as e:
        return False

def create_workflow(token: str, workflow_data: dict) -> dict:
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
            "category": workflow_data.get("category", "CRUD"),
            "tags": workflow_data.get("tags", []),
            "view_state": workflow_data.get("view_state", {}),
            "nodes": workflow_data.get("nodes", []),
            "connections": workflow_data.get("connections", []),
            "metadata": workflow_data.get("metadata", {})
        }
        
        response = requests.post(url, json=api_data, headers=headers)
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            return {"success": True, "result": result}
        else:
            return {"success": False, "error": f"Status: {response.status_code}, Response: {response.text}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    """Funzione principale dello script"""
    print("🚀 PramaIA - Inserimento Workflow CRUD Completi PDF")
    print("=" * 60)
    
    # Autentica
    print("\n📝 Autenticazione...")
    token = authenticate()
    
    successful_workflows = []
    failed_workflows = []
    skipped_workflows = []
    
    # Processa ogni workflow CRUD
    for workflow_info in CRUD_WORKFLOWS:
        workflow_file = os.path.join(WORKFLOWS_DIR, workflow_info["file"])
        workflow_name = workflow_info["name"]
        
        print(f"\n🔧 Elaborazione: {workflow_name}")
        print(f"   File: {workflow_file}")
        
        # Carica il workflow JSON
        workflow_data = load_workflow_json(workflow_file)
        if not workflow_data:
            failed_workflows.append({"name": workflow_name, "reason": "Errore caricamento file"})
            continue
        
        # Verifica se esiste già
        if check_existing_workflow(token, workflow_name):
            print(f"   ⚠️  Workflow già esistente, saltato")
            skipped_workflows.append(workflow_name)
            continue
        
        # Crea il workflow
        result = create_workflow(token, workflow_data)
        if result["success"]:
            wf_result = result["result"]
            print(f"   ✅ Creato con successo!")
            print(f"      ID: {wf_result.get('workflow_id', 'N/A')}")
            print(f"      Nodi: {len(workflow_data.get('nodes', []))}")
            print(f"      Connessioni: {len(workflow_data.get('connections', []))}")
            successful_workflows.append({
                "name": workflow_name,
                "id": wf_result.get('workflow_id', 'N/A'),
                "nodes": len(workflow_data.get('nodes', [])),
                "connections": len(workflow_data.get('connections', []))
            })
        else:
            print(f"   ❌ Errore nella creazione: {result['error']}")
            failed_workflows.append({"name": workflow_name, "reason": result['error']})
    
    # Riepilogo finale
    print(f"\n📊 RIEPILOGO OPERAZIONI")
    print("=" * 60)
    print(f"✅ Workflow creati con successo: {len(successful_workflows)}")
    print(f"⚠️  Workflow saltati (già esistenti): {len(skipped_workflows)}")
    print(f"❌ Workflow falliti: {len(failed_workflows)}")
    
    if successful_workflows:
        print(f"\n🎉 Workflow creati:")
        for wf in successful_workflows:
            print(f"   - {wf['name']}")
            print(f"     ID: {wf['id']}, Nodi: {wf['nodes']}, Connessioni: {wf['connections']}")
    
    if skipped_workflows:
        print(f"\n⚠️  Workflow saltati:")
        for wf_name in skipped_workflows:
            print(f"   - {wf_name}")
    
    if failed_workflows:
        print(f"\n❌ Workflow falliti:")
        for wf in failed_workflows:
            print(f"   - {wf['name']}: {wf['reason']}")
    
    print(f"\n📖 Architettura CRUD Completa:")
    print(f"   🏗️  Backend (FastAPI:8000): Orchestrazione + Metadati")
    print(f"   ⚙️  PDK Server (Node.js:3001): Elaborazione + Semantico") 
    print(f"   🗄️  Dual-Storage: Database + ChromaDB")
    print(f"   🔄 CRUD Operations: CREATE, READ, UPDATE, DELETE")
    
    print(f"\n📱 Frontend: http://localhost:3000")
    print(f"   Sezione Workflows > Categoria: CRUD")

if __name__ == "__main__":
    main()