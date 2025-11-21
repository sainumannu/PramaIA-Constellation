#!/usr/bin/env python3

import asyncio
import json
from backend.db.database import SessionLocal
from backend.engine.workflow_engine import WorkflowEngine
from sqlalchemy.orm import joinedload
from backend.db.workflow_models import Workflow

async def test_workflow():
    """Test execution del workflow per vedere l'errore esatto"""
    
    with SessionLocal() as session:
        # Carichiamo il workflow con i suoi nodi
        workflow = session.query(Workflow).options(
            joinedload(Workflow.nodes), 
            joinedload(Workflow.connections)
        ).filter(Workflow.workflow_id == 'wf_92eded45afde').first()
        
        if not workflow:
            print("❌ Workflow non trovato")
            return
            
        print(f"✅ Workflow caricato: {workflow.name}")
        print(f"   Nodi: {len(workflow.nodes)}")
        print(f"   Connessioni: {len(workflow.connections)}")
        
        # Stampiamo i nodi per vedere i tipi
        print("\n=== NODI DEL WORKFLOW ===")
        for i, node in enumerate(workflow.nodes[:5]):
            print(f"{i+1}. {node.node_id} ({node.node_type}) - {node.name}")
        
        # Simuliamo l'input data dall'errore
        input_data = {
            "filename": "test_e2e_upload.pdf", 
            "file_size": 1678, 
            "content_type": "application/pdf", 
            "user_id": 1, 
            "is_public": False, 
            "metadata": {
                "source": "web-client-upload", 
                "timestamp": "2025-11-20T00:28:12.344431", 
                "user_id": "1", 
                "additional_data": {}
            }
        }
        
        # Proviamo ad eseguire il workflow
        engine = WorkflowEngine()
        execution_id = "test_execution"
        
        try:
            print("\n🔄 Tentativo esecuzione workflow...")
            # Passiamo la sessione corretta invece di "system"
            result = await engine.execute_workflow(workflow, input_data, execution_id, session)
            print("✅ Esecuzione completata!")
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ ERRORE DURANTE ESECUZIONE: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow())