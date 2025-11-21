#!/usr/bin/env python3
"""
Script per verificare workflow CRUD e nodi PDK disponibili
"""

import sqlite3
import json
import requests
from pathlib import Path

def check_database_workflows():
    """Controlla workflow nel database"""
    db_path = Path("PramaIAServer/backend/db/database.db")
    
    if not db_path.exists():
        print("❌ Database non trovato:", db_path)
        return []
        
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Lista workflow
        cursor.execute("SELECT id, name, is_active FROM workflows")
        workflows = cursor.fetchall()
        
        print(f"📋 Workflow in Database: {len(workflows)}")
        for w_id, name, is_active in workflows:
            status = "✅ Attivo" if is_active else "❌ Inattivo"
            print(f"   {w_id}: {name} ({status})")
            
        # Dettagli workflow con nodi
        print("\n🔍 Dettagli Workflow:")
        for w_id, name, _ in workflows:
            cursor.execute("SELECT nodes FROM workflows WHERE id = ?", (w_id,))
            result = cursor.fetchone()
            if result and result[0]:
                try:
                    nodes = json.loads(result[0])
                    node_types = [node.get('node_type', 'unknown') for node in nodes]
                    print(f"   {w_id} ({name}):")
                    print(f"      Nodi: {len(nodes)}")
                    print(f"      Tipi: {', '.join(set(node_types))}")
                except json.JSONDecodeError:
                    print(f"   {w_id} ({name}): ❌ Errore parsing nodi")
        
        conn.close()
        return workflows
        
    except Exception as e:
        print(f"❌ Errore database: {e}")
        return []

def check_pdk_nodes():
    """Controlla nodi disponibili nel PDK"""
    pdk_url = "http://127.0.0.1:3001"
    
    try:
        # Health check PDK
        health_response = requests.get(f"{pdk_url}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ PDK non disponibile (health check failed)")
            return []
            
        print("✅ PDK Server disponibile")
        
        # Lista nodi
        nodes_response = requests.get(f"{pdk_url}/api/nodes", timeout=10)
        if nodes_response.status_code != 200:
            print(f"❌ Errore recupero nodi: {nodes_response.status_code}")
            return []
            
        nodes_data = nodes_response.json()
        nodes = nodes_data.get('data', [])
        
        print(f"🔧 Nodi PDK disponibili: {len(nodes)}")
        
        # Raggruppa per plugin
        plugins = {}
        for node in nodes:
            plugin_name = node.get('plugin_name', 'unknown')
            if plugin_name not in plugins:
                plugins[plugin_name] = []
            plugins[plugin_name].append(node)
            
        for plugin_name, plugin_nodes in plugins.items():
            print(f"   📦 {plugin_name}: {len(plugin_nodes)} nodi")
            for node in plugin_nodes:
                node_id = node.get('node_id', 'unknown')
                node_type = node.get('node_type', 'unknown')
                print(f"      - {node_id} ({node_type})")
                
        return nodes
        
    except requests.ConnectionError:
        print("❌ PDK Server non raggiungibile (porta 3001)")
        return []
    except Exception as e:
        print(f"❌ Errore PDK: {e}")
        return []

def analyze_crud_coverage(workflows, nodes):
    """Analizza copertura operazioni CRUD"""
    
    print("\n📊 ANALISI COPERTURA CRUD")
    print("="*50)
    
    # CRUD operations mapping
    crud_operations = {
        'CREATE': ['pdf_document_create', 'document_create', 'vectorstore_add'],
        'READ': ['pdf_document_read', 'document_read', 'vectorstore_search', 'vectorstore_query'],
        'UPDATE': ['pdf_document_update', 'document_update', 'vectorstore_update'],
        'DELETE': ['pdf_document_delete', 'document_delete', 'vectorstore_delete']
    }
    
    # Workflow names analysis
    workflow_names = [w[1].lower() for w in workflows]
    available_nodes = [n.get('node_type', '').lower() for n in nodes]
    
    for operation, expected_patterns in crud_operations.items():
        print(f"\n🔍 {operation} Operations:")
        
        # Check workflows
        matching_workflows = [name for name in workflow_names 
                            if any(pattern in name for pattern in expected_patterns)]
        
        if matching_workflows:
            print(f"   ✅ Workflow: {', '.join(matching_workflows)}")
        else:
            print(f"   ❌ Workflow: Nessuno trovato per {operation}")
            
        # Check nodes
        matching_nodes = [node for node in available_nodes 
                         if any(pattern in node for pattern in expected_patterns)]
        
        if matching_nodes:
            print(f"   ✅ Nodi: {', '.join(set(matching_nodes))}")
        else:
            print(f"   ❌ Nodi: Nessuno trovato per {operation}")

def check_semantic_capabilities(nodes):
    """Verifica capacità semantiche"""
    
    print("\n🧠 ANALISI CAPACITÀ SEMANTICHE")
    print("="*50)
    
    semantic_keywords = [
        'semantic', 'embedding', 'vector', 'rag', 'llm', 
        'similarity', 'search', 'retrieval'
    ]
    
    semantic_nodes = []
    for node in nodes:
        node_type = node.get('node_type', '').lower()
        node_id = node.get('node_id', '').lower()
        
        if any(keyword in node_type or keyword in node_id for keyword in semantic_keywords):
            semantic_nodes.append(node)
            
    if semantic_nodes:
        print(f"✅ Nodi semantici trovati: {len(semantic_nodes)}")
        for node in semantic_nodes:
            print(f"   - {node.get('node_id')} ({node.get('node_type')})")
    else:
        print("❌ Nessun nodo semantico trovato")
        
    return semantic_nodes

def main():
    """Main function"""
    print("🔍 VERIFICA WORKFLOW CRUD E NODI PDK")
    print("="*60)
    
    # 1. Check database workflows
    print("\n1️⃣ CONTROLLO WORKFLOW DATABASE")
    workflows = check_database_workflows()
    
    # 2. Check PDK nodes
    print("\n2️⃣ CONTROLLO NODI PDK")
    nodes = check_pdk_nodes()
    
    # 3. Analyze CRUD coverage
    if workflows and nodes:
        analyze_crud_coverage(workflows, nodes)
        
        # 4. Check semantic capabilities
        semantic_nodes = check_semantic_capabilities(nodes)
        
        # 5. Summary
        print("\n📝 RIEPILOGO")
        print("="*50)
        print(f"✅ Workflow disponibili: {len(workflows)}")
        print(f"✅ Nodi PDK disponibili: {len(nodes)}")
        print(f"✅ Nodi semantici: {len(semantic_nodes) if 'semantic_nodes' in locals() else 0}")
        
        # Recommendations
        print("\n💡 RACCOMANDAZIONI")
        print("="*50)
        
        if len(workflows) < 4:
            print("⚠️  Considerare aggiunta workflow per operazioni CRUD complete")
            
        if not any('semantic' in n.get('node_type', '').lower() for n in nodes):
            print("⚠️  Verificare disponibilità nodi semantici/RAG")
            
        if not any('vectorstore' in n.get('node_type', '').lower() for n in nodes):
            print("⚠️  Verificare integrazione VectorStore")
            
    else:
        print("\n❌ Impossibile completare analisi - servizi non disponibili")

if __name__ == "__main__":
    main()