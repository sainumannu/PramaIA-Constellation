-- Schema per la tabella workflow_triggers
CREATE TABLE IF NOT EXISTS workflow_triggers (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(100) NOT NULL,
    workflow_id VARCHAR(255) NOT NULL,
    conditions TEXT DEFAULT '{}',
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indici per migliorare le prestazioni delle query comuni
CREATE INDEX IF NOT EXISTS idx_trigger_event_source ON workflow_triggers(event_type, source);
CREATE INDEX IF NOT EXISTS idx_trigger_active ON workflow_triggers(active);
CREATE INDEX IF NOT EXISTS idx_trigger_workflow_id ON workflow_triggers(workflow_id);

-- Commenti per documentare la tabella
COMMENT ON TABLE workflow_triggers IS 'Contiene le associazioni tra eventi e workflow';
COMMENT ON COLUMN workflow_triggers.id IS 'ID univoco del trigger';
COMMENT ON COLUMN workflow_triggers.name IS 'Nome descrittivo del trigger';
COMMENT ON COLUMN workflow_triggers.event_type IS 'Tipo di evento (es. pdf_upload, file_created)';
COMMENT ON COLUMN workflow_triggers.source IS 'Sorgente dell''evento (es. pdf-monitor, scheduler)';
COMMENT ON COLUMN workflow_triggers.workflow_id IS 'ID del workflow da eseguire';
COMMENT ON COLUMN workflow_triggers.conditions IS 'Condizioni opzionali in formato JSON per filtrare gli eventi';
COMMENT ON COLUMN workflow_triggers.active IS 'Stato attivo/inattivo del trigger';
