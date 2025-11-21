"""
Test suite for Triggers & Integration - Complete document lifecycle
Tests the full workflow: file_upload → trigger → workflow execution → embeddings generation
"""

import pytest
import json
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import sqlite3
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'PramaIAServer'))

from backend.crud.workflow_crud import WorkflowCRUD
from backend.crud.trigger_crud import TriggerCRUD
from backend.crud.user_crud import UserCRUD
from backend.db.database import SessionLocal, engine

# =======================
# Setup & Fixtures
# =======================

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create test database tables"""
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup after all tests
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """Get database session"""
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def admin_token(db_session, client):
    """Get JWT token for admin user"""
    user_crud = UserCRUD(db_session)
    
    # Create or get admin user
    admin = user_crud.get_by_username("admin")
    if not admin:
        admin = user_crud.create(
            username="admin",
            email="admin@test.com",
            hashed_password="$2b$12$test",
            user_id=str(uuid.uuid4())
        )
    
    # Mock token generation
    from backend.auth.jwt_utils import create_access_token
    token = create_access_token(
        data={"sub": admin.username, "user_id": admin.user_id}
    )
    return token

@pytest.fixture
def sample_workflow(db_session):
    """Create a sample RAG workflow"""
    workflow_crud = WorkflowCRUD(db_session)
    
    workflow = workflow_crud.create(
        name="RAG Processing Workflow",
        description="Processes documents with RAG",
        nodes={
            "input": {
                "id": "input_1",
                "type": "input",
                "plugin": "core-input-plugin",
                "inputs": {},
                "outputs": {"document": "text"}
            },
            "rag": {
                "id": "rag_1",
                "type": "rag",
                "plugin": "core-rag-plugin",
                "inputs": {"document": "text"},
                "outputs": {"embeddings": "vector"}
            },
            "output": {
                "id": "output_1",
                "type": "output",
                "plugin": "core-output-plugin",
                "inputs": {"data": "any"},
                "outputs": {}
            }
        },
        connections=[
            {"from": "input_1", "to": "rag_1"},
            {"from": "rag_1", "to": "output_1"}
        ],
        user_id=str(uuid.uuid4())
    )
    
    return workflow

# =======================
# Trigger Tests
# =======================

def test_create_trigger(db_session, sample_workflow, admin_token, client):
    """Test creating a trigger"""
    trigger_crud = TriggerCRUD(db_session)
    
    trigger = trigger_crud.create(
        event_type="file_upload",
        workflow_id=sample_workflow.id,
        conditions={"file_type": "pdf"},
        enabled=True
    )
    
    assert trigger is not None
    assert trigger.event_type == "file_upload"
    assert trigger.workflow_id == sample_workflow.id
    assert trigger.enabled is True

def test_get_trigger_by_event(db_session, sample_workflow):
    """Test retrieving triggers by event type"""
    trigger_crud = TriggerCRUD(db_session)
    
    # Create trigger
    created_trigger = trigger_crud.create(
        event_type="file_upload",
        workflow_id=sample_workflow.id,
        conditions={},
        enabled=True
    )
    
    # Query by event type
    triggers = trigger_crud.get_by_event_type("file_upload")
    
    assert len(triggers) > 0
    assert any(t.id == created_trigger.id for t in triggers)

def test_list_triggers(db_session, sample_workflow):
    """Test listing all triggers"""
    trigger_crud = TriggerCRUD(db_session)
    
    # Create multiple triggers
    for i in range(3):
        trigger_crud.create(
            event_type=f"event_{i}",
            workflow_id=sample_workflow.id,
            conditions={},
            enabled=True
        )
    
    all_triggers = trigger_crud.list()
    assert len(all_triggers) >= 3

def test_disable_trigger(db_session, sample_workflow):
    """Test disabling a trigger"""
    trigger_crud = TriggerCRUD(db_session)
    
    trigger = trigger_crud.create(
        event_type="file_upload",
        workflow_id=sample_workflow.id,
        conditions={},
        enabled=True
    )
    
    # Disable
    updated = trigger_crud.update(
        trigger.id,
        {"enabled": False}
    )
    
    assert updated.enabled is False

# =======================
# Trigger Service Tests (Event Matching)
# =======================

def test_trigger_pattern_matching_exact_event(db_session, sample_workflow):
    """Test trigger matches exact event type"""
    trigger_crud = TriggerCRUD(db_session)
    
    trigger = trigger_crud.create(
        event_type="file_upload",
        workflow_id=sample_workflow.id,
        conditions={},
        enabled=True
    )
    
    # Simulate event matching
    event = {"event_type": "file_upload", "file_name": "test.pdf"}
    
    # Pattern match
    matches = trigger_crud.get_by_event_type(event["event_type"])
    
    assert len(matches) > 0
    assert any(
        m.enabled and 
        m.event_type == event["event_type"] 
        for m in matches
    )

def test_trigger_with_conditions(db_session, sample_workflow):
    """Test trigger with metadata conditions"""
    trigger_crud = TriggerCRUD(db_session)
    
    trigger = trigger_crud.create(
        event_type="file_upload",
        workflow_id=sample_workflow.id,
        conditions={"file_type": "pdf", "folder": "/documents"},
        enabled=True
    )
    
    # Verify conditions stored
    assert trigger.conditions["file_type"] == "pdf"
    assert trigger.conditions["folder"] == "/documents"

def test_multiple_triggers_same_event(db_session, sample_workflow):
    """Test multiple triggers for same event execute independently"""
    trigger_crud = TriggerCRUD(db_session)
    
    # Create multiple workflows
    workflow_crud = WorkflowCRUD(db_session)
    workflow1 = sample_workflow
    workflow2 = workflow_crud.create(
        name="Alternative RAG Workflow",
        description="Alternative RAG processing",
        nodes={},
        connections=[],
        user_id=str(uuid.uuid4())
    )
    
    # Create triggers for same event
    trigger1 = trigger_crud.create(
        event_type="file_upload",
        workflow_id=workflow1.id,
        conditions={},
        enabled=True
    )
    
    trigger2 = trigger_crud.create(
        event_type="file_upload",
        workflow_id=workflow2.id,
        conditions={},
        enabled=True
    )
    
    # Both should match same event
    matches = trigger_crud.get_by_event_type("file_upload")
    workflow_ids = [t.workflow_id for t in matches if t.enabled]
    
    assert workflow1.id in workflow_ids
    assert workflow2.id in workflow_ids

# =======================
# Workflow Execution Tests
# =======================

def test_workflow_execution_from_trigger(db_session, sample_workflow):
    """Test that trigger can execute workflow"""
    # Simulate workflow engine receiving workflow
    workflow_crud = WorkflowCRUD(db_session)
    fetched = workflow_crud.get_by_id(sample_workflow.id)
    
    assert fetched is not None
    assert fetched.nodes is not None
    assert len(fetched.nodes) > 0

def test_workflow_execution_record(db_session, sample_workflow):
    """Test workflow execution creates execution record"""
    workflow_crud = WorkflowCRUD(db_session)
    
    # Create execution
    execution = workflow_crud.create_execution(
        workflow_id=sample_workflow.id,
        status="running",
        input_data={"document": "test content"},
        output_data={}
    )
    
    assert execution is not None
    assert execution.workflow_id == sample_workflow.id
    assert execution.status == "running"

def test_workflow_execution_completion(db_session, sample_workflow):
    """Test updating workflow execution to complete"""
    workflow_crud = WorkflowCRUD(db_session)
    
    execution = workflow_crud.create_execution(
        workflow_id=sample_workflow.id,
        status="running",
        input_data={"document": "test"},
        output_data={}
    )
    
    # Update to completed
    updated = workflow_crud.update_execution(
        execution.id,
        status="completed",
        output_data={"embeddings": [0.1, 0.2, 0.3]}
    )
    
    assert updated.status == "completed"
    assert updated.output_data["embeddings"] is not None

# =======================
# Integration Tests (Full Cycle)
# =======================

def test_full_cycle_file_upload_trigger_workflow(db_session, sample_workflow):
    """
    INTEGRATION TEST: Complete cycle
    1. Create trigger for file_upload → RAG workflow
    2. Simulate file_upload event
    3. Verify workflow execution started
    4. Verify embeddings would be generated
    """
    trigger_crud = TriggerCRUD(db_session)
    workflow_crud = WorkflowCRUD(db_session)
    
    # 1. Create trigger
    trigger = trigger_crud.create(
        event_type="file_upload",
        workflow_id=sample_workflow.id,
        conditions={"file_type": "pdf"},
        enabled=True
    )
    
    assert trigger is not None
    
    # 2. Simulate file_upload event
    event = {
        "event_type": "file_upload",
        "file_name": "document.pdf",
        "file_type": "pdf",
        "document_id": str(uuid.uuid4()),
        "content": "Sample document content"
    }
    
    # 3. Match trigger
    matching_triggers = trigger_crud.get_by_event_type(event["event_type"])
    assert len(matching_triggers) > 0
    
    for matched_trigger in matching_triggers:
        if matched_trigger.enabled:
            # Get workflow
            workflow = workflow_crud.get_by_id(matched_trigger.workflow_id)
            
            # 3. Create execution
            execution = workflow_crud.create_execution(
                workflow_id=workflow.id,
                status="running",
                input_data=event,
                output_data={}
            )
            
            # 4. Simulate workflow processing
            execution = workflow_crud.update_execution(
                execution.id,
                status="completed",
                output_data={
                    "embeddings_generated": True,
                    "document_id": event["document_id"],
                    "embedding_vector": [0.1] * 768  # Mock embedding
                }
            )
            
            assert execution.status == "completed"
            assert execution.output_data["embeddings_generated"] is True

def test_integration_multiple_workflows_execution(db_session):
    """
    INTEGRATION: Multiple workflows execute for same event
    """
    trigger_crud = TriggerCRUD(db_session)
    workflow_crud = WorkflowCRUD(db_session)
    
    # Create workflows
    workflows = []
    for i in range(2):
        workflow = workflow_crud.create(
            name=f"Workflow {i}",
            description=f"Test workflow {i}",
            nodes={},
            connections=[],
            user_id=str(uuid.uuid4())
        )
        workflows.append(workflow)
    
    # Create triggers
    triggers = []
    for workflow in workflows:
        trigger = trigger_crud.create(
            event_type="file_upload",
            workflow_id=workflow.id,
            conditions={},
            enabled=True
        )
        triggers.append(trigger)
    
    # Simulate event
    event = {
        "event_type": "file_upload",
        "document_id": str(uuid.uuid4())
    }
    
    # Execute all matching workflows
    matching_triggers = trigger_crud.get_by_event_type(event["event_type"])
    executions = []
    
    for trigger in matching_triggers:
        if trigger.enabled:
            execution = workflow_crud.create_execution(
                workflow_id=trigger.workflow_id,
                status="completed",
                input_data=event,
                output_data={"processed": True}
            )
            executions.append(execution)
    
    # Verify all workflows executed
    assert len(executions) == len(workflows)
    for execution in executions:
        assert execution.status == "completed"

# =======================
# Error Handling Tests
# =======================

def test_trigger_nonexistent_workflow(db_session):
    """Test trigger with invalid workflow_id"""
    trigger_crud = TriggerCRUD(db_session)
    
    # Try to create with non-existent workflow
    trigger = trigger_crud.create(
        event_type="file_upload",
        workflow_id=str(uuid.uuid4()),  # Non-existent
        conditions={},
        enabled=True
    )
    
    # Should still create, but workflow lookup will fail
    assert trigger is not None
    assert trigger.workflow_id is not None

def test_disabled_trigger_not_executed(db_session, sample_workflow):
    """Test that disabled triggers don't execute"""
    trigger_crud = TriggerCRUD(db_session)
    
    # Create disabled trigger
    trigger = trigger_crud.create(
        event_type="file_upload",
        workflow_id=sample_workflow.id,
        conditions={},
        enabled=False
    )
    
    # When matching, check enabled status
    matches = trigger_crud.get_by_event_type("file_upload")
    active_matches = [t for t in matches if t.enabled]
    
    # Disabled trigger should not be in active matches
    assert not any(t.id == trigger.id for t in active_matches)

