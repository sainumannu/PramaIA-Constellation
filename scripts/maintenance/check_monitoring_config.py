#!/usr/bin/env python3
"""
Check PDF Monitoring Configuration
Verifica la configurazione del sistema di monitoraggio PDF
"""

import sys
import os
import requests
import json
import sqlite3

# Aggiungi path per backend
sys.path.insert(0, os.path.join(os.getcwd(), 'PramaIAServer'))

print("🔍 =============== VERIFICA CONFIGURAZIONE MONITORING ===============")

def check_services():
    """Controlla servizi attivi"""
    print("\n🌐 === VERIFICA SERVIZI ===")
    
    services = {
        "Backend": "http://localhost:8000",
        "PDK Server": "http://localhost:3001", 
        "VectorStore": "http://localhost:8090",
        "LogService": "http://localhost:8081",
        "Agents": "http://localhost:8001"
    }
    
    for name, url in services.items():
        try:
            response = requests.get(f"{url}/health", timeout=3)
            if response.status_code == 200:
                print(f"✅ {name}: ONLINE")
            else:
                print(f"⚠️ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: OFFLINE - {e}")

def check_database_triggers():
    """Controlla trigger nel database"""
    print("\n📋 === VERIFICA TRIGGER DATABASE ===")
    
    db_path = "PramaIAServer/backend/db/database.db"
    if not os.path.exists(db_path):
        print(f"❌ Database non trovato: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query trigger - usa le tabelle corrette
        cursor.execute("SELECT name, event_type, conditions, workflow_id, active FROM workflow_triggers")
        workflow_triggers = cursor.fetchall()
        
        cursor.execute("SELECT id, name, event_type, workflow_id, active FROM event_triggers")
        event_triggers = cursor.fetchall()
        
        print(f"📊 Workflow Triggers: {len(workflow_triggers)}")
        print(f"📊 Event Triggers: {len(event_triggers)}")
        
        if workflow_triggers:
            print(f"\n🎯 WORKFLOW TRIGGERS:")
            for trigger in workflow_triggers:
                name, event_type, conditions, workflow_id, active = trigger
                status = "🟢 ATTIVO" if active else "🔴 INATTIVO"
                print(f"  • {name} - {status}")
                print(f"    Event: {event_type}")
                print(f"    Workflow ID: {workflow_id}")
                if conditions:
                    try:
                        cond_obj = json.loads(conditions)
                        print(f"    Condizioni: {cond_obj}")
                    except:
                        print(f"    Condizioni: {conditions}")
        
        if event_triggers:
            print(f"\n🎯 EVENT TRIGGERS:")
            for trigger in event_triggers:
                trigger_id, name, event_type, workflow_id, active = trigger
                status = "🟢 ATTIVO" if active else "🔴 INATTIVO"
                print(f"  • {name} ({trigger_id}) - {status}")
                print(f"    Event: {event_type}")
                print(f"    Workflow ID: {workflow_id}")
        
        # Query workflow collegati
        print(f"\n📋 === VERIFICA WORKFLOW ===")
        cursor.execute("SELECT id, name, description FROM workflows")
        workflows = cursor.fetchall()
        
        for wf_id, name, desc in workflows:
            print(f"\n🔧 Workflow {wf_id}: {name}")
            print(f"   Descrizione: {desc}")
            
            # Controlla se ha trigger collegati
            cursor.execute("SELECT COUNT(*) FROM triggers WHERE workflow_id = ?", (wf_id,))
            trigger_count = cursor.fetchone()[0]
            print(f"   Trigger collegati: {trigger_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Errore database: {e}")

def check_pdk_nodes():
    """Controlla nodi PDK disponibili"""
    print("\n🔧 === VERIFICA NODI PDK ===")
    
    try:
        response = requests.get("http://localhost:3001/api/nodes", timeout=5)
        if response.status_code == 200:
            nodes = response.json()
            print(f"📊 Nodi PDK disponibili: {len(nodes)}")
            
            # Filtra nodi rilevanti per PDF processing
            pdf_relevant = [
                'document_input_node',
                'pdf_text_extractor', 
                'text_chunker',
                'text_embedder',
                'chroma_vector_store'
            ]
            
            print("\n🎯 Nodi rilevanti per PDF processing:")
            for node_name in pdf_relevant:
                if node_name in nodes:
                    node_data = nodes[node_name]
                    print(f"✅ {node_name}")
                    print(f"   Descrizione: {node_data.get('description', 'N/A')}")
                    print(f"   Input: {list(node_data.get('inputs', {}).keys())}")
                    print(f"   Output: {list(node_data.get('outputs', {}).keys())}")
                else:
                    print(f"❌ {node_name} - NON DISPONIBILE")
        else:
            print(f"❌ PDK Server: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ PDK Server: {e}")

def check_agents_config():
    """Controlla configurazione Agents"""
    print("\n🤖 === VERIFICA AGENTS CONFIGURATION ===")
    
    agents_path = "PramaIA-Agents"
    if not os.path.exists(agents_path):
        print(f"❌ Directory Agents non trovata: {agents_path}")
        return
    
    # Controlla file di configurazione
    config_files = [
        "config.json",
        "monitored_config.json", 
        ".env"
    ]
    
    for config_file in config_files:
        config_path = os.path.join(agents_path, config_file)
        if os.path.exists(config_path):
            print(f"✅ {config_file} trovato")
            if config_file.endswith('.json'):
                try:
                    with open(config_path, 'r') as f:
                        config_data = json.load(f)
                    print(f"   Configurazione: {config_data}")
                except Exception as e:
                    print(f"   ⚠️ Errore lettura: {e}")
        else:
            print(f"❌ {config_file} non trovato")
    
    # Controlla cartella monitored_pdfs
    monitored_path = os.path.join(agents_path, "monitored_pdfs")
    if os.path.exists(monitored_path):
        files = os.listdir(monitored_path)
        print(f"\n📁 Cartella monitored_pdfs: {len(files)} files")
        for f in files[:5]:  # Mostra solo primi 5
            print(f"   • {f}")
    else:
        print(f"\n❌ Cartella monitored_pdfs non trovata in Agents")

def check_recent_activity():
    """Controlla attività recente"""
    print("\n📈 === ATTIVITÀ RECENTE ===")
    
    # Controlla VectorStore per documenti recenti
    try:
        response = requests.get("http://localhost:8090/documents/", timeout=5)
        if response.status_code == 200:
            docs = response.json()
            print(f"📋 Documenti nel VectorStore: {len(docs)}")
            
            # Ordina per data più recente
            if docs:
                print("\n🕒 Documenti più recenti:")
                # Prendi solo i primi 3
                for i, doc in enumerate(docs[-3:]):
                    filename = doc.get('filename', 'Unknown')
                    created = doc.get('created_at', doc.get('timestamp', 'Unknown'))
                    print(f"   {i+1}. {filename} - {created}")
        else:
            print(f"⚠️ VectorStore: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ VectorStore check: {e}")

def main():
    """Verifica principale"""
    try:
        check_services()
        check_database_triggers()
        check_pdk_nodes()
        check_agents_config()
        check_recent_activity()
        
        print(f"\n📊 === CONCLUSIONI ===")
        print(f"✅ Test configurazione completato")
        print(f"")
        print(f"💡 Per testare monitoring PDF:")
        print(f"   1. Assicurati che tutti i servizi siano online")
        print(f"   2. Verifica che esista trigger per file_upload/file_created")
        print(f"   3. Controlla che workflow collegato usi nodi moderni")
        print(f"   4. Aggiungi PDF alla cartella monitorata")
        print(f"   5. Verifica logs e VectorStore per nuovo documento")
        
    except Exception as e:
        print(f"❌ Errore verifica: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()