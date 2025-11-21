"""
Quick Test Execution Reference
Guida di riferimento rapida per esecuzione test
"""

# ============================================================================
# SETUP RAPIDO
# ============================================================================

# 1. Una sola volta: Installare dipendenze
pip install -r tests/requirements.txt

# ============================================================================
# ESECUZIONE TEST
# ============================================================================

# OPZIONE 1: Python (multipiattaforma)
python tests/run_tests.py all -v -s
python tests/run_tests.py inventory -v
python tests/run_tests.py crud -v
python tests/run_tests.py e2e -v

# OPZIONE 2: PowerShell (Windows)
.\tests\run_tests.ps1 -Suite all -Verbose -ShowOutput
.\tests\run_tests.ps1 -Suite inventory -Verbose
.\tests\run_tests.ps1 -Suite crud -Verbose
.\tests\run_tests.ps1 -Suite e2e -Verbose

# OPZIONE 3: pytest direttamente
pytest tests/ -v -s
pytest tests/test_inventory.py -v -s
pytest tests/test_crud_operations.py -v -s
pytest tests/test_e2e_pipeline.py -v -s

# ============================================================================
# TEST SPECIFICI
# ============================================================================

# Inventario Workflow
pytest tests/test_inventory.py::TestWorkflowInventory -v -s

# Inventario Nodi
pytest tests/test_inventory.py::TestNodeInventory -v -s

# Inventario Event Sources
pytest tests/test_inventory.py::TestEventSourceInventory -v -s

# Inventario Trigger
pytest tests/test_inventory.py::TestTriggerInventory -v -s

# CRUD Document
pytest tests/test_crud_operations.py::TestDocumentCRUDOperations -v -s

# CRUD Metadata
pytest tests/test_crud_operations.py::TestDocumentMetadataCRUD -v -s

# CRUD VectorStore
pytest tests/test_crud_operations.py::TestVectorstoreCRUDOperations -v -s

# End-to-End Completo
pytest tests/test_e2e_pipeline.py::TestCompleteE2EPipeline -v -s

# ============================================================================
# REPORT E DEBUG
# ============================================================================

# HTML Report
pytest tests/ -v --html=report.html

# Coverage Report
pytest tests/ -v --cov=backend --cov-report=html

# Stop al primo fallimento
pytest tests/ -x

# Solo test falliti precedentemente
pytest tests/ --lf

# Verbose error messages
pytest tests/ -v --tb=long

# ============================================================================
# OUTPUT ATTESO
# ============================================================================

# test_inventory.py output:
#   ✅ Elenca workflow, nodi, event source, trigger, documenti
#   ✅ Mostra tabelle riepilogative
#   ✅ Verifica schemi database

# test_crud_operations.py output:
#   ✅ Crea/Legge/Aggiorna/Elimina documenti
#   ✅ Gestisce metadati
#   ✅ Testa VectorStore
#   ✅ Verifica integrità database

# test_e2e_pipeline.py output:
#   ✅ Verifica monitoring folder
#   ✅ Processa eventi
#   ✅ Esegue workflow
#   ✅ Testa ricerca semantica
#   ✅ Sincronizzazione DB-VectorStore

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

# Se fallisce: Verificare servizi online
pytest tests/test_inventory.py::TestWorkflowInventory::test_get_workflows_from_api -v

# Controllare database
sqlite3 PramaIAServer/backend/data/database.db "SELECT COUNT(*) FROM workflows;"

# Health check manuale
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:3001/health
curl http://127.0.0.1:8090/health

# ============================================================================
# DOCUMENTAZIONE
# ============================================================================

# Guide disponibili:
# - PramaIA-Docs/README.md (Index)
# - PramaIA-Docs/ECOSYSTEM_OVERVIEW.md (Architecture)
# - PramaIA-Docs/TEST_SUITE_GUIDE.md (This suite)
# - tests/TEST_SUITE_README.md (Detailed)

# ============================================================================