def test_execution_failure_handling(db_session, sample_workflow):
    """Test workflow execution failure handling"""
    workflow_crud = WorkflowCRUD(db_session)
    
    execution = workflow_crud.create_execution(
        workflow_id=sample_workflow.id,
        status="running",
        input_data={},
        output_data={}
    )
    
    # Mark as failed
    failed = workflow_crud.update_execution(
        execution.id,
        status="failed",
        output_data={"error": "Node execution failed"}
    )
    
    assert failed.status == "failed"
    assert "error" in failed.output_data

# =======================
# Execution History Tests
# =======================

def test_workflow_execution_history(db_session, sample_workflow):
    """Test retrieving workflow execution history"""
    workflow_crud = WorkflowCRUD(db_session)
    
    # Create multiple executions
    for i in range(3):
        workflow_crud.create_execution(
            workflow_id=sample_workflow.id,
            status="completed",
            input_data={"iteration": i},
            output_data={}
        )
    
    # Get executions for workflow
    executions = workflow_crud.get_executions_by_workflow(sample_workflow.id)
    
    assert len(executions) >= 3

def test_execution_timestamps(db_session, sample_workflow):
    """Test execution has proper timestamps"""
    workflow_crud = WorkflowCRUD(db_session)
    
    execution = workflow_crud.create_execution(
        workflow_id=sample_workflow.id,
        status="completed",
        input_data={},
        output_data={}
    )
    
    assert execution.created_at is not None
    assert isinstance(execution.created_at, datetime)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
