"""
Test Utilities e Configuration
Helpers, fixtures e configurazione per test suite
"""

import os
import json
import requests
import sqlite3
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURAZIONE SERVIZI
# ============================================================================

class ServiceConfig:
    """Configurazione centralizzata per tutti i servizi"""
    
    # Endpoints
    BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
    PDK_SERVER_URL = os.getenv("PDK_SERVER_BASE_URL", "http://127.0.0.1:3001")
    VECTORSTORE_URL = os.getenv("VECTORSTORE_SERVICE_URL", "http://127.0.0.1:8090")
    LOG_SERVICE_URL = os.getenv("PRAMAIALOG_URL", "http://127.0.0.1:8081")
    MONITOR_AGENT_URL = os.getenv("MONITOR_AGENT_URL", "http://127.0.0.1:8001")
    
    # Database - Use absolute path based on workspace root
    _workspace_root = Path(__file__).parent.parent  # Go up from tests/ to workspace root
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_workspace_root}/PramaIAServer/backend/db/database.db")
    VECTORSTORE_DB_PATH = os.getenv("VECTORSTORE_DB_PATH", str(_workspace_root / "PramaIA-VectorstoreService/data"))
    
    # Timeout
    REQUEST_TIMEOUT = 30
    HEALTH_CHECK_TIMEOUT = 5
    
    @classmethod
    def get_db_path(cls) -> str:
        """Estrae il path dal DATABASE_URL"""
        if cls.DATABASE_URL.startswith("sqlite"):
            path_part = cls.DATABASE_URL.split("sqlite:///")[-1]
            # Ensure it's absolute and uses proper path separators
            if not os.path.isabs(path_part):
                path_part = str(cls._workspace_root / path_part)
            # Normalize path separators
            return os.path.normpath(path_part)
        return "database.db"


# ============================================================================
# HEALTH CHECK UTILITIES
# ============================================================================

class ServiceHealthCheck:
    """Verifica lo stato di tutti i servizi"""
    
    @staticmethod
    def check_backend() -> bool:
        """Verifica Backend PramaIAServer"""
        try:
            response = requests.get(
                f"{ServiceConfig.BACKEND_URL}/health",
                timeout=ServiceConfig.HEALTH_CHECK_TIMEOUT
            )
            logger.info(f"✅ Backend: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Backend unavailable: {e}")
            return False
    
    @staticmethod
    def check_pdk() -> bool:
        """Verifica PDK Server"""
        try:
            response = requests.get(
                f"{ServiceConfig.PDK_SERVER_URL}/health",
                timeout=ServiceConfig.HEALTH_CHECK_TIMEOUT
            )
            logger.info(f"✅ PDK: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ PDK unavailable: {e}")
            return False
    
    @staticmethod
    def check_vectorstore() -> bool:
        """Verifica VectorstoreService"""
        try:
            response = requests.get(
                f"{ServiceConfig.VECTORSTORE_URL}/health",
                timeout=ServiceConfig.HEALTH_CHECK_TIMEOUT
            )
            logger.info(f"✅ VectorStore: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ VectorStore unavailable: {e}")
            return False
    
    @staticmethod
    def check_log_service() -> bool:
        """Verifica LogService"""
        try:
            response = requests.get(
                f"{ServiceConfig.LOG_SERVICE_URL}/health",
                timeout=ServiceConfig.HEALTH_CHECK_TIMEOUT
            )
            logger.info(f"✅ LogService: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ LogService unavailable: {e}")
            return False
    
    @staticmethod
    def check_all() -> Dict[str, bool]:
        """Verifica tutti i servizi"""
        logger.info("🔍 Checking all services...")
        results = {
            "backend": ServiceHealthCheck.check_backend(),
            "pdk": ServiceHealthCheck.check_pdk(),
            "vectorstore": ServiceHealthCheck.check_vectorstore(),
            "log_service": ServiceHealthCheck.check_log_service(),
        }
        
        all_healthy = all(results.values())
        status = "✅ ALL HEALTHY" if all_healthy else "⚠️ SOME SERVICES DOWN"
        logger.info(f"{status}\n")
        
        return results


# ============================================================================
# REST API HELPERS
# ============================================================================

