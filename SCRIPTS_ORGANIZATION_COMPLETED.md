# 📁 PramaIA Scripts Organization - COMPLETED

## ✅ Pulizia e Riorganizzazione Completata

**Data**: 20 Novembre 2025  
**Risultato**: Script organizzati logicamente nelle sottocartelle

---

## 📂 Struttura Organizzata

```
scripts/
├── 🔧 maintenance/     # Script di verifica e controllo sistema
├── 🐛 debug/          # Script per debugging e troubleshooting  
├── 🔄 workflows/      # Script gestione workflow e nodi
├── 📦 migration/      # Script migrazione e rebuild database
├── 🔧 utilities/      # Script utility varie
└── 🧪 testing/        # Test E2E e validazione sistema

tests/
└── 📋 (config)       # Solo file di configurazione test (conftest.py, run_tests.py)
```

---

## 🔧 scripts/maintenance/ - Verifica & Controllo

**Scopo**: Verificare stato sistema, database, servizi, configurazioni

| Script | Funzione |
|--------|----------|
| `check_admin_user.py` | Verifica utente admin |
| `check_auth_endpoints.py` | Test endpoint autenticazione |
| `check_db_schema.py` | Verifica schema database principale |
| `check_documents_db_schema.py` | Verifica schema database documenti |
| `check_event_flow.py` | Verifica flusso eventi completo |
| `check_monitor_buffer.py` | Verifica buffer eventi monitor |
| `check_monitoring_config.py` | Verifica configurazione monitoring |
| `check_nodes.py` | Analisi nodi workflow |
| `check_pdk_nodes.py` | Lista nodi PDK disponibili |
| `check_pramaiaserver_schema.py` | Verifica schema server principale |
| `check_system_status.py` | Status completo sistema |
| `check_triggers.py` | Verifica trigger nel database |
| `check_users.py` | Verifica tabella utenti |
| `check_vectorstore_schema.py` | Verifica schema vectorstore |
| `check_workflow_errors.py` | Ricerca errori workflow |
| `check_workflow_ids.py` | Verifica ID workflow |
| `check_workflow_schema.py` | Verifica schema workflow |
| `check_workflow_structure.py` | Struttura workflow |
| `test_crud_operations.py` | Test operazioni CRUD |

**Utilizzo Tipico**:
```bash
# Health check rapido
python scripts/maintenance/check_system_status.py

# Verifica trigger
python scripts/maintenance/check_triggers.py

# Verifica database
python scripts/maintenance/check_db_schema.py
```

---

## 🐛 scripts/debug/ - Debugging & Troubleshooting

**Scopo**: Debug problemi specifici, analisi approfondite, troubleshooting

| Script | Funzione |
|--------|----------|
| `debug_database.py` | Debug completo database |
| `debug_event_pipeline.py` | Debug pipeline eventi |
| `debug_triggers.py` | Debug trigger con simulazione |
| `debug_workflow_engine.py` | Debug engine workflow |
| `debug_workflow_input.py` | Debug input workflow |
| `patch_sqlalchemy.py` | Patch per SQLAlchemy |
| `run_sql.py` | Esecuzione SQL diretta |
| `test_triggers_integration.py` | Test debug integrazione trigger |
| `test_triggers_integration_simple.py` | Test debug trigger semplice |

**Utilizzo Tipico**:
```bash
# Debug trigger
python scripts/debug/debug_triggers.py

# Debug workflow
python scripts/debug/debug_workflow_engine.py

# Debug eventi
python scripts/debug/debug_event_pipeline.py
```

---

## 🔄 scripts/workflows/ - Gestione Workflow

**Scopo**: Creazione, modifica, gestione workflow e nodi

| Script | Funzione |
|--------|----------|
| `create_delete_update_workflows.py` | CRUD workflow completo |
| `import_crud_workflows.py` | Importazione workflow |
| `insert_crud_workflows.py` | Inserimento workflow |
| `insert_pdf_semantic_workflow.py` | Workflow semantic PDF |
| `list_workflow_nodes.py` | Lista nodi workflow |
| `list_workflows_triggers.py` | Lista workflow e trigger |
| `test_workflow_execution.py` | Test esecuzione workflow |
| `update_workflow_processors.py` | Aggiorna processori |
| `update_workflow_triggers.py` | Aggiorna trigger |

**Utilizzo Tipico**:
```bash
# Lista workflow
python scripts/workflows/list_workflows_triggers.py

# Crea workflow
python scripts/workflows/create_delete_update_workflows.py

# Test workflow
python scripts/workflows/test_workflow_execution.py
```

---

## 📦 scripts/migration/ - Migrazione Database

**Scopo**: Migrazione, rebuild, aggiornamenti database

| Script | Funzione |
|--------|----------|
| `run_rebuild_verbose.py` | Rebuild database con log esteso |

