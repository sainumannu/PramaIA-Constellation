-- ============================================================
-- RESET COMPLETO E RICOSTRUZIONE WORKFLOW (Schema corretto v2)
-- Usa id INTEGER autoincrement, non stringhe custom
-- ============================================================

-- 1. PULIZIA
DELETE FROM workflow_triggers;
DELETE FROM workflow_connections;
DELETE FROM workflow_nodes;
DELETE FROM workflows;

-- ============================================================
-- WORKFLOW 1: PDF DOCUMENT ADD
-- ============================================================

INSERT INTO workflows (workflow_id, name, description, created_by, is_active, created_at, updated_at)
VALUES (
    'pdf_document_add_workflow',
    'Gestione Nuovi Documenti PDF',
    'Workflow completo per aggiunta documenti PDF al VectorStore',
    'system',
    1,
    datetime('now'),
    datetime('now')
);

-- Nodi ADD (usa LAST_INSERT_ROWID per ottenere workflow.id)
INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
SELECT 
    'add_node_1',
    id,
    'Input Evento',
    'event_input_node',
    '{}',
    '{"x": 100, "y": 100}'
FROM workflows WHERE workflow_id = 'pdf_document_add_workflow';

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
SELECT 
    'add_node_2',
    id,
    'Parsing PDF',
    'file_parsing',
    '{"extract_text": true, "extract_metadata": true}',
    '{"x": 300, "y": 100}'
FROM workflows WHERE workflow_id = 'pdf_document_add_workflow';

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
SELECT 
    'add_node_3',
    id,
    'Gestione Metadati',
    'metadata_manager',
    '{"generate_id": true, "extract_standard_fields": true}',
    '{"x": 500, "y": 100}'
FROM workflows WHERE workflow_id = 'pdf_document_add_workflow';

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
SELECT 
    'add_node_4',
    id,
    'Chunking Documento',
    'document_processor',
    '{"chunk_size": 1000, "chunk_overlap": 200}',
    '{"x": 700, "y": 100}'
FROM workflows WHERE workflow_id = 'pdf_document_add_workflow';

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
SELECT 
    'add_node_5',
    id,
    'Aggiungi a VectorStore',
    'vector_store_operations',
    '{"operation": "add", "collection_name": "documents"}',
    '{"x": 900, "y": 100}'
FROM workflows WHERE workflow_id = 'pdf_document_add_workflow';

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
SELECT 
    'add_node_6',
    id,
    'Logger Eventi',
    'event_logger',
    '{"event_type": "document_added", "log_level": "INFO"}',
    '{"x": 1100, "y": 100}'
FROM workflows WHERE workflow_id = 'pdf_document_add_workflow';

-- Connessioni ADD (usa workflow_nodes.id integer, non node_id string)
INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
SELECT 
    w.id,
    n1.id,
    n2.id,
    'output',
    'input'
FROM workflows w
JOIN workflow_nodes n1 ON n1.workflow_id = w.id AND n1.node_id = 'add_node_1'
JOIN workflow_nodes n2 ON n2.workflow_id = w.id AND n2.node_id = 'add_node_2'
WHERE w.workflow_id = 'pdf_document_add_workflow';

INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
SELECT 
    w.id,
    n1.id,
    n2.id,
    'output',
    'input'
FROM workflows w
JOIN workflow_nodes n1 ON n1.workflow_id = w.id AND n1.node_id = 'add_node_2'
JOIN workflow_nodes n2 ON n2.workflow_id = w.id AND n2.node_id = 'add_node_3'
WHERE w.workflow_id = 'pdf_document_add_workflow';

INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
SELECT 
    w.id,
    n1.id,
    n2.id,
    'output',
    'input'
FROM workflows w
JOIN workflow_nodes n1 ON n1.workflow_id = w.id AND n1.node_id = 'add_node_3'
JOIN workflow_nodes n2 ON n2.workflow_id = w.id AND n2.node_id = 'add_node_4'
WHERE w.workflow_id = 'pdf_document_add_workflow';

INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
SELECT 
    w.id,
    n1.id,
    n2.id,
    'output',
    'input'