class APIClient:
    """Cliente HTTP per interagire con i servizi"""
    
    @staticmethod
    def get(url: str, headers: Optional[Dict] = None, timeout: int = None) -> requests.Response:
        """GET request"""
        timeout = timeout or ServiceConfig.REQUEST_TIMEOUT
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"GET {url} failed: {e}")
            raise
    
    @staticmethod
    def post(url: str, json_data: Dict = None, headers: Optional[Dict] = None, timeout: int = None) -> requests.Response:
        """POST request"""
        timeout = timeout or ServiceConfig.REQUEST_TIMEOUT
        try:
            response = requests.post(url, json=json_data, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"POST {url} failed: {e}")
            raise
    
    @staticmethod
    def put(url: str, json_data: Dict = None, headers: Optional[Dict] = None, timeout: int = None) -> requests.Response:
        """PUT request"""
        timeout = timeout or ServiceConfig.REQUEST_TIMEOUT
        try:
            response = requests.put(url, json=json_data, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"PUT {url} failed: {e}")
            raise
    
    @staticmethod
    def delete(url: str, headers: Optional[Dict] = None, timeout: int = None) -> requests.Response:
        """DELETE request"""
        timeout = timeout or ServiceConfig.REQUEST_TIMEOUT
        try:
            response = requests.delete(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"DELETE {url} failed: {e}")
            raise
    
    @staticmethod
    def post_multipart(url: str, files: Optional[Union[Dict, List]] = None, data: Optional[Dict] = None, headers: Optional[Dict] = None, timeout: Optional[int] = None) -> requests.Response:
        """POST multipart/form-data request (for file uploads)"""
        timeout = timeout or ServiceConfig.REQUEST_TIMEOUT
        try:
            response = requests.post(url, files=files, data=data, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"POST multipart {url} failed: {e}")
            raise
    
    @staticmethod
    def login(username: str = "admin", password: str = "admin") -> Optional[str]:
        """Esegue login e ritorna il token JWT"""
        try:
            url = f"{ServiceConfig.BACKEND_URL}/auth/token/local"
            response = requests.post(
                url,
                data={"username": username, "password": password},
                timeout=ServiceConfig.REQUEST_TIMEOUT
            )
            if response.status_code == 200:
                token_data = response.json()
                token = token_data.get("access_token")
                logger.info(f"✅ Login successful for user: {username}")
                return token
            else:
                logger.error(f"❌ Login failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return None
    
    @staticmethod
    def get_auth_headers(token: str) -> Dict:
        """Ritorna headers con Authorization token"""
        return {"Authorization": f"Bearer {token}"}


# ============================================================================
# DATABASE HELPERS
# ============================================================================

class DatabaseHelper:
    """Helper per operazioni su database SQLite"""
    
    @staticmethod
    def get_connection():
        """Ottiene connessione al database"""
        db_path = ServiceConfig.get_db_path()
        logger.debug(f"Connecting to database: {db_path}")
        return sqlite3.connect(db_path)
    
    @staticmethod
    def query(sql: str, params: tuple = ()) -> List[Any]:
        """Esegue query SELECT"""
        conn = DatabaseHelper.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            results = cursor.fetchall()
            logger.debug(f"Query returned {len(results)} rows")
            return results
        finally:
            conn.close()
    
    @staticmethod
    def query_dict(sql: str, params: tuple = ()) -> List[Dict]:
        """Esegue query e ritorna lista di dict"""
        conn = DatabaseHelper.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            results = [dict(row) for row in cursor.fetchall()]
            logger.debug(f"Query returned {len(results)} rows")
            return results
        finally:
            conn.close()
    
    @staticmethod
    def execute(sql: str, params: tuple = ()) -> int:
        """Esegue INSERT/UPDATE/DELETE"""
        conn = DatabaseHelper.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            conn.commit()
            logger.debug(f"Executed: {sql}")
            return cursor.rowcount
        finally:
            conn.close()
    
    @staticmethod
    def count_table(table_name: str) -> int:
        """Conta righe in una tabella"""
        results = DatabaseHelper.query(f"SELECT COUNT(*) FROM {table_name}")
        return results[0][0] if results else 0
    
    @staticmethod
    def get_table_schema(table_name: str) -> List[Dict]:
        """Ottiene schema di una tabella"""
        results = DatabaseHelper.query_dict(f"PRAGMA table_info({table_name})")
        return results


# ============================================================================
# DATA GENERATION HELPERS
# ============================================================================

class TestDataGenerator:
    """Generatore di dati di test"""
    
    @staticmethod
    def generate_document_data(filename: str = "test_document.pdf") -> Dict:
        """Genera dati documento di test"""
        return {
            "filename": filename,
            "content": "Test document content for testing purposes",
            "content_type": "application/pdf",
            "file_size": 1024,
            "metadata": {
                "author": "Test Author",
                "title": "Test Document",
                "created_date": datetime.utcnow().isoformat()
            }
        }
    
    @staticmethod
    def generate_trigger_data(workflow_id: str = "test_workflow") -> Dict:
        """Genera dati trigger di test"""
        return {
            "name": f"Test Trigger - {datetime.utcnow().isoformat()}",
            "event_type": "pdf_file_added",
            "source": "pdf-monitor-event-source",
            "workflow_id": workflow_id,
            "conditions": {
                "filename_pattern": "*.pdf",
                "max_size": 10485760
            },
            "active": True
        }
    
    @staticmethod
    def generate_event_data(event_type: str = "pdf_file_added") -> Dict:
        """Genera dati evento di test"""
        return {
            "event_type": event_type,
            "source": "pdf-monitor-event-source",
            "data": {
                "filename": "test_document.pdf",
                "file_path": "/test/test_document.pdf",
                "file_size": 1024,
                "content_type": "application/pdf"
            },
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "source_folder": "/test",
                "agent_id": "test-agent"
            }
        }
    
    @staticmethod
    def generate_workflow_data(workflow_id: str = "test_workflow") -> Dict:
        """Genera dati workflow di test"""
        return {
            "workflow_id": workflow_id,
            "name": f"Test Workflow - {datetime.utcnow().isoformat()}",
            "description": "Test workflow for testing purposes",
            "is_active": True,
            "is_public": True,
            "category": "test",
            "tags": ["test", "debug"],
            "nodes": [],
            "connections": []
        }