**Utilizzo Tipico**:
```bash
# ⚠️ ATTENZIONE: Solo con backup!
python scripts/migration/run_rebuild_verbose.py
```

---

## 🔧 scripts/utilities/ - Utility Varie

**Scopo**: Script di utility generali, ispezione dati, manutenzione

| Script | Funzione |
|--------|----------|
| `inspect_documents_data.py` | Ispezione documenti database |
| `process_monitor_events.py` | Elaborazione eventi monitor |
| `quick_check.py` | Check rapido sistema |
| `test_inventory.py` | Test inventario sistema |
| `test_utils.py` | Utility per test |

**Utilizzo Tipico**:
```bash
# Check rapido
python scripts/utilities/quick_check.py

# Ispezione documenti
python scripts/utilities/inspect_documents_data.py
```

---

## 🧪 scripts/testing/ - Test E2E e Validazione

**Scopo**: Test end-to-end, validazione sistema, test integrazione

| Script | Funzione |
|--------|----------|
| `test_e2e_modern_final.py` | Test E2E completo moderno |
| `test_e2e_register_login.py` | Test registrazione/login |
| `test_e2e_pipeline.py` | Test pipeline E2E |
| `test_monitor_upload.py` | Test monitor upload |
| `test_vectorization_pipeline.py` | Test pipeline vettorizzazione |
| `test_with_auth.py` | Test con autenticazione |

**Utilizzo Tipico**:
```bash
# Test E2E completo
python scripts/testing/test_e2e_modern_final.py

# Test monitor
python scripts/testing/test_monitor_upload.py

# Test pipeline
python scripts/testing/test_e2e_pipeline.py
```

---

## 📋 tests/ - Configurazione Test

**Scopo**: File di configurazione e runner per test suite

| Script | Funzione |
|--------|----------|
| `conftest.py` | Configurazione pytest |
| `run_tests.py` | Runner test suite |
| `__init__.py` | Init package test |

---

## ✅ tests/ - Test Suite

**Scopo**: Test E2E, validazione, test integrazione

| Script | Funzione |
|--------|----------|
| `test_e2e_modern_final.py` | Test E2E completo moderno |
| `test_e2e_register_login.py` | Test registrazione/login |
| `test_monitor_upload.py` | Test monitor upload |
| `test_vectorization_pipeline.py` | Test pipeline vettorizzazione |
| `test_with_auth.py` | Test con autenticazione |
| `test_workflow_execution.py` | Test esecuzione workflow |
| `test_triggers_integration.py` | Test integrazione trigger |
| `test_e2e_pipeline.py` | Test pipeline E2E |
| `test_crud_operations.py` | Test operazioni CRUD |
| Altri test... | Vedi tests/README.md |

**Utilizzo Tipico**:
```bash
# Test E2E completo
python tests/test_e2e_modern_final.py

# Test monitor
python tests/test_monitor_upload.py

# Test suite completa
python tests/run_tests.py
```

---

## 🎯 Quick Reference per Ruolo

### 👨‍💻 **Sviluppatore**
```bash
# Smoke test rapido
python scripts/utilities/quick_check.py

# Debug workflow
python scripts/debug/debug_workflow_engine.py

# Lista nodi disponibili
python scripts/maintenance/check_pdk_nodes.py
```

### 🔧 **DevOps**  
```bash
# Health check completo
python scripts/maintenance/check_system_status.py

# Verifica database
python scripts/maintenance/check_db_schema.py

# Debug eventi
python scripts/debug/debug_event_pipeline.py
```

### 👨‍💼 **Admin Sistema**
```bash
# Verifica trigger
python scripts/maintenance/check_triggers.py

# Gestione workflow
python scripts/workflows/list_workflows_triggers.py

# Test E2E
python tests/test_e2e_modern_final.py
```

---

## 📈 Risultati della Riorganizzazione

### ✅ **Prima della Pulizia**
- ~70+ script sparsi nella root
- Duplicati e script obsoleti
- Struttura disorganizzata
- Difficile trovare lo script giusto

### ✅ **Dopo la Riorganizzazione**
- **0 script nella root** - tutto organizzato!
- **~30 script essenziali** in 5 categorie logiche
- **Eliminati ~40+ duplicati**
- **Struttura logica e manutenibile**
- **Facile trovare e usare gli script**

---

## 🔍 Convenzioni

### **Naming**
- `check_*.py` → Verifica stato/configurazioni
- `debug_*.py` → Debugging problemi specifici
- `test_*.py` → Test e validazione
- Altri → Utility e operazioni specifiche

### **Organizzazione**
- **maintenance/** → Uso quotidiano, controlli
- **debug/** → Quando ci sono problemi
- **workflows/** → Gestione workflow
- **migration/** → Solo per aggiornamenti DB
- **utilities/** → Script generici
- **tests/** → Validazione e testing

---

**🎉 Organizzazione completata!** Ora gli script sono facili da trovare e usare!