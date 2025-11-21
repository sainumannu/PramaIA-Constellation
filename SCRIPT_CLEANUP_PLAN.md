# Piano di Pulizia Script PramaIA

## 📋 Analisi Attuale

Ho identificato numerosi script duplicati o simili che possono essere consolidati. Ecco la categorizzazione:

## 🔧 Script di Debug/Check da MANTENERE

### ✅ Script Debug Essenziali:
- `check_triggers.py` - Verifica stato trigger nel database (MANTIENI)
- `check_pdk_nodes.py` - Lista nodi PDK disponibili (MANTIENI)  
- `check_event_flow.py` - Verifica flusso eventi (MANTIENI)
- `debug_triggers.py` - Debug trigger con simulazione eventi (MANTIENI - più avanzato)

### ✅ Script Check Database:
- `check_db_schema.py` - Verifica schema database principale (MANTIENI)
- `check_vectorstore_schema.py` - Verifica schema vectorstore (MANTIENI)
- `check_documents_db_schema.py` - Schema documenti (MANTIENI)

### ✅ Script Check Servizi:
- `check_users.py` - Verifica utenti (MANTIENI)
- `check_auth_endpoints.py` - Test autenticazione (MANTIENI)

## ❌ Script da ELIMINARE (Doppioni/Obsoleti)

### Test E2E Duplicati:
- `test_e2e_final.py` ❌ (doppione di test_e2e_modern_final.py)
- `test_e2e_api_upload.py` ❌ (coperto da test_e2e_modern_final.py)
- `test_e2e_event_pipeline.py` ❌ (funzionalità sovrapposte)
- `test_complete_system.py` ❌ (ridondante con test_e2e_modern_final.py)
- `test_end_to_end.py` ❌ (doppione)
- `test_monitored_pdf_upload.py` ❌ (coperto da test_monitor_upload.py)
- `test_pdf_monitoring.py` ❌ (funzioni duplicate)

### Test Upload Duplicati:
- `test_upload_e2e.py` ❌ (coperto da test_e2e_modern_final.py)
- `test_monitor_upload.py` (MANTIENI - specifico per monitor)
- `test_direct_core_system.py` ❌ (ridondante)
- `test_direct_emit.py` ❌ (funzione coperta altrove)

### Script di Debug Ridondanti:
- `debug_workflow.py` ❌ (coperto da debug_workflow_engine.py)
- `debug_upload.py` ❌ (funzionalità coperte)
- `debug_input_nodes.py` ❌ (coperto da check_nodes.py)
- `debug_node_configs.py` ❌ (ridondante)

### Script di Report/Diagnostica Obsoleti:
- `final_report.py` ❌
- `final_diagnostic_report.py` ❌
- `final_test_summary.py` ❌
- `final_cleanup_legacy.py` ❌
- `analyze_*.py` (vari script di analisi temporanei) ❌

### Script di Fix Temporanei:
- `fix_trigger_manual.py` ❌
- `fix_trigger_nodes.py` ❌ 
- `fix_remaining_triggers.py` ❌
- `fix_admin_user_id.py` ❌

### Script di Test Legacy:
- `test_db_registry_simple.py` ❌
- `test_db_node_registry_e2e.py` ❌ (coperto da test moderni)
- `test_emit_event_direct.py` ❌
- `test_event_emitter_module.py` ❌

## ✅ Script da MANTENERE come Tools di Debug

### Testing Moderni:
- `test_e2e_modern_final.py` ✅ (completo e aggiornato)
- `test_monitor_upload.py` ✅ (specifico per monitor)
- `test_modern_only.py` ✅ (se diverso dai precedenti)

### Debug & Utilities:
- `debug_workflow_engine.py` ✅ (debug workflow)
- `debug_event_pipeline.py` ✅ (debug eventi)
- `check_workflow_schema.py` ✅
- `check_workflow_errors.py` ✅
- `process_monitor_events.py` ✅ (utility monitor)

### Database Tools:
- `inspect_documents_data.py` ✅
- `check_admin_user.py` ✅
- `quick_check.py` ✅ (se diverso dagli altri)

## 📁 Script in Sottocartelle (da Valutare)
- Scripts in `PramaIA-PDK/scripts/` - analizzare separatamente
- Scripts in `scripts/` subdirectory - già organizzati, mantenere
- Scripts in `tests/` - mantenere struttura esistente

## 🎯 Risultato Atteso

Dopo la pulizia:
- ~15-20 script essenziali di debug/check ben definiti
- Eliminazione di ~30-40 script duplicati/obsoleti
- Mantenimento di tools specifici per debugging
- Struttura più pulita e manutenibile