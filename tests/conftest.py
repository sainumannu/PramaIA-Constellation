"""
pytest Configuration
Configurazione pytest con fixtures riutilizzabili
"""

import sys
import os
from pathlib import Path

# Add tests directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from test_utils import ServiceHealthCheck, TestDataGenerator, TestSession, DatabaseHelper


@pytest.fixture(scope="session")
def check_services():
    """Fixture: Verifica servizi disponibili all'inizio della sessione"""
    health = ServiceHealthCheck.check_all()
    if not all(health.values()):
        pytest.skip("One or more services are not available")
    return health


@pytest.fixture
def test_data():
    """Fixture: Generator di dati test"""
    return TestDataGenerator()


@pytest.fixture
def test_session():
    """Fixture: Sessione di test per tracking risultati"""
    return TestSession("Test Session")


@pytest.fixture(scope="session")
def has_documents_table():
    """Fixture: Verifica se la tabella 'documents' esiste nel database"""
    try:
        result = DatabaseHelper.query("SELECT 1 FROM documents LIMIT 1")
        return True
    except Exception:
        return False


@pytest.fixture(scope="session", autouse=True)
def setup_session():
    """Setup iniziale della sessione di test"""
    print("\n" + "=" * 80)
    print("  PramaIA Test Suite - Starting")
    print("=" * 80)
    
    health = ServiceHealthCheck.check_all()
    
    if not all(health.values()):
        print("\n[WARNING] Some services are not available")
        print("The test suite will run but some tests may fail or be skipped\n")
    
    yield
    
    print("\n" + "=" * 80)
    print("  PramaIA Test Suite - Complete")
    print("=" * 80 + "\n")
