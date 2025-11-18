-- ============================================================
-- RESET COMPLETO E RICOSTRUZIONE WORKFLOW
-- ============================================================

-- 1. PULIZIA: Elimina tutti i trigger esistenti
DELETE FROM workflow_triggers;

-- 2. PULIZIA: Elimina tutte le connessioni esistenti
DELETE FROM workflow_connections;

-- 3. PULIZIA: Elimina tutti i nodi esistenti
DELETE FROM workflow_nodes;

-- 4. PULIZIA: Elimina tutti i workflow esistenti
DELETE FROM workflows;

-- Reset autoincrement
DELETE FROM sqlite_sequence WHERE name='workflows';
DELETE FROM sqlite_sequence WHERE name='workflow_nodes';
DELETE FROM sqlite_sequence WHERE name='workflow_connections';
DELETE FROM sqlite_sequence WHERE name='workflow_triggers';

-- ============================================================
-- WORKFLOW 1: PDF DOCUMENT ADD (Aggiunta documenti)
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

-- Nodi workflow ADD
INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config)
VALUES (
    'add_node_1',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    'Input Evento',
    'event_input_node',
    '{}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config)
VALUES (
    'add_node_2',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    'Parsing PDF',
    'file_parsing',
    '{"extract_text": true, "extract_metadata": true, "extract_images": false, "ocr_enabled": false}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config)
VALUES (
    'add_node_3',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    'Gestione Metadati',
    'metadata_manager',
    '{"generate_id": true, "extract_standard_fields": true, "normalize_dates": true}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config)
VALUES (
    'add_node_4',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    'Chunking Documento',
    'document_processor',
    '{"chunk_size": 1000, "chunk_overlap": 200, "normalize_text": true}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config)
VALUES (
    'add_node_5',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    'Aggiungi a VectorStore',
    'vector_store_operations',
    '{"operation": "add", "collection_name": "documents"}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config)
VALUES (
    'add_node_6',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    'Logger Eventi',
    'event_logger',
    '{"event_type": "document_added", "log_level": "INFO", "include_metadata": true}'
);

-- Connessioni workflow ADD
INSERT INTO workflow_connections (connection_id, workflow_id, source_node_id, target_node_id, source_handle, target_handle)
VALUES (
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'add_node_1'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'add_node_2'),
    'output',
    'input'
);

INSERT INTO workflow_connections (connection_id, workflow_id, source_node_id, target_node_id, source_handle, target_handle)
VALUES (
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'add_node_2'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'add_node_3'),
    'output',
    'input'
);

INSERT INTO workflow_connections (connection_id, workflow_id, source_node_id, target_node_id, source_handle, target_handle)
VALUES (
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'add_node_3'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'add_node_4'),
    'output',
    'input'
);

INSERT INTO workflow_connections (connection_id, workflow_id, source_node_id, target_node_id, source_handle, target_handle)
VALUES (
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'add_node_4'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'add_node_5'),
    'output',
    'input'
);

INSERT INTO workflow_connections (connection_id, workflow_id, source_node_id, target_node_id, source_handle, target_handle)
VALUES (
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_add_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'add_node_5'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'add_node_6'),
    'output',
    'input'
);

-- Trigger workflow ADD
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
-- WORKFLOW 2: PDF DOCUMENT DELETE (Eliminazione documenti)
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

-- Nodi workflow DELETE
INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config)
VALUES (
    'delete_node_1',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow'),
    'Input Evento',
    'event_input_node',
    '{}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config)
VALUES (
    'delete_node_2',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow'),
    'Elimina da VectorStore',
    'vector_store_operations',
    '{"operation": "delete", "collection_name": "documents"}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config)
VALUES (
    'delete_node_3',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow'),
    'Logger Eliminazione',
    'event_logger',
    '{"event_type": "document_deleted", "log_level": "INFO", "include_metadata": true}'
);

-- Connessioni workflow DELETE
INSERT INTO workflow_connections (connection_id, workflow_id, source_node_id, target_node_id, source_handle, target_handle)
VALUES (
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'delete_node_1'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'delete_node_2'),
    'output',
    'input'
);

INSERT INTO workflow_connections (connection_id, workflow_id, source_node_id, target_node_id, source_handle, target_handle)
VALUES (
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_delete_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'delete_node_2'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'delete_node_3'),
    'output',
    'input'
);

-- Trigger workflow DELETE
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
-- WORKFLOW 3: PDF DOCUMENT UPDATE (Aggiornamento documenti)
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

-- Nodi workflow UPDATE (simile ad ADD ma con operation=update)
INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config)
VALUES (
    'update_node_1',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    'Input Evento',
    'event_input_node',
    '{}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config)
VALUES (
    'update_node_2',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    'Parsing PDF',
    'file_parsing',
    '{"extract_text": true, "extract_metadata": true, "extract_images": false, "ocr_enabled": false}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config)
VALUES (
    'update_node_3',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    'Gestione Metadati',
    'metadata_manager',
    '{"generate_id": true, "extract_standard_fields": true, "normalize_dates": true}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config)
VALUES (
    'update_node_4',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    'Chunking Documento',
    'document_processor',
    '{"chunk_size": 1000, "chunk_overlap": 200, "normalize_text": true}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config)
VALUES (
    'update_node_5',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    'Aggiorna VectorStore',
    'vector_store_operations',
    '{"operation": "update", "collection_name": "documents"}'
);

INSERT INTO workflow_nodes (node_id, workflow_id, name, node_type, config)
VALUES (
    'update_node_6',
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    'Logger Aggiornamento',
    'event_logger',
    '{"event_type": "document_updated", "log_level": "INFO", "include_metadata": true}'
);

-- Connessioni workflow UPDATE
INSERT INTO workflow_connections (connection_id, workflow_id, source_node_id, target_node_id, source_handle, target_handle)
VALUES (
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'update_node_1'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'update_node_2'),
    'output',
    'input'
);

INSERT INTO workflow_connections (connection_id, workflow_id, source_node_id, target_node_id, source_handle, target_handle)
VALUES (
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'update_node_2'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'update_node_3'),
    'output',
    'input'
);

INSERT INTO workflow_connections (connection_id, workflow_id, source_node_id, target_node_id, source_handle, target_handle)
VALUES (
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'update_node_3'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'update_node_4'),
    'output',
    'input'
);

INSERT INTO workflow_connections (connection_id, workflow_id, source_node_id, target_node_id, source_handle, target_handle)
VALUES (
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'update_node_4'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'update_node_5'),
    'output',
    'input'
);

INSERT INTO workflow_connections (connection_id, workflow_id, source_node_id, target_node_id, source_handle, target_handle)
VALUES (
    lower(hex(randomblob(16))),
    (SELECT id FROM workflows WHERE workflow_id = 'pdf_document_update_workflow'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'update_node_5'),
    (SELECT id FROM workflow_nodes WHERE node_id = 'update_node_6'),
    'output',
    'input'
);

-- Trigger workflow UPDATE
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

-- ============================================================
-- VERIFICA FINALE
-- ============================================================

SELECT '=== WORKFLOWS CREATI ===' as info;
SELECT workflow_id, name, 
       (SELECT COUNT(*) FROM workflow_nodes WHERE workflow_nodes.workflow_id = workflows.id) as nodi
FROM workflows;

SELECT '' as spacer;

SELECT '=== TRIGGER CREATI ===' as info;
SELECT name, event_type, source, active
FROM workflow_triggers
ORDER BY event_type;
