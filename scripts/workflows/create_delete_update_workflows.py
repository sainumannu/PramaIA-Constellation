"""
Script per creare workflow DELETE e UPDATE per gestione documenti PDF
"""
from backend.database import SessionLocal
from backend.models import Workflow, WorkflowNode, WorkflowConnection, WorkflowTrigger
import uuid
from datetime import datetime

def create_delete_workflow(db):
    """Crea workflow per eliminazione documenti"""
    
    # Verifica se esiste già
    existing = db.query(Workflow).filter(
        Workflow.workflow_id == 'pdf_document_delete_workflow'
    ).first()
    
    if existing:
        print(f"⚠️  Workflow DELETE già esistente (ID: {existing.id})")
        return existing
    
    # Crea workflow
    workflow = Workflow(
        workflow_id='pdf_document_delete_workflow',
        name='Eliminazione Documenti PDF',
        description='Workflow per eliminare documenti PDF dal VectorStore',
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(workflow)
    db.flush()
    
    print(f"✅ Workflow DELETE creato (ID: {workflow.id})")
    
    # Nodo 1: Event Input
    event_input = WorkflowNode(
        node_id=str(uuid.uuid4()),
        workflow_id=workflow.id,
        name='Input Evento',
        node_type='event_input_node',
        config={},
        position_x=100,
        position_y=100
    )
    db.add(event_input)
    db.flush()
    
    # Nodo 2: VectorStore Delete
    vectorstore_delete = WorkflowNode(
        node_id=str(uuid.uuid4()),
        workflow_id=workflow.id,
        name='Elimina da VectorStore',
        node_type='vector_store_operations',
        config={
            'operation': 'delete',
            'collection_name': 'documents'
        },
        position_x=300,
        position_y=100
    )
    db.add(vectorstore_delete)
    db.flush()
    
    # Nodo 3: Event Logger
    event_logger = WorkflowNode(
        node_id=str(uuid.uuid4()),
        workflow_id=workflow.id,
        name='Logger Eliminazione',
        node_type='event_logger',
        config={
            'event_type': 'document_deleted',
            'log_level': 'INFO'
        },
        position_x=500,
        position_y=100
    )
    db.add(event_logger)
    db.flush()
    
    # Connessioni
    conn1 = WorkflowConnection(
        connection_id=str(uuid.uuid4()),
        workflow_id=workflow.id,
        source_node_id=event_input.id,
        target_node_id=vectorstore_delete.id,
        source_handle='output',
        target_handle='input'
    )
    db.add(conn1)
    
    conn2 = WorkflowConnection(
        connection_id=str(uuid.uuid4()),
        workflow_id=workflow.id,
        source_node_id=vectorstore_delete.id,
        target_node_id=event_logger.id,
        source_handle='output',
        target_handle='input'
    )
    db.add(conn2)
    
    print(f"  ✅ 3 nodi creati")
    print(f"  ✅ 2 connessioni create")
    
    return workflow


def create_update_workflow(db):
    """Crea workflow per aggiornamento documenti"""
    
    # Verifica se esiste già
    existing = db.query(Workflow).filter(
        Workflow.workflow_id == 'pdf_document_update_workflow'
    ).first()
    
    if existing:
        print(f"⚠️  Workflow UPDATE già esistente (ID: {existing.id})")
        return existing
    
    # Crea workflow
    workflow = Workflow(
        workflow_id='pdf_document_update_workflow',
        name='Aggiornamento Documenti PDF',
        description='Workflow per aggiornare documenti PDF nel VectorStore',
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(workflow)
    db.flush()
    
    print(f"✅ Workflow UPDATE creato (ID: {workflow.id})")
    
    # Nodo 1: Event Input
    event_input = WorkflowNode(
        node_id=str(uuid.uuid4()),
        workflow_id=workflow.id,
        name='Input Evento',
        node_type='event_input_node',
        config={},
        position_x=100,
        position_y=100
    )
    db.add(event_input)
    db.flush()
    
    # Nodo 2: File Parsing
    file_parsing = WorkflowNode(
        node_id=str(uuid.uuid4()),
        workflow_id=workflow.id,
        name='Parsing PDF',
        node_type='file_parsing',
        config={
            'extract_text': True,
            'extract_metadata': True
        },
        position_x=250,
        position_y=100
    )
    db.add(file_parsing)
    db.flush()
    
    # Nodo 3: Metadata Manager
    metadata_manager = WorkflowNode(
        node_id=str(uuid.uuid4()),
        workflow_id=workflow.id,
        name='Gestione Metadati',
        node_type='metadata_manager',
        config={
            'generate_id': True,
            'extract_standard_fields': True
        },
        position_x=400,
        position_y=100
    )
    db.add(metadata_manager)
    db.flush()
    
    # Nodo 4: Document Processor
    document_processor = WorkflowNode(
        node_id=str(uuid.uuid4()),
        workflow_id=workflow.id,
        name='Chunking Documento',
        node_type='document_processor',
        config={
            'chunk_size': 1000,
            'chunk_overlap': 200
        },
        position_x=550,
        position_y=100
    )
    db.add(document_processor)
    db.flush()
    
    # Nodo 5: VectorStore Update
    vectorstore_update = WorkflowNode(
        node_id=str(uuid.uuid4()),
        workflow_id=workflow.id,
        name='Aggiorna VectorStore',
        node_type='vector_store_operations',
        config={
            'operation': 'update',
            'collection_name': 'documents'
        },
        position_x=700,
        position_y=100
    )
    db.add(vectorstore_update)
    db.flush()
    
    # Nodo 6: Event Logger
    event_logger = WorkflowNode(
        node_id=str(uuid.uuid4()),
        workflow_id=workflow.id,
        name='Logger Aggiornamento',
        node_type='event_logger',
        config={
            'event_type': 'document_updated',
            'log_level': 'INFO'
        },
        position_x=850,
        position_y=100
    )
    db.add(event_logger)
    db.flush()
    
    # Connessioni
    connections = [
        (event_input.id, file_parsing.id),
        (file_parsing.id, metadata_manager.id),
        (metadata_manager.id, document_processor.id),
        (document_processor.id, vectorstore_update.id),
        (vectorstore_update.id, event_logger.id)
    ]
    
    for source_id, target_id in connections:
        conn = WorkflowConnection(
            connection_id=str(uuid.uuid4()),
            workflow_id=workflow.id,
            source_node_id=source_id,
            target_node_id=target_id,
            source_handle='output',
            target_handle='input'
        )
        db.add(conn)
    
    print(f"  ✅ 6 nodi creati")
    print(f"  ✅ 5 connessioni create")
    
    return workflow


def create_triggers(db, delete_workflow, update_workflow):
    """Crea trigger per DELETE e UPDATE"""
    
    # Trigger DELETE
    existing_delete = db.query(WorkflowTrigger).filter(
        WorkflowTrigger.workflow_id == delete_workflow.id
    ).first()
    
    if not existing_delete:
        trigger_delete = WorkflowTrigger(
            trigger_id=str(uuid.uuid4()),
            name='Trigger Eliminazione PDF',
            workflow_id=delete_workflow.id,
            event_type='pdf_file_deleted',
            event_source='pdf-monitor-event-source',
            is_active=True,
            conditions={},
            created_at=datetime.utcnow()
        )
        db.add(trigger_delete)
        print(f"✅ Trigger DELETE creato: {trigger_delete.name}")
    else:
        print(f"⚠️  Trigger DELETE già esistente")
    
    # Trigger UPDATE
    existing_update = db.query(WorkflowTrigger).filter(
        WorkflowTrigger.workflow_id == update_workflow.id
    ).first()
    
    if not existing_update:
        trigger_update = WorkflowTrigger(
            trigger_id=str(uuid.uuid4()),
            name='Trigger Aggiornamento PDF',
            workflow_id=update_workflow.id,
            event_type='pdf_file_updated',
            event_source='pdf-monitor-event-source',
            is_active=True,
            conditions={},
            created_at=datetime.utcnow()
        )
        db.add(trigger_update)
        print(f"✅ Trigger UPDATE creato: {trigger_update.name}")
    else:
        print(f"⚠️  Trigger UPDATE già esistente")


def main():
    print("="*60)
    print("  CREAZIONE WORKFLOW DELETE E UPDATE")
    print("="*60)
    print()
    
    db = SessionLocal()
    
    try:
        # Crea workflow
        print("📝 Creazione workflow...")
        delete_wf = create_delete_workflow(db)
        print()
        update_wf = create_update_workflow(db)
        print()
        
        # Crea trigger
        print("🎯 Creazione trigger...")
        create_triggers(db, delete_wf, update_wf)
        print()
        
        # Commit
        db.commit()
        print("✅ Tutte le modifiche salvate nel database")
        
        # Verifica
        print()
        print("="*60)
        print("  VERIFICA")
        print("="*60)
        total_workflows = db.query(Workflow).count()
        total_triggers = db.query(WorkflowTrigger).count()
        print(f"Workflow totali nel database: {total_workflows}")
        print(f"Trigger totali nel database: {total_triggers}")
        
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print()
    print("="*60)
    print()


if __name__ == '__main__':
    main()
