# Database Schema - Advanced Trigger System

## 📊 Database Changes Overview

### Enhanced `workflow_triggers` Table

#### Schema Definition
```sql
CREATE TABLE workflow_triggers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    workflow_id VARCHAR(255) NOT NULL,
    source VARCHAR(255) NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    target_node_id VARCHAR(255),  -- NEW FIELD
    config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### Indexes
```sql
-- Performance indexes
CREATE INDEX idx_workflow_triggers_workflow_id 
ON workflow_triggers(workflow_id);

CREATE INDEX idx_workflow_triggers_source 
ON workflow_triggers(source);

CREATE INDEX idx_workflow_triggers_event_type 
ON workflow_triggers(event_type);

CREATE INDEX idx_workflow_triggers_target_node 
ON workflow_triggers(target_node_id);

CREATE INDEX idx_workflow_triggers_active 
ON workflow_triggers(is_active) WHERE is_active = true;

-- Composite indexes for common queries
CREATE INDEX idx_workflow_triggers_composite 
ON workflow_triggers(workflow_id, target_node_id) WHERE is_active = true;

CREATE INDEX idx_workflow_triggers_event_lookup 
ON workflow_triggers(source, event_type) WHERE is_active = true;
```

#### Constraints
```sql
-- Foreign key constraint (if workflows table exists)
ALTER TABLE workflow_triggers 
ADD CONSTRAINT fk_workflow_triggers_workflow_id 
FOREIGN KEY (workflow_id) REFERENCES workflows(id) 
ON DELETE CASCADE;

-- Check constraints
ALTER TABLE workflow_triggers 
ADD CONSTRAINT chk_trigger_name_not_empty 
CHECK (length(trim(name)) > 0);

ALTER TABLE workflow_triggers 
ADD CONSTRAINT chk_workflow_id_not_empty 
CHECK (length(trim(workflow_id)) > 0);

ALTER TABLE workflow_triggers 
ADD CONSTRAINT chk_source_not_empty 
CHECK (length(trim(source)) > 0);

