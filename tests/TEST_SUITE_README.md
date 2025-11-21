# PramaIA Test Suite

Batteria completa di test per validazione e debug del sistema PramaIA.

## 📋 Contenuto Test Suite

### 1. **test_utils.py**
Utility condivise per tutti i test:
- `ServiceConfig`: Configurazione centralizzata (URL, database, timeout)
- `ServiceHealthCheck`: Verifica stato di tutti i servizi
- `APIClient`: Client HTTP per REST API
- `DatabaseHelper`: Query e operazioni su SQLite
- `TestDataGenerator`: Generatore di dati di test
- `TestReporter`: Formattazione e reporting risultati
- `Assertions`: Helper per assertions comuni
- `TestSession`: Tracking risultati test

### 2. **test_inventory.py**
Verifica componenti disponibili nel sistema:
- **TestWorkflowInventory**: Workflow disponibili (API + database)
- **TestNodeInventory**: Nodi PDK e loro schema
- **TestEventSourceInventory**: Event source configurati
- **TestTriggerInventory**: Trigger configurati e loro distribuzione
- **TestSystemInventorySummary**: Riepilogo completo

**Output**: Lista di quanti workflow, nodi, event source, trigger, documenti sono nel sistema.

### 3. **test_crud_operations.py**
Operazioni CRUD su dati:
- **TestDocumentCRUDOperations**: Create, read, update, delete documenti
- **TestDocumentMetadataCRUD**: Gestione metadati documenti
- **TestVectorstoreCRUDOperations**: Operazioni su vectorstore
- **TestDatabaseStatistics**: Statistiche database

**Output**: Verifica che CRUD funzioni su database, vectorstore e metadati.

### 4. **test_e2e_pipeline.py**
Test end-to-end completi:
- **TestFileMonitoringPipeline**: Health del folder monitor
- **TestEventProcessingPipeline**: Invio e processamento eventi
- **TestVectorstoreIntegration**: Embedding e ricerca semantica
- **TestDatabaseIntegrationPipeline**: Ciclo di vita documento
- **TestCompleteE2EPipeline**: Workflow completo file → search

**Output**: Verifica il flusso completo: Monitor → Backend → VectorStore → DB → Search.

## 🚀 Esecuzione Test

### Prerequisiti
```bash
# Installare pytest e dipendenze
pip install pytest requests
```

### Eseguire Tutti i Test
```bash
cd C:\PramaIA
pytest tests/ -v -s
```

### Eseguire Test Specifico
```bash
# Solo inventory
pytest tests/test_inventory.py -v -s

# Solo CRUD
pytest tests/test_crud_operations.py -v -s

# Solo E2E
pytest tests/test_e2e_pipeline.py -v -s

# Singolo test
pytest tests/test_inventory.py::TestWorkflowInventory::test_get_workflows_from_api -v -s
```

### Esecuzione con Report
```bash
# HTML report
pytest tests/ -v -s --html=report.html

# Coverage
pytest tests/ -v --cov=backend --cov-report=html

# JSON report (per automazione)
pytest tests/ -v --tb=short -o log_cli=true > test_results.json
```

## 📊 Output Esempi

### Test Inventory
```
================================================================================
  GET WORKFLOWS
================================================================================

Total workflows: 5

📋 Workflows disponibili:
ID                | Name                | Active | Category        | Tags
pdf_processing    | PDF Processing      | True   | document        | pdf
text_analysis     | Text Analysis       | True   | nlp             | text
metadata_extract  | Metadata Extractor  | False  | data            | meta
```

### Test CRUD
```
================================================================================
  CREATE DOCUMENT VIA API
================================================================================

Document created: doc_12345abc
Status: created

📋 Sample documents:
ID           | Filename              | Size  | Created
doc_12345abc | test_document_1234.pdf| 1024  | 2025-11-18T10:30
doc_98765def | report_nov_2025.pdf   | 2048  | 2025-11-18T09:15
```

### Test E2E
```
================================================================================
  COMPLETE E2E WORKFLOW
================================================================================

📋 E2E Test Steps:

1. Verifying services...
   ✅ Services online

2. Creating test document...
   ✅ Document created: doc_e2e_test_001

3. Waiting for background processing...
   ✅ Processing delay completed

4. Verifying document in database...
   ✅ Found in database

5. Verifying document in vectorstore...
   ✅ Found in vectorstore

6. Testing semantic search...
   ✅ Search executed: 3 results

✅ PASSED - Complete E2E Pipeline
  Total: 6 | Passed: 6 | Failed: 0 | Skipped: 0
```