FROM workflows w
JOIN workflow_nodes n1 ON n1.workflow_id = w.id AND n1.node_id = 'add_node_4'
JOIN workflow_nodes n2 ON n2.workflow_id = w.id AND n2.node_id = 'add_node_5'
WHERE w.workflow_id = 'pdf_document_add_workflow';

INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
SELECT 
    w.id,
    n1.id,
    n2.id,
    'output',
    'input'
FROM workflows w
JOIN workflow_nodes n1 ON n1.workflow_id = w.id AND n1.node_id = 'add_node_5'
JOIN workflow_nodes n2 ON n2.workflow_id = w.id AND n2.node_id = 'add_node_6'
WHERE w.workflow_id = 'pdf_document_add_workflow';

-- Trigger ADD
INSERT INTO workflow_triggers (name, event_type, source, workflow_id, conditions, active, created_at)
SELECT
    'Trigger Aggiunta PDF',
    'pdf_file_added',
    'pdf-monitor-event-source',
    id,
    '{}',
    1,
    datetime('now')
FROM workflows WHERE workflow_id = 'pdf_document_add_workflow';

-- ============================================================
-- WORKFLOW 2: PDF DOCUMENT DELETE
-- ============================================================

INSERT INTO workflows (workflow_id, name, description, created_by, is_active, created_at, updated_at)
VALUES (
    'pdf_document_delete_workflow',
    'Eliminazione Documenti PDF',
    'Workflow per eliminare documenti PDF dal VectorStore',
    'system',
    1,
    datetime('now'),
    datetime('now')
);

-- Nodi DELETE
INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
SELECT 
    'delete_node_1',
    id,
    'Input Evento',
    'event_input_node',
    '{}',
    '{"x": 100, "y": 100}'
FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow';

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
SELECT 
    'delete_node_2',
    id,
    'Elimina da VectorStore',
    'vector_store_operations',
    '{"operation": "delete", "collection_name": "documents"}',
    '{"x": 300, "y": 100}'
FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow';

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
SELECT 
    'delete_node_3',
    id,
    'Logger Eliminazione',
    'event_logger',
    '{"event_type": "document_deleted", "log_level": "INFO"}',
    '{"x": 500, "y": 100}'
FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow';

-- Connessioni DELETE
INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
SELECT 
    w.id,
    n1.id,
    n2.id,
    'output',
    'input'
FROM workflows w
JOIN workflow_nodes n1 ON n1.workflow_id = w.id AND n1.node_id = 'delete_node_1'
JOIN workflow_nodes n2 ON n2.workflow_id = w.id AND n2.node_id = 'delete_node_2'
WHERE w.workflow_id = 'pdf_document_delete_workflow';

INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
SELECT 
    w.id,
    n1.id,
    n2.id,
    'output',
    'input'
FROM workflows w
JOIN workflow_nodes n1 ON n1.workflow_id = w.id AND n1.node_id = 'delete_node_2'
JOIN workflow_nodes n2 ON n2.workflow_id = w.id AND n2.node_id = 'delete_node_3'
WHERE w.workflow_id = 'pdf_document_delete_workflow';

-- Trigger DELETE
INSERT INTO workflow_triggers (name, event_type, source, workflow_id, conditions, active, created_at)
SELECT
    'Trigger Eliminazione PDF',
    'pdf_file_deleted',
    'pdf-monitor-event-source',
    id,
    '{}',
    1,
    datetime('now')
FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow';

-- ============================================================
-- WORKFLOW 3: PDF DOCUMENT UPDATE
-- ============================================================

INSERT INTO workflows (workflow_id, name, description, created_by, is_active, created_at, updated_at)
VALUES (
    'pdf_document_update_workflow',
    'Aggiornamento Documenti PDF',
    'Workflow per aggiornare documenti PDF nel VectorStore',
    'system',
    1,
    datetime('now'),
    datetime('now')
);

-- Nodi UPDATE
INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
SELECT 
    'update_node_1',
    id,
    'Input Evento',
    'event_input_node',
    '{}',
    '{"x": 100, "y": 100}'
