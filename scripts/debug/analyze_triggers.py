#!/usr/bin/env python3
"""
ANALISI TRIGGER SISTEMA PramaIA
===============================

Analizza i trigger configurati nel sistema e confronta con i workflow CRUD.
"""

import sqlite3
import json
import os
from pathlib import Path

def analyze_database_triggers():
    """Analizza i trigger nel database."""
    print("🗄️ ANALISI TRIGGER DATABASE")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('C:/PramaIA/backend/db/database.db')
        cursor = conn.cursor()
        
        # Count totale
        cursor.execute("SELECT COUNT(*) FROM workflow_triggers")
        total_triggers = cursor.fetchone()[0]
        print(f"📊 Totale trigger nel database: {total_triggers}")
        
        if total_triggers > 0:
            # Lista trigger
            cursor.execute("""
                SELECT name, event_type, source, workflow_id, active, conditions, target_node_id 
                FROM workflow_triggers 
                ORDER BY event_type, name
            """)
            
            triggers = cursor.fetchall()
            print("\n📋 TRIGGER ESISTENTI:")
            for name, event_type, source, workflow_id, active, conditions, target_node in triggers:
                status = "✅ Attivo" if active else "❌ Disattivo"
                print(f"   - {name}")
                print(f"     • Evento: {event_type}")
                print(f"     • Source: {source}")
                print(f"     • Workflow: {workflow_id}")
                print(f"     • Target Node: {target_node}")
                print(f"     • Status: {status}")
                print(f"     • Conditions: {conditions}")
                print()
            
            # Grouping per event_type
            cursor.execute("SELECT event_type, COUNT(*) FROM workflow_triggers GROUP BY event_type")
            event_types = cursor.fetchall()
            print("📈 TRIGGER PER TIPO EVENTO:")
            for event_type, count in event_types:
                print(f"   - {event_type}: {count} trigger")
        else:
            print("⚠️  Nessun trigger trovato nel database")
        
        conn.close()
        return total_triggers > 0
        
    except Exception as e:
        print(f"❌ Errore analisi database: {e}")
        return False

def analyze_workflow_trigger_definitions():
    """Analizza le definizioni dei trigger nei file JSON dei workflow."""
    print("\n📄 ANALISI TRIGGER NEI WORKFLOW JSON")
    print("=" * 50)
    
    try:
        workflow_files = [
            "C:/PramaIA/PramaIA-PDK/workflows/pdf_document_create_pipeline.json",
            "C:/PramaIA/PramaIA-PDK/workflows/pdf_document_read_pipeline.json", 
            "C:/PramaIA/PramaIA-PDK/workflows/pdf_document_update_pipeline.json",
            "C:/PramaIA/PramaIA-PDK/workflows/pdf_document_delete_pipeline.json"
        ]
        
        all_triggers = {}
        
        for filepath in workflow_files:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    workflow = json.load(f)
                    
                workflow_name = workflow.get('name', os.path.basename(filepath))
                triggers = workflow.get('triggers', [])
                
                print(f"\n🔧 {workflow_name}")
                print(f"   Trigger definiti: {len(triggers)}")
                
                if triggers:
                    for i, trigger in enumerate(triggers):
                        trigger_name = trigger.get('name', f'Trigger-{i+1}')
                        event_type = trigger.get('event_type', 'N/A')
                        source = trigger.get('source', 'N/A')
                        conditions = trigger.get('conditions', {})
                        target_node = trigger.get('target_node_id', 'N/A')
                        
                        print(f"     • {trigger_name}")
                        print(f"       - Evento: {event_type}")
                        print(f"       - Source: {source}")
                        print(f"       - Target: {target_node}")
                        print(f"       - Conditions: {len(conditions) if isinstance(conditions, dict) else 'N/A'}")
                        
                        # Raccolta per statistiche globali
                        if event_type not in all_triggers:
                            all_triggers[event_type] = []
                        all_triggers[event_type].append({
                            'workflow': workflow_name,
                            'trigger': trigger_name,
                            'source': source
                        })
                else:
                    print("     ⚠️  Nessun trigger definito")
            else:
                print(f"❌ File non trovato: {os.path.basename(filepath)}")
        
        # Statistiche globali
        if all_triggers:
            print(f"\n📊 RIEPILOGO TRIGGER DEFINITI:")
            for event_type, triggers in all_triggers.items():
                print(f"   - {event_type}: {len(triggers)} trigger")
                for trigger in triggers:
                    print(f"     • {trigger['trigger']} ({trigger['workflow']}) -> {trigger['source']}")
        
        return len(all_triggers) > 0
        
    except Exception as e:
        print(f"❌ Errore analisi JSON: {e}")
        return False