# ============================================================================
# REPORTING & FORMATTING
# ============================================================================

class TestReporter:
    """Helper per reporting dei risultati"""
    
    @staticmethod
    def print_header(title: str, level: int = 1):
        """Stampa header"""
        markers = ["=" * 80, "-" * 80, "~" * 80]
        marker = markers[min(level - 1, len(markers) - 1)]
        print(f"\n{marker}")
        print(f"  {title}")
        print(f"{marker}\n")
    
    @staticmethod
    def print_result(name: str, value: Any, indent: int = 0):
        """Stampa un risultato"""
        prefix = "  " * indent
        if isinstance(value, (dict, list)):
            print(f"{prefix}{name}:")
            print(f"{prefix}  {json.dumps(value, indent=2, ensure_ascii=False)}")
        else:
            print(f"{prefix}{name}: {value}")
    
    @staticmethod
    def print_table(headers: List[str], rows: List[List[Any]]):
        """Stampa una tabella formattata"""
        # Calcola larghezze colonne
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Intestazione
        header_line = " | ".join(f"{h:{w}}" for h, w in zip(headers, col_widths))
        separator = "-+-".join("-" * w for w in col_widths)
        print(header_line)
        print(separator)
        
        # Righe
        for row in rows:
            print(" | ".join(f"{str(cell):{w}}" for cell, w in zip(row, col_widths)))
    
    @staticmethod
    def print_summary(test_name: str, total: int, passed: int, failed: int, skipped: int = 0):
        """Stampa riepilogo test"""
        status = "✅ PASSED" if failed == 0 else "❌ FAILED"
        print(f"\n{status} - {test_name}")
        print(f"  Total: {total} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")


# ============================================================================
# ASSERTION HELPERS
# ============================================================================

class Assertions:
    """Helper per assertions comuni"""
    
    @staticmethod
    def assert_status_code(response: requests.Response, expected: int, message: str = ""):
        """Verifica status code"""
        assert response.status_code == expected, \
            f"Expected {expected}, got {response.status_code}. {message}\nResponse: {response.text}"
    
    @staticmethod
    def assert_has_key(obj: Dict, key: str, message: str = ""):
        """Verifica chiave esiste"""
        assert key in obj, f"Key '{key}' not found in object. {message}\nObject: {obj}"
    
    @staticmethod
    def assert_not_empty(collection: List, message: str = ""):
        """Verifica collezione non vuota"""
        assert len(collection) > 0, f"Collection is empty. {message}"
    
    @staticmethod
    def assert_type(obj: Any, expected_type: type, message: str = ""):
        """Verifica tipo oggetto"""
        assert isinstance(obj, expected_type), \
            f"Expected {expected_type}, got {type(obj)}. {message}"


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

class TestSession:
    """Gestisce sessione di test"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = datetime.utcnow()
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def record_pass(self):
        """Registra test passato"""
        self.results["total"] += 1
        self.results["passed"] += 1
    
    def record_failure(self, error: str):
        """Registra test fallito"""
        self.results["total"] += 1
        self.results["failed"] += 1
        self.results["errors"].append(error)
    
    def summary(self):
        """Ritorna riepilogo sessione"""
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        return {
            "test_name": self.test_name,
            "duration_seconds": duration,
            **self.results
        }