FROM workflows WHERE workflow_id = 'pdf_document_update_workflow';

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
SELECT 
    'update_node_2',
    id,
    'Parsing PDF',
    'file_parsing',
    '{"extract_text": true, "extract_metadata": true}',
    '{"x": 300, "y": 100}'
FROM workflows WHERE workflow_id = 'pdf_document_update_workflow';

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
SELECT 
    'update_node_3',
    id,
    'Gestione Metadati',
    'metadata_manager',
    '{"generate_id": true, "extract_standard_fields": true}',
    '{"x": 500, "y": 100}'
FROM workflows WHERE workflow_id = 'pdf_document_update_workflow';

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
SELECT 
    'update_node_4',
    id,
    'Chunking Documento',
    'document_processor',
    '{"chunk_size": 1000, "chunk_overlap": 200}',
    '{"x": 700, "y": 100}'
FROM workflows WHERE workflow_id = 'pdf_document_update_workflow';

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
SELECT 
    'update_node_5',
    id,
    'Aggiorna VectorStore',
    'vector_store_operations',
    '{"operation": "update", "collection_name": "documents"}',
    '{"x": 900, "y": 100}'
FROM workflows WHERE workflow_id = 'pdf_document_update_workflow';

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
SELECT 
    'update_node_6',
    id,
    'Logger Aggiornamento',
    'event_logger',
    '{"event_type": "document_updated", "log_level": "INFO"}',
    '{"x": 1100, "y": 100}'
FROM workflows WHERE workflow_id = 'pdf_document_update_workflow';

-- Connessioni UPDATE
INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
SELECT 
    w.id,
    n1.id,
    n2.id,
    'output',
    'input'
FROM workflows w
JOIN workflow_nodes n1 ON n1.workflow_id = w.id AND n1.node_id = 'update_node_1'
JOIN workflow_nodes n2 ON n2.workflow_id = w.id AND n2.node_id = 'update_node_2'
WHERE w.workflow_id = 'pdf_document_update_workflow';

INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
SELECT 
    w.id,
    n1.id,
    n2.id,
    'output',
    'input'
FROM workflows w
JOIN workflow_nodes n1 ON n1.workflow_id = w.id AND n1.node_id = 'update_node_2'
JOIN workflow_nodes n2 ON n2.workflow_id = w.id AND n2.node_id = 'update_node_3'
WHERE w.workflow_id = 'pdf_document_update_workflow';

INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
SELECT 
    w.id,
    n1.id,
    n2.id,
    'output',
    'input'
FROM workflows w
JOIN workflow_nodes n1 ON n1.workflow_id = w.id AND n1.node_id = 'update_node_3'
JOIN workflow_nodes n2 ON n2.workflow_id = w.id AND n2.node_id = 'update_node_4'
WHERE w.workflow_id = 'pdf_document_update_workflow';

INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
SELECT 
    w.id,
    n1.id,
    n2.id,
    'output',
    'input'
FROM workflows w
JOIN workflow_nodes n1 ON n1.workflow_id = w.id AND n1.node_id = 'update_node_4'
JOIN workflow_nodes n2 ON n2.workflow_id = w.id AND n2.node_id = 'update_node_5'
WHERE w.workflow_id = 'pdf_document_update_workflow';

INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
SELECT 
    w.id,
    n1.id,
    n2.id,
    'output',
    'input'
FROM workflows w
JOIN workflow_nodes n1 ON n1.workflow_id = w.id AND n1.node_id = 'update_node_5'
JOIN workflow_nodes n2 ON n2.workflow_id = w.id AND n2.node_id = 'update_node_6'
WHERE w.workflow_id = 'pdf_document_update_workflow';

-- Trigger UPDATE
INSERT INTO workflow_triggers (name, event_type, source, workflow_id, conditions, active, created_at)
SELECT
    'Trigger Aggiornamento PDF',
    'pdf_file_updated',
    'pdf-monitor-event-source',
    id,
    '{}',
    1,
    datetime('now')
FROM workflows WHERE workflow_id = 'pdf_document_update_workflow';