ALTER TABLE workflow_triggers 
ADD CONSTRAINT chk_event_type_not_empty 
CHECK (length(trim(event_type)) > 0);
```

## 🔄 Migration Scripts

### Migration: Add Target Node Support

**File:** `backend/db/migrations/add_target_node_to_triggers.py`

```python
"""
Migration: Add target_node_id to workflow_triggers table
Date: 2025-08-05
Description: Adds support for specific node targeting in triggers
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    """Add target_node_id column to workflow_triggers table"""
    
    # Add the new column
    op.add_column('workflow_triggers', 
        sa.Column('target_node_id', sa.String(255), nullable=True)
    )
    
    # Add index for performance
    op.create_index('idx_workflow_triggers_target_node', 
                   'workflow_triggers', ['target_node_id'])
    
    # Add composite index for common queries
    op.create_index('idx_workflow_triggers_composite', 
                   'workflow_triggers', 
                   ['workflow_id', 'target_node_id'])
    
    # Update existing triggers with default behavior
    # (Optional: set target_node_id to first input node for existing triggers)
    connection = op.get_bind()
    connection.execute("""
        UPDATE workflow_triggers 
        SET target_node_id = NULL 
        WHERE target_node_id IS NULL
    """)

def downgrade():
    """Remove target_node_id column from workflow_triggers table"""
    
    # Drop indexes
    op.drop_index('idx_workflow_triggers_composite', 'workflow_triggers')
    op.drop_index('idx_workflow_triggers_target_node', 'workflow_triggers')
    
    # Drop column
    op.drop_column('workflow_triggers', 'target_node_id')
```

### Data Migration: Populate Target Nodes

**File:** `backend/db/migrations/populate_target_nodes.py`

```python
"""
Migration: Populate target_node_id for existing triggers
Date: 2025-08-05
Description: Automatically sets target_node_id for existing triggers
"""

import asyncio
from alembic import op
from sqlalchemy import text
from backend.engine.workflow_engine import WorkflowEngine
from backend.core.config import settings

def upgrade():
    """Populate target_node_id for existing triggers"""
    
    connection = op.get_bind()
    
    # Get all triggers without target_node_id
    result = connection.execute(text("""
        SELECT id, workflow_id 
        FROM workflow_triggers 
        WHERE target_node_id IS NULL
    """))
    
    workflow_engine = WorkflowEngine()
    
    for trigger in result:
        try:
            # Get input nodes for workflow
            input_nodes = asyncio.run(
                workflow_engine.get_input_nodes(trigger.workflow_id)
            )
            
            if input_nodes:
                # Use first available input node as default
                default_node_id = input_nodes[0]['node_id']
                
                connection.execute(text("""
                    UPDATE workflow_triggers 
                    SET target_node_id = :node_id 
                    WHERE id = :trigger_id
                """), {
                    'node_id': default_node_id,
                    'trigger_id': trigger.id
                })
                
                print(f"Updated trigger {trigger.id} with node {default_node_id}")
            else:
                print(f"No input nodes found for workflow {trigger.workflow_id}")
                
        except Exception as e:
            print(f"Error processing trigger {trigger.id}: {e}")

def downgrade():
    """Clear target_node_id for all triggers"""
    connection = op.get_bind()
    connection.execute(text("""
        UPDATE workflow_triggers 
        SET target_node_id = NULL
    """))
```

## 📈 Performance Optimizations

### Query Optimization

#### Common Query Patterns
```sql
-- Find triggers for specific workflow and event
SELECT t.*, w.name as workflow_name
FROM workflow_triggers t
LEFT JOIN workflows w ON t.workflow_id = w.id
WHERE t.workflow_id = $1 
  AND t.source = $2 
  AND t.event_type = $3 
  AND t.is_active = true;

-- Find triggers by target node
SELECT t.*, w.name as workflow_name
FROM workflow_triggers t
LEFT JOIN workflows w ON t.workflow_id = w.id
WHERE t.target_node_id = $1 
  AND t.is_active = true;

-- Count triggers per workflow
SELECT workflow_id, COUNT(*) as trigger_count
FROM workflow_triggers
WHERE is_active = true
GROUP BY workflow_id;

-- Find triggers with no target node (legacy)
SELECT id, name, workflow_id
FROM workflow_triggers
WHERE target_node_id IS NULL
  AND is_active = true;
```

#### Optimized Indexes
```sql
-- Partial indexes for active triggers only
CREATE INDEX idx_active_triggers_workflow 
ON workflow_triggers(workflow_id) 
WHERE is_active = true;

CREATE INDEX idx_active_triggers_event 
ON workflow_triggers(source, event_type) 
WHERE is_active = true;

-- Covering index for trigger lookup
CREATE INDEX idx_trigger_lookup_covering 
ON workflow_triggers(workflow_id, source, event_type) 
INCLUDE (target_node_id, config) 
WHERE is_active = true;

-- JSON index for config queries
CREATE INDEX idx_trigger_config_gin 
ON workflow_triggers USING GIN (config);
```

### Connection Pooling
```python
# Database connection pool configuration
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "pool_pre_ping": True
}
```

## 🔍 Data Validation

### Database-Level Validation
```sql
-- Trigger name validation
ALTER TABLE workflow_triggers 
ADD CONSTRAINT chk_trigger_name_valid 
CHECK (length(trim(name)) BETWEEN 3 AND 255);

-- JSON config validation
ALTER TABLE workflow_triggers 
ADD CONSTRAINT chk_config_is_object 
CHECK (jsonb_typeof(config) = 'object');

-- Event type format validation
ALTER TABLE workflow_triggers 
ADD CONSTRAINT chk_event_type_format 
CHECK (event_type ~ '^[a-z][a-z0-9_]*$');

-- Source format validation
ALTER TABLE workflow_triggers 
ADD CONSTRAINT chk_source_format 
CHECK (source ~ '^[a-z][a-z0-9-]*[a-z0-9]$');
```

### Application-Level Validation
```python
# SQLAlchemy model validation
from sqlalchemy import event
from sqlalchemy.orm import validates

class WorkflowTrigger(Base):
    __tablename__ = "workflow_triggers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    workflow_id = Column(String(255), nullable=False)
    target_node_id = Column(String(255), nullable=True)
    config = Column(JSON, default=dict)
    
    @validates('name')
    def validate_name(self, key, name):
        if not name or len(name.strip()) < 3:
            raise ValueError("Trigger name must be at least 3 characters")
        return name.strip()
    
    @validates('config')
    def validate_config(self, key, config):
        if not isinstance(config, dict):
            raise ValueError("Config must be a dictionary")
        return config
    
    @validates('target_node_id')
    def validate_target_node_id(self, key, node_id):
        if node_id and not re.match(r'^[a-zA-Z0-9_-]+$', node_id):
            raise ValueError("Invalid target node ID format")
        return node_id
```

## 🔧 Maintenance Procedures

### Regular Maintenance Tasks

#### Cleanup Orphaned Triggers
```sql
-- Find triggers with non-existent workflows
SELECT t.id, t.name, t.workflow_id
FROM workflow_triggers t
LEFT JOIN workflows w ON t.workflow_id = w.id
WHERE w.id IS NULL;

-- Archive or delete orphaned triggers
UPDATE workflow_triggers 
SET is_active = false, 
    updated_at = CURRENT_TIMESTAMP
WHERE workflow_id NOT IN (SELECT id FROM workflows);
```

#### Performance Monitoring
```sql
-- Monitor trigger usage
SELECT 
    source,
    event_type,
    COUNT(*) as trigger_count,
    COUNT(CASE WHEN is_active THEN 1 END) as active_count
FROM workflow_triggers
GROUP BY source, event_type
ORDER BY trigger_count DESC;

-- Find frequently accessed triggers
SELECT 
    t.id,
    t.name,
    t.workflow_id,
    t.target_node_id,
    COUNT(el.id) as execution_count
FROM workflow_triggers t
LEFT JOIN execution_logs el ON el.trigger_id = t.id
WHERE el.created_at > CURRENT_DATE - INTERVAL '30 days'
GROUP BY t.id, t.name, t.workflow_id, t.target_node_id
ORDER BY execution_count DESC
LIMIT 20;
```

#### Index Maintenance
```sql
-- Rebuild indexes for performance
REINDEX INDEX CONCURRENTLY idx_workflow_triggers_composite;
REINDEX INDEX CONCURRENTLY idx_workflow_triggers_target_node;

-- Analyze table statistics
ANALYZE workflow_triggers;

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename = 'workflow_triggers'
ORDER BY idx_scan DESC;
```

## 📊 Monitoring & Metrics

### Key Metrics to Track
```sql
-- Trigger performance metrics
CREATE VIEW trigger_metrics AS
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    source,
    event_type,
    COUNT(*) as trigger_count,
    COUNT(CASE WHEN is_active THEN 1 END) as active_count,
    AVG(CASE WHEN target_node_id IS NOT NULL THEN 1 ELSE 0 END) as node_targeting_ratio
FROM workflow_triggers
GROUP BY DATE_TRUNC('hour', created_at), source, event_type;

-- Node targeting usage
CREATE VIEW node_targeting_stats AS
SELECT 
    CASE 
        WHEN target_node_id IS NOT NULL THEN 'targeted'
        ELSE 'auto_detected'
    END as routing_type,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM workflow_triggers
WHERE is_active = true
GROUP BY (target_node_id IS NOT NULL);
```

### Health Checks
```sql
-- Database health check queries
SELECT 'workflow_triggers' as table_name,
       COUNT(*) as total_records,
       COUNT(CASE WHEN is_active THEN 1 END) as active_records,
       COUNT(CASE WHEN target_node_id IS NOT NULL THEN 1 END) as targeted_records,
       MIN(created_at) as oldest_record,
       MAX(updated_at) as last_update;

-- Index health check
SELECT 
    indexname,
    tablename,
    indexdef,
    CASE 
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 100 THEN 'LOW_USAGE'
        ELSE 'ACTIVE'
    END as usage_status
FROM pg_stat_user_indexes 
JOIN pg_indexes USING (indexname)
WHERE tablename = 'workflow_triggers';
```

---

**Versione Schema:** 2.0.0
**Database:** PostgreSQL 14+
**Migration Date:** 2025-08-05
**Maintainer:** PramaIA DB Team
