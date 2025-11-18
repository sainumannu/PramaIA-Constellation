-- ============================================================
-- RESET COMPLETO E RICOSTRUZIONE WORKFLOW (Schema corretto)
-- ============================================================

-- 1. PULIZIA: Elimina in ordine per rispettare foreign keys
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

-- Nodi ADD
INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
VALUES (
    'add_node_1',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    'Input Evento',
    'event_input_node',
    '{}',
    '{"x": 100, "y": 100}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
VALUES (
    'add_node_2',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    'Parsing PDF',
    'file_parsing',
    '{"extract_text": true, "extract_metadata": true}',
    '{"x": 300, "y": 100}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
VALUES (
    'add_node_3',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    'Gestione Metadati',
    'metadata_manager',
    '{"generate_id": true, "extract_standard_fields": true}',
    '{"x": 500, "y": 100}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
VALUES (
    'add_node_4',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    'Chunking Documento',
    'document_processor',
    '{"chunk_size": 1000, "chunk_overlap": 200}',
    '{"x": 700, "y": 100}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
VALUES (
    'add_node_5',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    'Aggiungi a VectorStore',
    'vector_store_operations',
    '{"operation": "add", "collection_name": "documents"}',
    '{"x": 900, "y": 100}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
VALUES (
    'add_node_6',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    'Logger Eventi',
    'event_logger',
    '{"event_type": "document_added", "log_level": "INFO"}',
    '{"x": 1100, "y": 100}'
);

-- Connessioni ADD
INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
VALUES (
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'add_node_1'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'add_node_2'),
    'output',
    'input'
);

INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
VALUES (
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'add_node_2'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'add_node_3'),
    'output',
    'input'
);

INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
VALUES (
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'add_node_3'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'add_node_4'),
    'output',
    'input'
);

INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
VALUES (
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'add_node_4'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'add_node_5'),
    'output',
    'input'
);

INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
VALUES (
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'add_node_5'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'add_node_6'),
    'output',
    'input'
);

-- Trigger ADD
INSERT INTO workflow_triggers (name, event_type, source, workflow_id, conditions, active, created_at)
VALUES (
    'Trigger Aggiunta PDF',
    'pdf_file_added',
    'pdf-monitor-event-source',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    '{}',
    1,
    datetime('now')
);

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
VALUES (
    'delete_node_1',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow'),
    'Input Evento',
    'event_input_node',
    '{}',
    '{"x": 100, "y": 100}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
VALUES (
    'delete_node_2',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow'),
    'Elimina da VectorStore',
    'vector_store_operations',
    '{"operation": "delete", "collection_name": "documents"}',
    '{"x": 300, "y": 100}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
VALUES (
    'delete_node_3',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow'),
    'Logger Eliminazione',
    'event_logger',
    '{"event_type": "document_deleted", "log_level": "INFO"}',
    '{"x": 500, "y": 100}'
);

-- Connessioni DELETE
INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
VALUES (
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'delete_node_1'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'delete_node_2'),
    'output',
    'input'
);

INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
VALUES (
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'delete_node_2'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'delete_node_3'),
    'output',
    'input'
);

-- Trigger DELETE
INSERT INTO workflow_triggers (name, event_type, source, workflow_id, conditions, active, created_at)
VALUES (
    'Trigger Eliminazione PDF',
    'pdf_file_deleted',
    'pdf-monitor-event-source',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow'),
    '{}',
    1,
    datetime('now')
);

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
VALUES (
    'update_node_1',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    'Input Evento',
    'event_input_node',
    '{}',
    '{"x": 100, "y": 100}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
VALUES (
    'update_node_2',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    'Parsing PDF',
    'file_parsing',
    '{"extract_text": true, "extract_metadata": true}',
    '{"x": 300, "y": 100}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
VALUES (
    'update_node_3',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    'Gestione Metadati',
    'metadata_manager',
    '{"generate_id": true, "extract_standard_fields": true}',
    '{"x": 500, "y": 100}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
VALUES (
    'update_node_4',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    'Chunking Documento',
    'document_processor',
    '{"chunk_size": 1000, "chunk_overlap": 200}',
    '{"x": 700, "y": 100}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
VALUES (
    'update_node_5',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    'Aggiorna VectorStore',
    'vector_store_operations',
    '{"operation": "update", "collection_name": "documents"}',
    '{"x": 900, "y": 100}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config, position)
VALUES (
    'update_node_6',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    'Logger Aggiornamento',
    'event_logger',
    '{"event_type": "document_updated", "log_level": "INFO"}',
    '{"x": 1100, "y": 100}'
);

-- Connessioni UPDATE
INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
VALUES (
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'update_node_1'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'update_node_2'),
    'output',
    'input'
);

INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
VALUES (
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'update_node_2'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'update_node_3'),
    'output',
    'input'
);

INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
VALUES (
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'update_node_3'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'update_node_4'),
    'output',
    'input'
);

INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
VALUES (
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'update_node_4'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'update_node_5'),
    'output',
    'input'
);

INSERT INTO workflow_connections (workflow_id, from_node_id, to_node_id, from_port, to_port)
VALUES (
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'update_node_5'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'update_node_6'),
    'output',
    'input'
);

-- Trigger UPDATE
INSERT INTO workflow_triggers (name, event_type, source, workflow_id, conditions, active, created_at)
VALUES (
    'Trigger Aggiornamento PDF',
    'pdf_file_updated',
    'pdf-monitor-event-source',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    '{}',
    1,
    datetime('now')
);
