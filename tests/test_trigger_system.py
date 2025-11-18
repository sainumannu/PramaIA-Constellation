#!/usr/bin/env python3
"""
TEST SISTEMA TRIGGER CON WORKFLOW CRUD
======================================

Test per verificare il funzionamento del sistema di trigger 
con i workflow CRUD importati.
"""

import sys
import os
import sqlite3
import json
import asyncio
from pathlib import Path

# Configurazione paths
sys.path.append("C:/PramaIA")

def check_trigger_workflow_mapping():
    """Verifica il mapping tra trigger e workflow."""
    print("🔍 VERIFICA MAPPING TRIGGER → WORKFLOW")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('C:/PramaIA/backend/db/database.db')
        cursor = conn.cursor()
        
        # Trigger nel database
        cursor.execute("""
            SELECT name, event_type, source, workflow_id, active 
            FROM workflow_triggers
            ORDER BY event_type
        """)
        triggers = cursor.fetchall()
        
        # Workflow nel database  
        cursor.execute("SELECT workflow_id, name FROM workflows")
        workflows = {wid: name for wid, name in cursor.fetchall()}
        
        print(f"📊 Trigger: {len(triggers)} | Workflow: {len(workflows)}")
        print()
        
        # Analizza mapping
        for trigger_name, event_type, source, workflow_id, active in triggers:
            status = "✅ Attivo" if active else "❌ Disattivo"
            
            if workflow_id in workflows:
                workflow_status = f"✅ {workflows[workflow_id]}"
            else:
                workflow_status = f"❌ Workflow '{workflow_id}' NON TROVATO"
            
            print(f"🎯 {trigger_name}")
            print(f"   • Evento: {event_type}")
            print(f"   • Source: {source}")
            print(f"   • Status: {status}")
            print(f"   • Workflow: {workflow_status}")
            print()
        
        # Problemi rilevati
        missing_workflows = []
        for _, _, _, workflow_id, _ in triggers:
            if workflow_id not in workflows:
                missing_workflows.append(workflow_id)
        
        if missing_workflows:
            print("⚠️ PROBLEMI RILEVATI:")
            for wid in missing_workflows:
                print(f"   - Workflow '{wid}' referenziato da trigger ma non esistente")
            print()
            
            # Proponi alternative per workflow mancanti
            print("💡 WORKFLOW DISPONIBILI PER RIMAPPING:")
            for wid, name in workflows.items():
                if 'PDF' in name.upper() or 'DOCUMENT' in name.upper():
                    print(f"   - {wid}: {name}")
            
            return False
        else:
            print("✅ MAPPING CORRETTO: Tutti i trigger referenziano workflow esistenti")
            return True
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Errore verifica mapping: {e}")
        return False

def propose_trigger_updates():
    """Propone aggiornamenti dei trigger per i workflow CRUD."""
    print("\n💡 PROPOSTA AGGIORNAMENTO TRIGGER")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('C:/PramaIA/backend/db/database.db')
        cursor = conn.cursor()
        
        # Workflow CRUD disponibili
        cursor.execute("SELECT workflow_id, name FROM workflows WHERE name LIKE '%PDF%'")
        crud_workflows = cursor.fetchall()
        
        print("🔧 WORKFLOW CRUD DISPONIBILI:")
        for wid, name in crud_workflows:
            print(f"   - {wid}: {name}")
        
        print("\n📋 MAPPATURA TRIGGER SUGGERITA:")
        
        # Mapping suggeriti
        mappings = [
            ("pdf_file_added", "PDF Document CREATE Pipeline"),
            ("pdf_file_updated", "PDF Document UPDATE Pipeline"), 
            ("pdf_file_deleted", "PDF Document DELETE Pipeline"),
            ("pdf_search_query", "PDF Document READ Pipeline")  # Nuovo trigger per READ
        ]
        
        for event_type, target_workflow_name in mappings:
            # Trova il workflow_id corrispondente
            matching_workflow = None
            for wid, name in crud_workflows:
                if target_workflow_name in name:
                    matching_workflow = (wid, name)
                    break
            
            if matching_workflow:
                print(f"   • {event_type} → {matching_workflow[0]} ({matching_workflow[1]})")
            else:
                print(f"   • {event_type} → ❌ Workflow '{target_workflow_name}' non trovato")
        
        # Query di update suggerite
        print("\n🔨 QUERY UPDATE SUGGERITE:")
        for event_type, target_workflow_name in mappings[:3]:  # Solo i primi 3 esistenti
            matching_workflow = None
            for wid, name in crud_workflows:
                if target_workflow_name in name:
                    matching_workflow = (wid, name)
                    break
            
            if matching_workflow:
                print(f"""
UPDATE workflow_triggers 
SET workflow_id = '{matching_workflow[0]}' 
WHERE event_type = '{event_type}';""")
        
        # Nuovo trigger per READ 
        read_workflow = None
        for wid, name in crud_workflows:
            if "READ" in name:
                read_workflow = (wid, name)
                break
                
        if read_workflow:
            print(f"""
INSERT INTO workflow_triggers (id, name, event_type, source, workflow_id, active)
VALUES (
    'trigger_pdf_read_query',
    'Trigger Query PDF',
    'pdf_search_query',
    'search-api-source',
    '{read_workflow[0]}',
    1
);""")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Errore proposta aggiornamenti: {e}")
        return False

