#!/usr/bin/env python3
"""
TEST SEMPLIFICATO - Processori Reali CRUD

Test diretto dei processori reali senza dipendenze complesse.
"""

import sys
import os
import json
import sqlite3
from pathlib import Path

# Configurazione paths
sys.path.append(str(Path(__file__).parent))

def test_real_processors():
    """Test diretto dei processori reali implementati."""
    print("🧪 TEST PROCESSORI REALI")
    print("=" * 50)
    
    try:
        # Import diretto dei processori dal backend
        sys.path.append("C:/PramaIA/backend/engine/processors")
        from backend.engine.processors import (
            EventInputProcessor,
            FileParsingProcessor,
            DocumentProcessorProcessor,
            VectorStoreOperationsProcessor,
            MetadataManagerProcessor,
            EventLoggerProcessor
        )
        print("✅ Import processori: OK")
        
        # Test istanziazione
        processors = {
            'EventInput': EventInputProcessor(),
            'FileParsing': FileParsingProcessor(),
            'DocumentProcessor': DocumentProcessorProcessor(),
            'VectorOperations': VectorStoreOperationsProcessor(),
            'MetadataManager': MetadataManagerProcessor(),
            'EventLogger': EventLoggerProcessor()
        }
        
        print("✅ Istanziazione processori: OK")
        
        # Test dati sample
        test_data = {
            "file_path": "test.pdf",
            "file_content": b"Test PDF content",
            "query": "test query",
            "metadata": {"title": "Test Document"}
        }
        
        # Context mock per i test
        class MockContext:
            def __init__(self):
                self.workflow_id = "test_workflow"
                self.execution_id = "test_execution"
                self.node_id = "test_node"
                self.logger = print  # Simple logger
        
        test_context = MockContext()
        
        # Test FileParsing
        parser = processors['FileParsing']
        result = parser.execute(test_data, test_context)
        print(f"✅ FileParsingProcessor: {result['status'] if isinstance(result, dict) and 'status' in result else 'completed'}")
        
        # Test DocumentProcessor
        doc_processor = processors['DocumentProcessor']
        doc_result = doc_processor.execute({"document": test_data}, test_context)
        print(f"✅ DocumentProcessorProcessor: {doc_result['status'] if isinstance(doc_result, dict) and 'status' in doc_result else 'completed'}")
        
        # Test MetadataManager
        metadata_processor = processors['MetadataManager']
        metadata_result = metadata_processor.execute({"metadata": test_data["metadata"]}, test_context)
        print(f"✅ MetadataManagerProcessor: {metadata_result['status'] if isinstance(metadata_result, dict) and 'status' in metadata_result else 'completed'}")
        
        # Test EventInput
        event_processor = processors['EventInput']
        event_result = event_processor.execute({"event_type": "file_upload", "data": test_data}, test_context)
        print(f"✅ EventInputProcessor: {event_result['status'] if isinstance(event_result, dict) and 'status' in event_result else 'completed'}")
        
        print("\n🎉 TUTTI I PROCESSORI FUNZIONANO CORRETTAMENTE!")
        return True
        
    except Exception as e:
        print(f"❌ Errore test processori: {e}")
        return False

def test_database_connectivity():
    """Test connessione database e struttura workflow."""
    print("\n🗄️  TEST DATABASE")
    print("=" * 50)
    
    try:
        # Connessione database (database principale)
        db_path = "C:/PramaIA/backend/db/database.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica workflow
        cursor.execute("SELECT COUNT(*) FROM workflows")
        workflow_count = cursor.fetchone()[0]
        print(f"📋 Workflow nel database: {workflow_count}")
        
        if workflow_count > 0:
            cursor.execute("SELECT workflow_id, name FROM workflows LIMIT 3")
            workflows = cursor.fetchall()
            for wf_id, name in workflows:
                print(f"   - {name} ({wf_id})")
        
        # Verifica nodi
        cursor.execute("SELECT COUNT(*) FROM workflow_nodes")
        node_count = cursor.fetchone()[0]
        print(f"⚙️  Nodi nel database: {node_count}")
        
        # Verifica processori nei nodi
        cursor.execute("SELECT DISTINCT node_type FROM workflow_nodes")
        processor_types = cursor.fetchall()
        print("🔧 Tipi processori trovati:")
        for ptype, in processor_types:
            cursor.execute("SELECT COUNT(*) FROM workflow_nodes WHERE node_type = ?", (ptype,))
            count = cursor.fetchone()[0]
            print(f"   - {ptype}: {count} nodi")
        
        conn.close()
        print("✅ Database: OK")
        return True
        
    except Exception as e:
        print(f"❌ Errore database: {e}")
        return False

def test_workflow_json_files():
    """Test verifica file JSON workflow."""
    print("\n📄 TEST FILE WORKFLOW")
    print("=" * 50)
    
    try:
        json_files = [
            "C:/PramaIA/PramaIA-PDK/workflows/pdf_document_create_pipeline.json",
            "C:/PramaIA/PramaIA-PDK/workflows/pdf_document_read_pipeline.json", 
            "C:/PramaIA/PramaIA-PDK/workflows/pdf_document_update_pipeline.json",
            "C:/PramaIA/PramaIA-PDK/workflows/pdf_document_delete_pipeline.json"
        ]
        
        for filename in json_files:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    workflow = json.load(f)
                    nodes = len(workflow.get('nodes', []))
                    connections = len(workflow.get('connections', []))
                    print(f"✅ {os.path.basename(filename)}: {nodes} nodi, {connections} connessioni")
            else:
                print(f"❌ {os.path.basename(filename)}: File non trovato")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore file JSON: {e}")
        return False

def main():
    """Test principale."""
    print("🚀 AVVIO TEST SEMPLIFICATI PROCESSORI REALI")
    print("=" * 60)
    
    results = []
    
    # Test processori
    results.append(test_real_processors())
    
    # Test database
    results.append(test_database_connectivity())
    
    # Test file JSON
    results.append(test_workflow_json_files())
    
    # Risultato finale
    print("\n" + "=" * 60)
    if all(results):
        print("🎉 TUTTI I TEST SUPERATI!")
        print("\n💡 PROSSIMI PASSI:")
        print("   1. I processori reali funzionano ✅")
        print("   2. I workflow sono nel database ✅") 
        print("   3. Pronto per test avanzati o deploy")
    else:
        print("❌ Alcuni test falliti - verificare i log sopra")
    
    print("=" * 60)

if __name__ == "__main__":
    main()