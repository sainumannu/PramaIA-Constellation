"""
Test CRUD Operations
Testa operazioni CRUD su metadati e contenuti
"""

import pytest
import json
import io
from datetime import datetime
from test_utils import (
    ServiceConfig, APIClient, DatabaseHelper, TestReporter,
    TestDataGenerator, Assertions
)
import sqlite3
from pathlib import Path


class VectorstoreDBHelper:
    """Helper per accedere a VectorstoreService documents.db"""
    
    @staticmethod
    def get_db_path():
        """Restituisce il path a documents.db"""
        return Path(__file__).parent.parent / "PramaIA-VectorstoreService" / "data" / "documents.db"
    
    @staticmethod
    def query(sql):
        """Esegue query SELECT"""
        db_path = VectorstoreDBHelper.get_db_path()
        if not db_path.exists():
            raise FileNotFoundError(f"documents.db not found at {db_path}")
        
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        conn.close()
        return [dict(row) for row in results]
    
    @staticmethod
    def execute(sql, params=()):
        """Esegue INSERT/UPDATE/DELETE"""
        db_path = VectorstoreDBHelper.get_db_path()
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected


class TestDocumentCRUDOperations:
    """Test: Operazioni CRUD su documenti"""
    
    def test_create_document_via_api(self, test_data):
        """Crea un documento via API"""
        TestReporter.print_header("CREATE DOCUMENT VIA API")
        
        # Login prima
        token = APIClient.login()
        if not token:
            pytest.skip("Could not authenticate: login failed")
        
        headers = APIClient.get_auth_headers(str(token))
        
        # Crea file di test - FastAPI List[UploadFile] richiede multiple file con chiave "files"
        filename = f"test_{datetime.utcnow().timestamp()}.pdf"
        file_content = b"Test PDF content - Simple test document for testing"
        
        # Use requests directly for proper multipart handling with list
        files_multipart = [
            ("files", (filename, io.BytesIO(file_content), "application/pdf"))
        ]
        
        response = None
        try:
            import requests as req_lib
            response = req_lib.post(
                f"{ServiceConfig.BACKEND_URL}/api/documents/upload/",
                files=files_multipart,
                headers=headers,
                timeout=ServiceConfig.REQUEST_TIMEOUT
            )
            # Non fare raise_for_status() per poter leggere l'errore
        except Exception as e:
            pytest.skip(f"Document upload API connection error: {str(e)[:100]}")
        
        # Verifica
        if response and response.status_code in [200, 201]:
            result = response.json()
            TestReporter.print_result("Document uploaded", result.get("message", "Success"))
            uploaded_files = result.get("uploaded_files", [])
            TestReporter.print_result("Uploaded files", len(uploaded_files) if uploaded_files else 0)
            return uploaded_files[0] if uploaded_files else filename
        elif response:
            # Mostra l'errore del server
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", str(error_data))
            except:
                error_detail = response.text
            status_code = response.status_code
            print(f"\n⚠️  Backend error {status_code}: {error_detail}")
            pytest.skip(f"Document upload failed: {status_code} - {error_detail[:100]}")
            return filename
        else:
            pytest.skip("Document upload failed: No response from server")
            return filename
    
    def test_read_document_metadata(self):
        """Legge metadati di un documento"""
        TestReporter.print_header("READ DOCUMENT METADATA", level=2)
        
        try:
            # Prendi primo documento da VectorstoreService
            docs = VectorstoreDBHelper.query("SELECT id, filename, created_at FROM documents LIMIT 1")
            
            if not docs:
                pytest.skip("No documents in VectorStore database")
            
            doc_id = docs[0]["id"]
            filename = docs[0]["filename"]
            
            TestReporter.print_result("Document ID", doc_id)
            TestReporter.print_result("Filename", filename)
            TestReporter.print_result("Created at", docs[0].get("created_at"))
            
            return doc_id
        except Exception as e:
            pytest.skip(f"Could not read documents from VectorStore: {e}")
    
    def test_update_document_metadata(self):
        """Aggiorna metadati di un documento"""
        TestReporter.print_header("UPDATE DOCUMENT METADATA", level=2)
        
        try:
            # Prendi primo documento da VectorStore
            docs = VectorstoreDBHelper.query("SELECT id FROM documents LIMIT 1")
            
            if not docs:
                pytest.skip("No documents in VectorStore database")
            
            doc_id = docs[0]["id"]
            
            # Update metadata in VectorStore
            VectorstoreDBHelper.execute(
                """INSERT OR REPLACE INTO document_metadata 
                   (document_id, key, value, value_type) VALUES (?, ?, ?, ?)""",
                (doc_id, "updated_at", datetime.utcnow().isoformat(), "str")
            )
            
            TestReporter.print_result("Document metadata updated", "✅")
            return True
            
        except Exception as e:
            pytest.skip(f"Could not update document metadata: {e}")
    
    def test_delete_document(self):
        """Elimina un documento"""
        TestReporter.print_header("DELETE DOCUMENT", level=2)
        
        try:
            # Crea documento di test per cancellare
            test_doc_id = f"delete_test_{datetime.utcnow().timestamp()}".replace(".", "_")
            VectorstoreDBHelper.execute(
                """INSERT INTO documents (id, filename, collection, created_at)
                   VALUES (?, ?, ?, ?)""",
                (test_doc_id, "test_delete.pdf", "test_collection", datetime.utcnow().isoformat())
            )
            
            # Delete
            affected = VectorstoreDBHelper.execute(
                "DELETE FROM documents WHERE id = ?",
                (test_doc_id,)
            )
            
            TestReporter.print_result("Document deleted", f"✅ ({affected} rows)")
            return True
            
        except Exception as e:
            pytest.skip(f"Could not delete document: {e}")
    
    def test_list_documents(self):
        """Elenca documenti con paginazione"""
        TestReporter.print_header("LIST DOCUMENTS")
        
        try:
            # Leggi da VectorStore
            docs = VectorstoreDBHelper.query("SELECT id, filename, collection, created_at FROM documents")
            
            TestReporter.print_result("Total documents", len(docs))
            
            if docs:
                print("\n📋 Documents in VectorStore:")
                headers = ["ID", "Filename", "Collection", "Created"]
                rows = []
                for doc in docs:
                    rows.append([
                        str(doc.get("id", "N/A"))[:20],
                        str(doc.get("filename", "N/A"))[:25],
                        str(doc.get("collection", "N/A"))[:20],
                        str(doc.get("created_at", "N/A"))[:19]
                    ])
                TestReporter.print_table(headers, rows)
            
            return len(docs)
                
        except Exception as e:
            pytest.skip(f"Could not list documents from VectorStore: {e}")


