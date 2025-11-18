-- SQL per creare workflow DELETE e UPDATE nel database

-- ========================================
-- WORKFLOW DELETE
-- ========================================

-- Inserisci workflow DELETE
INSERT INTO workflows (workflow_id, name, description, is_active, created_by, created_at, updated_at)
VALUES (
    'pdf_document_delete_workflow',
    'Eliminazione Documenti PDF',
    'Workflow per eliminare documenti PDF dal VectorStore',
    1,
    'system',
    datetime('now'),
    datetime('now')
);

-- Ottieni l'ID del workflow appena creato (assumiamo sia l'ultimo inserito)
-- In SQLite questo sarà gestito tramite last_insert_rowid()

-- Nodi per workflow DELETE
INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position_x, position_y)
SELECT 
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow'),
    'Input Evento',
    'event_input_node',
    '{}',
    100,
    100;

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position_x, position_y)
SELECT 
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow'),
    'Elimina da VectorStore',
    'vector_store_operations',
    '{"operation": "delete", "collection_name": "documents"}',
    300,
    100;

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position_x, position_y)
SELECT 
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow'),
    'Logger Eliminazione',
    'event_logger',
    '{"event_type": "document_deleted", "log_level": "INFO"}',
    500,
    100;

-- Connessioni per workflow DELETE
INSERT INTO workflow_connections (connection_id, workflow_id, source_node_id, target_node_id, source_handle, target_handle)
SELECT 
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow'),
    (SELECT id FROM workflow_nodes WHERE workflow_id = (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow') AND node_type = 'event_input_node'),
    (SELECT id FROM workflow_nodes WHERE workflow_id = (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow') AND node_type = 'vector_store_operations'),
    'output',
    'input';

INSERT INTO workflow_connections (connection_id, workflow_id, source_node_id, target_node_id, source_handle, target_handle)
SELECT 
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow'),
    (SELECT id FROM workflow_nodes WHERE workflow_id = (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow') AND node_type = 'vector_store_operations'),
    (SELECT id FROM workflow_nodes WHERE workflow_id = (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow') AND node_type = 'event_logger'),
    'output',
    'input';

-- Trigger per workflow DELETE
INSERT INTO workflow_triggers (trigger_id, name, workflow_id, event_type, event_source, is_active, conditions, created_at)
SELECT 
    lower(hex(randomblob(16))),
    'Trigger Eliminazione PDF',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow'),
    'pdf_file_deleted',
    'pdf-monitor-event-source',
    1,
    '{}',
    datetime('now');

-- ========================================
-- WORKFLOW UPDATE
-- ========================================

-- Inserisci workflow UPDATE
INSERT INTO workflows (workflow_id, name, description, is_active, created_by, created_at, updated_at)
VALUES (
    'pdf_document_update_workflow',
    'Aggiornamento Documenti PDF',
    'Workflow per aggiornare documenti PDF nel VectorStore',
    1,
    'system',
    datetime('now'),
    datetime('now')
);

-- Nodi per workflow UPDATE (stesso pattern del workflow ADD ma con operation='update')
-- Nodo 1: Event Input
INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position_x, position_y)
SELECT 
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    'Input Evento',
    'event_input_node',
    '{}',
    100,
    100;

-- Nodo 2: File Parsing
INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position_x, position_y)
SELECT 
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    'Parsing PDF',
    'file_parsing',
    '{"extract_text": true, "extract_metadata": true}',
    250,
    100;

-- Nodo 3: Metadata Manager
INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position_x, position_y)
SELECT 
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    'Gestione Metadati',
    'metadata_manager',
    '{"generate_id": true, "extract_standard_fields": true}',
    400,
    100;

-- Nodo 4: Document Processor
INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position_x, position_y)
SELECT 
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    'Chunking Documento',
    'document_processor',
    '{"chunk_size": 1000, "chunk_overlap": 200}',
    550,
    100;

-- Nodo 5: VectorStore Update
INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position_x, position_y)
SELECT 
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    'Aggiorna VectorStore',
    'vector_store_operations',
    '{"operation": "update", "collection_name": "documents"}',
    700,
    100;

-- Nodo 6: Event Logger
INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position_x, position_y)
SELECT 
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    'Logger Aggiornamento',
    'event_logger',
    '{"event_type": "document_updated", "log_level": "INFO"}',
    850,
    100;

-- Trigger per workflow UPDATE
INSERT INTO workflow_triggers (trigger_id, name, workflow_id, event_type, event_source, is_active, conditions, created_at)
SELECT 
    lower(hex(randomblob(16))),
    'Trigger Aggiornamento PDF',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    'pdf_file_updated',
    'pdf-monitor-event-source',
    1,
    '{}',
    datetime('now');

-- Verifica
SELECT 'Workflows creati:' as info;
SELECT workflow_id, name FROM workflows WHERE workflow_id LIKE 'pdf_document_%_workflow';

SELECT 'Trigger creati:' as info;
SELECT name, event_type FROM workflow_triggers WHERE event_type IN ('pdf_file_deleted', 'pdf_file_updated');
