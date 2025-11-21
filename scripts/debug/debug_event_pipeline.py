"""
Debug script: Verifica che l'evento sia stato emesso e che il trigger abbia matchato
"""
import sys
sys.path.insert(0, "PramaIAServer")

from backend.db.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("=" * 70)
print("EVENT PIPELINE DEBUG")
print("=" * 70)

# 1. Check event_logs table
print("\n1. EVENT LOGS")
print("-" * 70)

try:
    from backend.models.trigger_models import EventLog
    
    events = db.query(EventLog).order_by(EventLog.processed_at.desc()).limit(5).all()
    
    if events:
        print(f"✓ Found {len(events)} event logs:\n")
        for i, e in enumerate(events, 1):
            print(f"  Event #{i}:")
            print(f"    Type: {e.event_type}")
            print(f"    Source: {e.source}")
            print(f"    Triggers matched: {e.triggers_matched}")
            print(f"    Workflows executed: {e.workflows_executed}")
            print(f"    Success: {e.success}")
            print(f"    Processed: {e.processed_at}")
            if e.error_message:
                print(f"    Error: {e.error_message}")
            print()
    else:
        print("✗ No event logs found - events not being logged!")
        
except Exception as e:
    print(f"✗ Error querying event logs: {e}")

# 2. Check event_triggers table
print("\n2. EVENT TRIGGERS")
print("-" * 70)

try:
    from backend.models.trigger_models import EventTrigger
    
    triggers = db.query(EventTrigger).all()
    
    print(f"✓ Total triggers: {len(triggers)}")
    for t in triggers:
        print(f"\n  Trigger: {t.name}")
        print(f"    ID: {t.id}")
        print(f"    Event Type: {t.event_type}")
        print(f"    Source: {t.source}")
        print(f"    Workflow ID: {t.workflow_id}")
        print(f"    Active: {t.active}")
        
except Exception as e:
    print(f"✗ Error querying triggers: {e}")

# 3. Check workflow_executions table
print("\n3. WORKFLOW EXECUTIONS")
print("-" * 70)

try:
    from backend.db.workflow_models import WorkflowExecution
    
    execs = db.query(WorkflowExecution).order_by(
        WorkflowExecution.started_at.desc()
    ).limit(5).all()
    
    if execs:
        print(f"✓ Found {len(execs)} executions:\n")
        for e in execs:
            print(f"  Execution ID: {e.execution_id}")
            print(f"    Workflow: {e.workflow_id}")
            print(f"    Status: {e.status}")
            print(f"    Started: {e.started_at}")
            print()
    else:
        print("✗ No workflow executions - workflows not being triggered!")
        
except Exception as e:
    print(f"✗ Error querying executions: {e}")

# 4. Check workflow_triggers (older system)
print("\n4. WORKFLOW TRIGGERS (Legacy System)")
print("-" * 70)

try:
    # Query directly with SQL to avoid model issues
    result = db.execute(text("SELECT id, name, event_type, source FROM workflow_triggers LIMIT 5"))
    triggers = result.fetchall()
    
    if triggers:
        print(f"✓ Found {len(triggers)} legacy triggers:")
        for t in triggers:
            print(f"  - {t[1]} (event: {t[2]}, source: {t[3]})")
    else:
        print("⚠ No legacy triggers")
        
except Exception as e:
    print(f"⚠ No legacy trigger system: {e}")

# 5. Check if tables exist
print("\n5. DATABASE TABLES CHECK")
print("-" * 70)

try:
    from sqlalchemy import inspect
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()
    
    required_tables = ["event_triggers", "event_logs", "workflow_executions"]
    
    for table in required_tables:
        status = "✓" if table in tables else "✗"
        print(f"  {status} {table}")
        
except Exception as e:
    print(f"✗ Error checking tables: {e}")

db.close()

print("\n" + "=" * 70)
print("DEBUG COMPLETE")
print("=" * 70)

print("\n💡 NEXT STEPS:")
print("  1. If event_logs is empty: event_emitter.py not being called")
print("  2. If event_logs exist but workflows_executed=0: trigger not matching")
print("  3. If workflow_executions empty: workflow engine not executing")
print("  4. Check backend console for 'emit_event' messages")