## 🔧 Configurazione

### Variabili d'Ambiente
```bash
# Backend
BACKEND_URL=http://127.0.0.1:8000
DATABASE_URL=sqlite:///./PramaIAServer/backend/data/database.db

# PDK
PDK_SERVER_BASE_URL=http://127.0.0.1:3001

# VectorStore
VECTORSTORE_SERVICE_URL=http://127.0.0.1:8090

# Monitor Agent
MONITOR_AGENT_URL=http://127.0.0.1:8001

# LogService
PRAMAIALOG_URL=http://127.0.0.1:8081
```

## 📈 Metriche Controllate

### System Inventory
- ✅ Numero workflow configurati
- ✅ Numero nodi disponibili
- ✅ Numero event source
- ✅ Numero trigger attivi
- ✅ Numero documenti nel sistema

### CRUD Operations
- ✅ Create document (backend)
- ✅ Read metadata (database)
- ✅ Update metadata (database + API)
- ✅ Delete document
- ✅ Add to VectorStore
- ✅ Search VectorStore
- ✅ Database integrity

### E2E Pipeline
- ✅ File monitoring status
- ✅ Event processing
- ✅ Trigger execution
- ✅ Document embedding
- ✅ Semantic search
- ✅ Database sync
- ✅ Complete workflow: File → DB → VectorStore → Search

## 🐛 Debugging & Troubleshooting

### Se un test fallisce:

1. **Verificare servizi**: `ServiceHealthCheck.check_all()`
2. **Controllare logs**: Port 8081 ha dashboard log
3. **Verificare database**: 
   ```sql
   sqlite3 database.db "SELECT COUNT(*) FROM workflows;"
   ```
4. **Test manuale endpoint**:
   ```bash
   curl http://127.0.0.1:8000/health
   curl http://127.0.0.1:3001/api/nodes
   ```

### Comandi Utili

```bash
# Eseguire solo test che non falliscono
pytest tests/ -v --lf

# Eseguire solo test falliti precedentemente
pytest tests/ -v --ff

# Stop al primo fallimento
pytest tests/ -v -x

# Verbose error messages
pytest tests/ -v --tb=long

# Dry run (vedi cosa verrebbe eseguito)
pytest tests/ --collect-only
```

## 📝 Test Naming Convention

- `test_*`: Funzione di test
- `Test*`: Classe di test
- `test_get_*`: Test GET/read
- `test_create_*`: Test POST/create
- `test_update_*`: Test PUT/update
- `test_delete_*`: Test DELETE
- `test_*_e2e`: Test end-to-end

## 🔄 Continuous Integration

Test suite è progettata per CI/CD:

```yaml
# Esempio GitHub Actions
- name: Run Tests
  run: pytest tests/ -v --tb=short --json-report --json-report-file=report.json

- name: Upload Report
  uses: actions/upload-artifact@v2
  with:
    name: test-report
    path: report.json
```

## 📚 Fixture e Helpers Disponibili

### Fixture pytest
- `check_services`: Verifica servizi all'inizio
- `test_data`: Generator di dati test
- `test_session`: Tracking sessione test

### Helper Utilities
- `ServiceHealthCheck.check_all()`
- `APIClient.get/post/put/delete()`
- `DatabaseHelper.query/query_dict/execute()`
- `TestDataGenerator.generate_*_data()`
- `TestReporter.print_*()`
- `Assertions.assert_*()`

## 🚨 Expected Behavior

| Scenario | Expected | Fix |
|----------|----------|-----|
| Servizi offline | Skip test | Avviare servizi |
| Database vuoto | Pass (test data generation) | Normale |
| VectorStore offline | Fallback a DB | Avviare vectorstore |
| Trigger non esegue | Check event_type/conditions | Verificare trigger config |

## 📌 Best Practices

1. **Eseguire dopo deployment**: `pytest tests/ -v`
2. **Eseguire prima di merge**: `pytest tests/ -x` (stop al primo fallimento)
3. **Monitoring periodico**: Schedulare test settimanali
4. **Conservare report**: Tracciare trend nel tempo
5. **Aggiornare test**: Quando cambiano API o schema

---

**Last Updated**: 18 Novembre 2025  
**Version**: 1.0
