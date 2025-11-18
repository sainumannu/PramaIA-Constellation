# Test Suite PramaIA

**Test completi per validazione sistema**

## 📋 Test Disponibili

### Test Database

#### `test_chromadb_crud.py`
**Funzione:** Test operazioni ChromaDB
- CRUD operations vector store
- Performance inserimenti/query
- Validazione embedding

#### `test_sqlite_metadata.py`
**Funzione:** Test metadata SQLite
- Operazioni metadata
- Integrità referenziale
- Performance query

#### `test_coordinated_metadata.py`
**Funzione:** Test metadata coordinato
- Sincronizzazione metadata
- Coordinamento multi-store
- Validazione consistenza

### Test Sistema

#### `test_trigger_system.py`
**Funzione:** Test sistema trigger
- Attivazione trigger
- Propagazione eventi
- Performance trigger

#### `test_workflow_crud.py`
**Funzione:** Test CRUD workflow
- Operazioni workflow base
- Validazione configurazioni
- Test lifecycle workflow

#### `test_workflow_execution.py`
**Funzione:** Test esecuzione workflow
- Esecuzione end-to-end
- Performance execution
- Validazione output

### Test Semplici

#### `simple_test.py`
**Funzione:** Test base sistema
- Connectivity test
- Health check rapido
- Smoke test

#### `simple_trigger_test.py`
**Funzione:** Test trigger semplice
- Test trigger singolo
- Validazione rapida
- Debug trigger

## 🚀 Esecuzione Test

### Test Singolo
```bash
# Test specifico
cd C:\PramaIA
python tests/test_workflow_execution.py

# Test con output verboso
python -v tests/test_trigger_system.py
```

### Test Suite Completa
```bash
# Tutti i test
python -m pytest tests/

# Test con coverage
python -m pytest tests/ --cov=backend

# Test paralleli
python -m pytest tests/ -n auto
```

### Test Rapidi
```bash
# Smoke test veloce
python tests/simple_test.py

# Test trigger base
python tests/simple_trigger_test.py
```

## 📊 Categorie Test

### 🟢 **Test Verdi** (Sempre funzionanti)
- `simple_test.py` - Connectivity base
- `test_workflow_crud.py` - CRUD workflow

### 🟡 **Test Gialli** (Dipendenti da servizi)
- `test_trigger_system.py` - Richiede trigger attivi
- `test_workflow_execution.py` - Richiede PDK

### 🔴 **Test Rossi** (Al momento disabilitati)
- `test_chromadb_crud.py` - In migrazione verso PDK
- `test_coordinated_metadata.py` - In refactoring

## ⚡ Configurazione Test

### Environment
```bash
# Set environment per test
export PRAMAAI_ENV=test
export DB_URL=sqlite:///test.db
```

### Dependencies
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-xdist
```

## 📋 Checklist Test

- [ ] ✅ Database test configurato
- [ ] ✅ Servizi test attivi
- [ ] ✅ Environment variables set
- [ ] ✅ Test data preparata
- [ ] ✅ Mock services configured

---
**Categoria:** Testing  
**Coverage:** ~80% (target 90%)  
**Data organizzazione:** 16 Novembre 2025