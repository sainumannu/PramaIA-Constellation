#!/usr/bin/env python3

import sys
sys.path.append('.')

from backend.db.database import SessionLocal
from backend.crud.workflow_crud import WorkflowCRUD
from backend.engine.workflow_engine import WorkflowEngine

def test_workflow_engine():
    """Testa il metodo _find_input_nodes del WorkflowEngine."""
    
    db = SessionLocal()
    try:
        workflow_id = 'wf_055bf5029833'
        
        print(f"Testing WorkflowEngine._find_input_nodes() per workflow: {workflow_id}")
        
        # Ottieni il workflow
        workflow = WorkflowCRUD.get_workflow(db, workflow_id)
        if not workflow:
            print(f'❌ Workflow {workflow_id} non trovato')
            return False
        
        print(f'✅ Workflow trovato: {workflow.name}')
        print(f'   Nodi: {len(workflow.nodes)}')
        print(f'   Connessioni: {len(workflow.connections)}')
        
        # Usa WorkflowEngine per trovare nodi di input
        engine = WorkflowEngine()
        input_nodes = engine._find_input_nodes(workflow)
        
        print(f'')
        print(f'🔍 Risultato _find_input_nodes():')
        print(f'   Nodi di input trovati: {len(input_nodes)}')
        
        if input_nodes:
            for idx, node in enumerate(input_nodes, 1):
                print(f'   {idx}. {node.get("node_id", "N/A")}: {node.get("name", "N/A")} ({node.get("node_type", "N/A")})')
                if node.get("input_ports"):
                    print(f'      Input Ports: {len(node["input_ports"])}')
        else:
            print('   ⚠️ Nessun nodo di input trovato!')
            
        return True
        
    except Exception as e:
        print(f'❌ Errore: {e}')
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

if __name__ == '__main__':
    test_workflow_engine()