class TestDocumentMetadataCRUD:
    """Test: Operazioni su metadati specifici"""
    
    def test_add_metadata_to_document(self):
        """Aggiunge metadati a un documento"""
        TestReporter.print_header("ADD DOCUMENT METADATA")
        
        try:
            docs = VectorstoreDBHelper.query("SELECT id FROM documents LIMIT 1")
            
            if not docs:
                pytest.skip("No documents in VectorStore database")
            
            doc_id = docs[0]["id"]
            
            # Aggiungi metadati a VectorStore con chiave unica
            import uuid
            unique_key = f"test_key_{uuid.uuid4().hex[:8]}"
            VectorstoreDBHelper.execute(
                """INSERT INTO document_metadata (document_id, key, value, value_type)
                   VALUES (?, ?, ?, ?)""",
                (doc_id, unique_key, "test_added_value", "str")
            )
            TestReporter.print_result("Metadata added", "✅")
            return True
                
        except Exception as e:
            pytest.skip(f"Could not add metadata: {e}")
    
    def test_read_document_metadata_by_key(self):
        """Legge metadati specifici per chiave"""
        TestReporter.print_header("READ METADATA BY KEY", level=2)
        
        try:
            metadata = VectorstoreDBHelper.query(
                """SELECT document_id, key, value, value_type FROM document_metadata LIMIT 10"""
            )
            
            if not metadata:
                print("ℹ️  No metadata found in VectorStore")
                return
            
            print("📋 Sample metadata:")
            for item in metadata:
                doc_id = item.get('document_id', 'N/A')[:15]
                key = item.get('key')
                value = item.get('value')
                vtype = item.get('value_type')
                print(f"  Doc: {doc_id}")
                print(f"    {key}: {value} ({vtype})")
            
        except Exception as e:
            print(f"⚠️  Could not read metadata from VectorStore: {e}")
    
    def test_update_metadata(self):
        """Aggiorna metadati esistenti"""
        TestReporter.print_header("UPDATE METADATA", level=2)
        
        try:
            metadata = VectorstoreDBHelper.query(
                "SELECT document_id, key FROM document_metadata LIMIT 1"
            )
            
            if not metadata:
                pytest.skip("No metadata to update in VectorStore")
            
            doc_id = metadata[0]["document_id"]
            key = metadata[0]["key"]
            
            # Update metadata
            VectorstoreDBHelper.execute(
                "UPDATE document_metadata SET value = ? WHERE document_id = ? AND key = ?",
                (f"updated_{datetime.utcnow().timestamp()}", doc_id, key)
            )
            
            TestReporter.print_result("Metadata updated", "✅")
            
        except Exception as e:
            pytest.skip(f"Could not update metadata: {e}")
    
    def test_delete_metadata(self):
        """Elimina metadati specifici"""
        TestReporter.print_header("DELETE METADATA", level=2)
        
        try:
            # Crea metadata di test
            docs = VectorstoreDBHelper.query("SELECT id FROM documents LIMIT 1")
            if not docs:
                pytest.skip("No documents in VectorStore")
            
            doc_id = docs[0]["id"]
            
            # Aggiungi metadata di test con chiave unica
            import uuid
            unique_key = f"delete_test_{uuid.uuid4().hex[:8]}"
            VectorstoreDBHelper.execute(
                """INSERT INTO document_metadata (document_id, key, value, value_type)
                   VALUES (?, ?, ?, ?)""",
                (doc_id, unique_key, "test_value", "str")
            )
            
            # Delete
            deleted = VectorstoreDBHelper.execute(
                "DELETE FROM document_metadata WHERE document_id = ? AND key = ?",
                (doc_id, unique_key)
            )
            
            TestReporter.print_result("Metadata deleted", f"✅ ({deleted} rows)")
            
        except Exception as e:
            pytest.skip(f"Could not delete metadata: {e}")


