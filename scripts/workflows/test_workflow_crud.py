"""
Test diretto WorkflowCRUD per vedere se carica i nodi
"""
import sys
sys.path.insert(0, 'backend')

from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.crud.workflow_crud import WorkflowCRUD

db = SessionLocal()

try:
    workflow_id = "pdf_document_add_workflow"
    print(f"Caricamento workflow: {workflow_id}")
    
    workflow = WorkflowCRUD.get_workflow(db, workflow_id)
    
    if workflow:
        print(f"\n✅ Workflow trovato: {workflow.name}")
        print(f"   ID: {workflow.id}")
        print(f"   workflow_id: {workflow.workflow_id}")
        print(f"   Nodi: {len(workflow.nodes) if hasattr(workflow, 'nodes') else 'N/A'}")
        print(f"   Connessioni: {len(workflow.connections) if hasattr(workflow, 'connections') else 'N/A'}")
        
        if hasattr(workflow, 'nodes'):
            print(f"\n📋 Dettaglio nodi:")
            for node in workflow.nodes:
                print(f"   - [{node.id}] {node.node_id}: {node.name} (type={node.node_type})")
        else:
            print("\n❌ Attributo 'nodes' non trovato!")
            
        if hasattr(workflow, 'connections'):
            print(f"\n🔗 Dettaglio connessioni:")
            for conn in workflow.connections:
                print(f"   - {conn.from_node_id} -> {conn.to_node_id}")
        else:
            print("\n❌ Attributo 'connections' non trovato!")
    else:
        print(f"\n❌ Workflow non trovato!")
        
finally:
    db.close()