def analyze_trigger_system_documentation():
    """Analizza la documentazione del sistema di trigger."""
    print("\n📚 DOCUMENTAZIONE TRIGGER SYSTEM")
    print("=" * 50)
    
    doc_files = [
        "C:/PramaIA/docs/EVENT_TRIGGER_SYSTEM.md",
        "C:/PramaIA/docs/CHANGELOG_TRIGGER_SYSTEM_v2.0.0.md"
    ]
    
    for doc_file in doc_files:
        if os.path.exists(doc_file):
            print(f"✅ Trovato: {os.path.basename(doc_file)}")
            
            # Quick scan per tipi di evento menzionati
            with open(doc_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Cerca pattern di eventi
            import re
            event_patterns = re.findall(r'event_type.*?["\']([^"\']+)["\']', content, re.IGNORECASE)
            source_patterns = re.findall(r'source.*?["\']([^"\']+)["\']', content, re.IGNORECASE)
            
            if event_patterns:
                print(f"   Event types menzionati: {set(event_patterns)}")
            if source_patterns:
                print(f"   Sources menzionati: {set(source_patterns)}")
        else:
            print(f"❌ Non trovato: {os.path.basename(doc_file)}")

def check_trigger_backend_support():
    """Verifica il supporto backend per i trigger."""
    print("\n🔧 SUPPORTO BACKEND TRIGGER")
    print("=" * 50)
    
    backend_files = [
        "C:/PramaIA/backend/engine/trigger_engine.py",
        "C:/PramaIA/backend/engine/event_handler.py", 
        "C:/PramaIA/backend/services/trigger_service.py",
        "C:/PramaIA/backend/models/trigger.py"
    ]
    
    for backend_file in backend_files:
        if os.path.exists(backend_file):
            print(f"✅ {os.path.basename(backend_file)}")
        else:
            print(f"❌ {os.path.basename(backend_file)}")

def main():
    """Analisi principale dei trigger."""
    print("🚀 ANALISI COMPLETA SISTEMA TRIGGER")
    print("=" * 60)
    
    results = []
    
    # Analisi database
    results.append(analyze_database_triggers())
    
    # Analisi definizioni JSON
    results.append(analyze_workflow_trigger_definitions())
    
    # Documentazione
    analyze_trigger_system_documentation()
    
    # Supporto backend
    check_trigger_backend_support()
    
    # Risultato finale
    print("\n" + "=" * 60)
    print("🎯 RIEPILOGO ANALISI TRIGGER")
    
    if any(results):
        print("✅ Sistema trigger configurato:")
        print("   - Database: ✅" if results[0] else "   - Database: ⚠️ Vuoto")
        print("   - Workflow JSON: ✅" if results[1] else "   - Workflow JSON: ⚠️ Non definiti")
        print("\n💡 NEXT STEPS:")
        if not results[0]:
            print("   1. Importare trigger da JSON a database")
        if results[0] and results[1]:
            print("   1. Verificare sincronizzazione JSON ↔ Database") 
        print("   2. Testare attivazione trigger")
        print("   3. Verificare event handling")
    else:
        print("⚠️ Sistema trigger non configurato")
        print("💡 NEXT STEPS:")
        print("   1. Definire trigger nei workflow JSON")
        print("   2. Importare trigger nel database")
        print("   3. Implementare trigger engine")
    
    print("=" * 60)

if __name__ == "__main__":
    main()