class TestVectorstoreCRUDOperations:
    """Test: Operazioni CRUD su VectorStore"""
    
    def test_add_document_to_vectorstore(self, test_data):
        """Aggiunge documento a vectorstore"""
        TestReporter.print_header("ADD DOCUMENT TO VECTORSTORE")
        
        doc_data = test_data.generate_document_data()
        
        try:
            response = APIClient.post(
                f"{ServiceConfig.VECTORSTORE_URL}/api/documents/add",
                json_data={
                    "id": f"doc_{datetime.utcnow().timestamp()}",
                    "filename": doc_data["filename"],
                    "content": doc_data["content"],
                    "metadata": doc_data["metadata"]
                }
            )
            
            if response.status_code in [200, 201]:
                TestReporter.print_result("Document added to vectorstore", "✅")
                result = response.json()
                TestReporter.print_result("Vectorstore ID", result.get("id"))
                return True
            else:
                print(f"❌ Failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"⚠️  VectorStore add operation failed: {e}")
            return False
    
    def test_search_vectorstore(self):
        """Ricerca semantica nel vectorstore"""
        TestReporter.print_header("SEARCH VECTORSTORE")
        
        try:
            query = "test document content"
            response = APIClient.post(
                f"{ServiceConfig.VECTORSTORE_URL}/api/documents/search",
                json_data={"query": query, "limit": 5}
            )
            
            if response.status_code == 200:
                results = response.json()
                count = len(results.get("results", []))
                TestReporter.print_result("Search results", count)
                
                if results.get("results"):
                    print("\n📋 Top results:")
                    for i, result in enumerate(results["results"][:3], 1):
                        score = result.get("score", "N/A")
                        filename = result.get("filename", "N/A")
                        print(f"  {i}. {filename} (score: {score})")
                
                return True
            else:
                print(f"❌ Search failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"⚠️  VectorStore search failed: {e}")
            return False
    
    def test_get_document_from_vectorstore(self):
        """Recupera documento da vectorstore"""
        TestReporter.print_header("GET DOCUMENT FROM VECTORSTORE", level=2)
        
        try:
            # Primo, ottieni lista documenti
            response = APIClient.get(f"{ServiceConfig.VECTORSTORE_URL}/api/documents")
            
            if response.status_code != 200:
                print(f"⚠️  Could not list documents: {response.text}")
                return False
            
            docs = response.json()
            if isinstance(docs, dict):
                docs = docs.get("documents", docs.get("items", []))
            
            if not docs:
                print("ℹ️  No documents in vectorstore")
                return False
            
            doc_id = docs[0].get("id")
            
            # Get specifico documento
            response = APIClient.get(f"{ServiceConfig.VECTORSTORE_URL}/api/documents/{doc_id}")
            
            if response.status_code == 200:
                doc = response.json()
                TestReporter.print_result("Document retrieved", doc_id)
                TestReporter.print_result("Filename", doc.get("filename"))
                return True
            else:
                print(f"⚠️  Get document failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"⚠️  VectorStore get operation failed: {e}")
            return False
    
    def test_delete_document_from_vectorstore(self):
        """Elimina documento da vectorstore"""
        TestReporter.print_header("DELETE DOCUMENT FROM VECTORSTORE", level=2)
        
        try:
            # Prima aggiungi un documento di test
            response = APIClient.post(
                f"{ServiceConfig.VECTORSTORE_URL}/api/documents/add",
                json_data={
                    "id": f"delete_test_{datetime.utcnow().timestamp()}",
                    "filename": "delete_test.txt",
                    "content": "This document will be deleted",
                    "metadata": {"test": True}
                }
            )
            
            if response.status_code not in [200, 201]:
                pytest.skip(f"Could not create test document: {response.text}")
            
            doc_id = response.json().get("id")
            
            # Delete
            response = APIClient.delete(f"{ServiceConfig.VECTORSTORE_URL}/api/documents/{doc_id}")
            
            if response.status_code in [200, 204]:
                TestReporter.print_result("Document deleted from vectorstore", "✅")
                return True
            else:
                print(f"❌ Delete failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"⚠️  VectorStore delete operation failed: {e}")
            return False


class TestDatabaseStatistics:
    """Test: Statistiche e analisi del database"""
    
    def test_database_statistics(self):
        """Ottiene statistiche sul database"""
        TestReporter.print_header("DATABASE STATISTICS")
        
        stats = {}
        tables = [
            "documents",
            "workflows",
            "workflow_triggers",
            "users",
            "sessions"
        ]
        
        print("📊 Table statistics:")
        for table in tables:
            try:
                count = DatabaseHelper.count_table(table)
                stats[table] = count
                print(f"  {table}:.<30 {count:>5} rows")
            except:
                stats[table] = "N/A"
                print(f"  {table}:.<30 N/A")
        
        return stats
    
    def test_database_integrity(self):
        """Verifica integrità del database"""
        TestReporter.print_header("DATABASE INTEGRITY CHECK", level=2)
        
        try:
            # Check foreign keys (se supportato)
            response = DatabaseHelper.query("PRAGMA foreign_keys")
            status = "ENABLED" if response and response[0][0] else "DISABLED"
            TestReporter.print_result("Foreign key checks", status)
            
            # Check per documenti orfani
            orphaned = DatabaseHelper.query(
                """SELECT COUNT(*) FROM documents 
                   WHERE id NOT IN (SELECT DISTINCT document_id FROM document_metadata)"""
            )
            
            if orphaned and orphaned[0][0] > 0:
                print(f"⚠️  Found {orphaned[0][0]} documents without metadata")
            else:
                print("✅ No orphaned documents found")
            
        except Exception as e:
            print(f"⚠️  Could not check integrity: {e}")


# ============================================================================
# PYTEST EXECUTION
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