async def test_trigger_service():
    """Test del trigger service con eventi simulati."""
    print("\n🧪 TEST TRIGGER SERVICE")
    print("=" * 60)
    
    try:
        # Import necessari
        from backend.db.database import get_db
        from backend.services.trigger_service import TriggerService
        
        # Setup database
        db = next(get_db())
        trigger_service = TriggerService(db)
        
        print("✅ TriggerService inizializzato")
        
        # Test eventi simulati
        test_events = [
            {
                "event_type": "pdf_file_added",
                "data": {
                    "file_path": "/test/document.pdf",
                    "file_size": 1024,
                    "mime_type": "application/pdf"
                },
                "metadata": {
                    "source": "pdf-monitor-event-source",
                    "timestamp": "2025-11-15T10:00:00Z"
                }
            },
            {
                "event_type": "pdf_file_updated",
                "data": {
                    "file_path": "/test/document_v2.pdf",
                    "file_size": 2048,
                    "previous_version": "/test/document.pdf"
                },
                "metadata": {
                    "source": "pdf-monitor-event-source",
                    "timestamp": "2025-11-15T10:05:00Z"
                }
            }
        ]
        
        print("\n🎯 SIMULAZIONE EVENTI:")
        
        for i, event in enumerate(test_events, 1):
            print(f"\n--- Test Evento {i}: {event['event_type']} ---")
            print(f"Data: {event['data']}")
            print(f"Metadata: {event['metadata']}")
            
            try:
                result = await trigger_service.process_event(
                    event_type=event["event_type"],
                    data=event["data"],
                    metadata=event["metadata"]
                )
                
                print(f"✅ Risultato: {result}")
                
                if result.get("success"):
                    print(f"   • Trigger trovati: {result.get('triggers_matched', 0)}")
                    print(f"   • Workflow eseguiti: {result.get('workflows_executed', 0)}")
                else:
                    print(f"   ❌ Errore: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Errore processing evento: {e}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Errore test trigger service: {e}")
        return False

def main():
    """Test principale del sistema trigger."""
    print("🚀 ANALISI E TEST SISTEMA TRIGGER")
    print("=" * 80)
    
    results = []
    
    # 1. Verifica mapping trigger-workflow
    results.append(check_trigger_workflow_mapping())
    
    # 2. Proponi aggiornamenti se necessario
    if not results[0]:
        propose_trigger_updates()
    
    # 3. Test trigger service (se mapping OK)
    if results[0]:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            test_result = loop.run_until_complete(test_trigger_service())
            results.append(test_result)
        except Exception as e:
            print(f"❌ Errore test async: {e}")
            results.append(False)
    
    # Risultato finale
    print("\n" + "=" * 80)
    print("🎯 RIEPILOGO TEST TRIGGER")
    
    if all(results):
        print("✅ Sistema trigger completamente funzionante:")
        print("   - Mapping trigger → workflow: OK")
        print("   - TriggerService: OK")
        print("   - Simulazione eventi: OK")
    else:
        print("⚠️ Sistema trigger richiede attenzione:")
        if not results[0]:
            print("   - Mapping trigger → workflow: PROBLEMI")
        if len(results) > 1 and not results[1]:
            print("   - TriggerService test: FALLITO")
    
    print("=" * 80)

if __name__ == "__main__":
    main()