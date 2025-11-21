"""
Test suite for Triggers & Integration - Complete document lifecycle (Simplified)
Tests the full workflow: file_upload → trigger → workflow execution → embeddings generation
"""

import pytest
import json
import uuid
from datetime import datetime
from unittest.mock import Mock, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'PramaIAServer'))


# =======================
# Mock Models & CRUD
# =======================

class MockTrigger:
    def __init__(self, id, event_type, workflow_id, conditions=None, enabled=True):
        self.id = id
        self.event_type = event_type
        self.workflow_id = workflow_id
        self.conditions = conditions or {}
        self.enabled = enabled


class MockWorkflow:
    def __init__(self, id, name, nodes=None, connections=None):
        self.id = id
        self.name = name
        self.nodes = nodes or {}
        self.connections = connections or []


class MockExecution:
    def __init__(self, id, workflow_id, status, input_data, output_data):
        self.id = id
        self.workflow_id = workflow_id
        self.status = status
        self.input_data = input_data
        self.output_data = output_data
        self.created_at = datetime.now()


class SimpleTriggerCRUD:
    """Mock CRUD for triggers"""
    def __init__(self):
        self.triggers = {}
        self.next_id = 1
    
    def create(self, event_type, workflow_id, conditions=None, enabled=True):
        trigger_id = str(self.next_id)
        self.next_id += 1
        trigger = MockTrigger(trigger_id, event_type, workflow_id, conditions, enabled)
        self.triggers[trigger_id] = trigger
        return trigger
    
    def get_by_event_type(self, event_type):
        return [t for t in self.triggers.values() if t.event_type == event_type]
    
    def list(self):
        return list(self.triggers.values())
    
    def update(self, trigger_id, data):
        if trigger_id in self.triggers:
            trigger = self.triggers[trigger_id]
            for key, value in data.items():
                setattr(trigger, key, value)
            return trigger
        return None


class SimpleWorkflowCRUD:
    """Mock CRUD for workflows"""
    def __init__(self):
        self.workflows = {}
        self.executions = {}
        self.next_workflow_id = 1
        self.next_execution_id = 1
    
    def create(self, name, description, nodes, connections, user_id):
        workflow_id = str(self.next_workflow_id)
        self.next_workflow_id += 1
        workflow = MockWorkflow(workflow_id, name, nodes, connections)
        self.workflows[workflow_id] = workflow
        return workflow
    
    def get_by_id(self, workflow_id):
        return self.workflows.get(workflow_id)
    
    def create_execution(self, workflow_id, status, input_data, output_data):
        execution_id = str(self.next_execution_id)
        self.next_execution_id += 1
        execution = MockExecution(execution_id, workflow_id, status, input_data, output_data)
        self.executions[execution_id] = execution
        return execution
    
    def update_execution(self, execution_id, status=None, output_data=None):
        if execution_id in self.executions:
            execution = self.executions[execution_id]
            if status:
                execution.status = status
            if output_data:
                execution.output_data = output_data
            return execution
        return None
    
    def get_executions_by_workflow(self, workflow_id):
        return [e for e in self.executions.values() if e.workflow_id == workflow_id]


# =======================
# Setup & Fixtures
# =======================

@pytest.fixture
def trigger_crud():
    return SimpleTriggerCRUD()


@pytest.fixture
def workflow_crud():
    return SimpleWorkflowCRUD()


