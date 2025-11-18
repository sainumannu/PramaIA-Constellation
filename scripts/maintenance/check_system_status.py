#!/usr/bin/env python3
"""
Database Status Check - Verifica stato database workflow

Script veloce per controllare contenuto database e registry.
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = "backend/db/database.db"

def check_database():
    """Verifica contenuto database."""
    if not Path(DB_PATH).exists():
        print(f"❌ Database non trovato: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("📊 DATABASE STATUS")
    print("=" * 40)
    
    # Verifica tabelle
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"📋 Tabelle: {len(tables)}")
    for table in sorted(tables):
        print(f"   - {table}")
    
    print()
    
    # Verifica workflow
    cursor.execute("SELECT COUNT(*) FROM workflows")
    workflow_count = cursor.fetchone()[0]
    print(f"🔄 Workflow: {workflow_count}")
    
    if workflow_count > 0:
        cursor.execute("SELECT workflow_id, name, tags FROM workflows")
        for row in cursor.fetchall():
            print(f"   - {row[1]} ({row[0]}) - {row[2]}")
    
    print()
    
    # Verifica nodi
    cursor.execute("SELECT COUNT(*) FROM workflow_nodes")
    node_count = cursor.fetchone()[0]
    print(f"📍 Nodi: {node_count}")
    
    if node_count > 0:
        cursor.execute("SELECT DISTINCT node_type FROM workflow_nodes")
        node_types = [row[0] for row in cursor.fetchall()]
        print(f"   Tipi unici: {len(node_types)}")
        for node_type in sorted(node_types):
            print(f"   - {node_type}")
    
    print()
    
    # Verifica connessioni
    if 'workflow_connections' in tables:
        cursor.execute("SELECT COUNT(*) FROM workflow_connections")
        connection_count = cursor.fetchone()[0]
        print(f"🔗 Connessioni: {connection_count}")
    
    conn.close()

def check_registry():
    """Verifica registry processori."""
    print("\n🔧 REGISTRY STATUS")
    print("=" * 40)
    
    try:
        from backend.engine.node_registry import NodeRegistry
        
        registry = NodeRegistry()
        
        # Ottieni lista processori disponibili
        available_processors = []
        test_processors = [
            "event_input_node", "file_parsing", "metadata_manager",
            "document_processor", "vector_store_operations", "event_logger",
            "input_user", "input_file", "llm_openai", "output_text"
        ]
        
        for proc in test_processors:
            if registry.get_processor(proc):
                available_processors.append(proc)
        
        print(f"⚙️ Processori testati: {len(available_processors)}/{len(test_processors)}")
        
        # Verifica processori reali
        real_processors = [
            "event_input_node", "file_parsing", "metadata_manager",
            "document_processor", "vector_store_operations", "event_logger"
        ]
        
        print("\n📍 Processori reali:")
        for proc in real_processors:
            processor = registry.get_processor(proc)
            if processor:
                proc_type = type(processor).__name__
                status = "✅" if "Simple" in proc_type else "⚠️"
                print(f"   {status} {proc}: {proc_type}")
            else:
                print(f"   ❌ {proc}: NON TROVATO")
        
        print("\n📋 Altri processori:")
        other_test_procs = ["input_user", "input_file", "llm_openai", "output_text", "text_processor"]
        for proc in other_test_procs:
            processor = registry.get_processor(proc)
            if processor:
                print(f"   ✅ {proc}: {type(processor).__name__}")
    
    except ImportError as e:
        print(f"❌ Errore import registry: {e}")
    except Exception as e:
        print(f"❌ Errore registry: {e}")

def check_workflow_files():
    """Verifica file JSON dei workflow."""
    print("\n📄 WORKFLOW FILES")
    print("=" * 40)
    
    workflow_dir = Path("PramaIA-PDK/workflows")
    if not workflow_dir.exists():
        print(f"❌ Directory non trovata: {workflow_dir}")
        return
    
    json_files = list(workflow_dir.glob("*.json"))
    print(f"📁 File JSON trovati: {len(json_files)}")
    
    for file in json_files:
        try:
            with open(file, 'r') as f:
                data = json.load(f)
            
            nodes = len(data.get("nodes", []))
            edges = len(data.get("edges", []))
            print(f"   ✅ {file.name}: {nodes} nodi, {edges} connessioni")
            
        except Exception as e:
            print(f"   ❌ {file.name}: Errore - {e}")

def main():
    """Controllo completo stato sistema."""
    print("🔍 CONTROLLO STATO SISTEMA WORKFLOW")
    print("=" * 50)
    
    check_database()
    check_registry()
    check_workflow_files()
    
    print("\n" + "=" * 50)
    print("✅ Controllo completato!")
    print("\n💡 NEXT STEPS:")
    print("   1. Se workflow=0: eseguire import_crud_workflows.py")
    print("   2. Se tutto OK: eseguire test_workflow_execution.py")
    print("   3. Verificare log per eventuali errori")

if __name__ == "__main__":
    main()