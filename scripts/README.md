# PramaIA Scripts Organization

**Struttura organizzata script e utility del progetto**

## 📁 **Struttura Script**

```
scripts/
├── maintenance/         🔧 Script diagnostici e manutenzione
├── debug/              🐛 Script debug e analisi problemi  
├── migration/          📦 Script migrazione e rebuild
└── workflows/          🔄 Script gestione workflow

tests/                  ✅ Test suite completa
```

## 🎯 **Utilizzo per Categoria**

### 🔧 **Maintenance** (`scripts/maintenance/`)
**Quando usare:** Controlli periodici, post-deploy validation
```bash
python scripts/maintenance/check_system_status.py
```

### 🐛 **Debug** (`scripts/debug/`)  
**Quando usare:** Problemi in produzione, troubleshooting
```bash
python scripts/debug/debug_database.py
```

### 📦 **Migration** (`scripts/migration/`)
**⚠️ ATTENZIONE:** Solo con backup, ambiente test
```bash
python scripts/migration/run_rebuild_simple.py
```

### 🔄 **Workflows** (`scripts/workflows/`)
**Quando usare:** Gestione workflow, configurazioni
```bash
python scripts/workflows/list_workflows_triggers.py
```

### ✅ **Tests** (`tests/`)
**Quando usare:** Validazione modifiche, CI/CD
```bash
python -m pytest tests/
```

## 📋 **Script Principali per Ruolo**

### 👨‍💻 **Sviluppatore**
- `tests/simple_test.py` - Smoke test rapido
- `scripts/debug/debug_database.py` - Debug DB
- `scripts/workflows/list_workflow_nodes.py` - Inventario nodi

### 🔧 **DevOps**  
- `scripts/maintenance/check_system_status.py` - Health check
- `scripts/migration/run_rebuild_simple.py` - Deploy updates
- `scripts/debug/analyze_triggers.py` - Monitor trigger

### 👨‍💼 **Admin Sistema**
- `scripts/maintenance/check_schema.py` - Validazione DB
- `scripts/workflows/create_delete_update_workflows.py` - Gestione workflow
- `tests/test_workflow_execution.py` - Test end-to-end

## 🚀 **Quick Commands**

```bash
# Health check completo
python scripts/maintenance/check_system_status.py

# Debug rapido quando qualcosa non va
python scripts/debug/debug_database.py

# Lista tutti i workflow attivi  
python scripts/workflows/list_workflows_triggers.py

# Test veloce del sistema
python tests/simple_test.py

# Rebuild ambiente development (SAFE)
python scripts/migration/run_rebuild_simple.py
```

## ⚠️ **Safety Guidelines**

### 🟢 **SAFE** (Sempre utilizzabili)
- Tutti gli script in `maintenance/`
- Tutti gli script in `debug/` 
- Tutti i test in `tests/`
- Script `list_*` in `workflows/`

### 🟡 **CAUTION** (Backup consigliato)
- Script `create_*`, `update_*` in `workflows/`
- Script con modifiche al database

### 🔴 **DANGER** (Solo con backup obbligatorio)
- Tutti gli script in `migration/`
- Script con `rebuild` nel nome
- File `.sql` con `DROP` statements

## 📈 **Metriche Organizzazione**

- **Total files moved:** 25+ script organizzati
- **Categories created:** 4 categorie principali  
- **Documentation:** README per ogni categoria
- **Safety level:** Color-coded per ogni script
- **Cleanup:** File temporanei e backup rimossi

---
**Organizzazione completata:** 16 Novembre 2025  
**Struttura:** Pronta per team development  
**Manutenzione:** Script categorizzati per uso sicuro