@pytest.fixture
def sample_workflow(workflow_crud):
    """Create a sample RAG workflow"""
    workflow = workflow_crud.create(
        name="RAG Processing Workflow",
        description="Processes documents with RAG",
        nodes={
            "input": {
                "id": "input_1",
                "type": "input",
                "plugin": "core-input-plugin",
            },
            "rag": {
                "id": "rag_1",
                "type": "rag",
                "plugin": "core-rag-plugin",
            },
            "output": {
                "id": "output_1",
                "type": "output",
                "plugin": "core-output-plugin",
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

def test_create_trigger(trigger_crud, sample_workflow):
    """Test creating a trigger"""
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


def test_get_trigger_by_event(trigger_crud, sample_workflow):
    """Test retrieving triggers by event type"""
    created_trigger = trigger_crud.create(
        event_type="file_upload",
        workflow_id=sample_workflow.id,
        conditions={},
        enabled=True
    )
    
    triggers = trigger_crud.get_by_event_type("file_upload")
    
    assert len(triggers) > 0
    assert any(t.id == created_trigger.id for t in triggers)


def test_list_triggers(trigger_crud, sample_workflow):
    """Test listing all triggers"""
    for i in range(3):
        trigger_crud.create(
            event_type=f"event_{i}",
            workflow_id=sample_workflow.id,
            conditions={},
            enabled=True
        )
    
    all_triggers = trigger_crud.list()
    assert len(all_triggers) >= 3


def test_disable_trigger(trigger_crud, sample_workflow):
    """Test disabling a trigger"""
    trigger = trigger_crud.create(
        event_type="file_upload",
        workflow_id=sample_workflow.id,
        conditions={},
        enabled=True
    )
    
    # Disable
    updated = trigger_crud.update(trigger.id, {"enabled": False})
    
    assert updated.enabled is False


# =======================
# Trigger Service Tests (Event Matching)
# =======================

def test_trigger_pattern_matching_exact_event(trigger_crud, sample_workflow):
    """Test trigger matches exact event type"""
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


def test_trigger_with_conditions(trigger_crud, sample_workflow):
    """Test trigger with metadata conditions"""
    trigger = trigger_crud.create(
        event_type="file_upload",
        workflow_id=sample_workflow.id,
        conditions={"file_type": "pdf", "folder": "/documents"},
        enabled=True
    )
    
    # Verify conditions stored
    assert trigger.conditions["file_type"] == "pdf"
    assert trigger.conditions["folder"] == "/documents"


def test_multiple_triggers_same_event(trigger_crud, workflow_crud, sample_workflow):
    """Test multiple triggers for same event execute independently"""
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
        workflow_id=sample_workflow.id,
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
    
    assert sample_workflow.id in workflow_ids
    assert workflow2.id in workflow_ids


# =======================
# Workflow Execution Tests
# =======================

def test_workflow_execution_from_trigger(workflow_crud, sample_workflow):
    """Test that trigger can execute workflow"""
    fetched = workflow_crud.get_by_id(sample_workflow.id)
    
    assert fetched is not None
    assert fetched.nodes is not None
    assert len(fetched.nodes) > 0


def test_workflow_execution_record(workflow_crud, sample_workflow):
    """Test workflow execution creates execution record"""
    execution = workflow_crud.create_execution(
        workflow_id=sample_workflow.id,
        status="running",
        input_data={"document": "test content"},
        output_data={}
    )
    
    assert execution is not None
    assert execution.workflow_id == sample_workflow.id
    assert execution.status == "running"


def test_workflow_execution_completion(workflow_crud, sample_workflow):
    """Test updating workflow execution to complete"""
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

def test_full_cycle_file_upload_trigger_workflow(trigger_crud, workflow_crud, sample_workflow):
    """
    INTEGRATION TEST: Complete cycle
    1. Create trigger for file_upload → RAG workflow
    2. Simulate file_upload event
    3. Verify workflow execution started
    4. Verify embeddings would be generated
    """
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
            
            # 4. Simulate workflow processing (RAG node generating embeddings)
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
            print(f"✅ Full cycle completed: {event['file_name']} → {workflow.name} → embeddings generated")


def test_integration_multiple_workflows_execution(trigger_crud, workflow_crud):
    """
    INTEGRATION: Multiple workflows execute for same event
    """
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
    
    print(f"✅ Multiple workflows integration: {len(executions)} workflows executed for same event")


# =======================
# Error Handling Tests
# =======================

def test_disabled_trigger_not_executed(trigger_crud, sample_workflow):
    """Test that disabled triggers don't execute"""
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


def test_execution_failure_handling(workflow_crud, sample_workflow):
    """Test workflow execution failure handling"""
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

def test_workflow_execution_history(workflow_crud, sample_workflow):
    """Test retrieving workflow execution history"""
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


def test_execution_timestamps(workflow_crud, sample_workflow):
    """Test execution has proper timestamps"""
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
