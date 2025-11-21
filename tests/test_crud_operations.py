#!/usr/bin/env python3
"""
Test CRUD Operations - PramaIA Test Suite
Test delle operazioni CRUD su documenti, metadati e vectorstore
"""

import pytest
import requests
import sqlite3
import json
from pathlib import Path
from typing import Dict, Any
from test_utils import ServiceConfig, APIClient, DatabaseHelper, TestDataGenerator, TestReporter, Assertions


class TestDocumentCRUDOperations:
    """Test operazioni CRUD sui documenti"""

    def test_create_document_via_api(self, check_services, test_data):
        """Test creazione documento via API"""
        TestReporter.print_header("CREATE DOCUMENT VIA API")

        # Crea documento di test
        doc_data = test_data.generate_document_data("test_crud_doc.pdf")

        # POST al backend
        response = APIClient.post("/api/documents/upload-with-visibility/", doc_data)

        if response.status_code == 200:
            result = response.json()
            doc_id = result.get("document_id")

            TestReporter.print_result("Document created", doc_id)
            TestReporter.print_result("Status", "created")
            TestReporter.print_result("Document ID", doc_id)

            # Verifica nel database
            db_docs = DatabaseHelper.query_dict("SELECT * FROM documents WHERE id = ?", (doc_id,))
            if db_docs:
                TestReporter.print_result("Database verification", "✅ Found in database")
            else:
                TestReporter.print_result("Database verification", "❌ Not found in database")

        else:
            TestReporter.print_result("API call failed", f"Status: {response.status_code}")
            TestReporter.print_result("Response", response.text)

    def test_read_document_metadata(self, check_services):
        """Test lettura metadati documento"""
        TestReporter.print_header("READ DOCUMENT METADATA")

        # Query documenti esistenti
        docs = DatabaseHelper.query_dict("SELECT id, filename FROM documents LIMIT 5")

        if docs:
            TestReporter.print_result("Found documents", len(docs))

            for doc in docs[:3]:  # Mostra primi 3
                TestReporter.print_result("Document", f"{doc['id'][:8]}... | {doc['filename']}")

            # Verifica metadati
            for doc in docs[:1]:  # Verifica dettagliato primo documento
                metadata = DatabaseHelper.query_dict(
                    "SELECT key, value FROM document_metadata WHERE document_id = ?",
                    (doc['id'],)
                )
                if metadata:
                    TestReporter.print_result("Metadata count", len(metadata))
                    for meta in metadata[:3]:
                        TestReporter.print_result("Metadata", f"{meta['key']}: {meta['value'][:50]}...")
        else:
            TestReporter.print_result("No documents found", "in database")

    def test_update_document_metadata(self, check_services, test_data):
        """Test aggiornamento metadati documento"""
        TestReporter.print_header("UPDATE DOCUMENT METADATA")

        # Trova documento esistente
        docs = DatabaseHelper.query_dict("SELECT id FROM documents LIMIT 1")

        if docs:
            doc_id = docs[0]['id']

            # Aggiorna metadati
            new_metadata = {
                "updated_by": "test_crud_operations",
                "last_modified": test_data.get_timestamp(),
                "test_marker": "crud_test_updated"
            }

            # Simula update via API (se disponibile)
            # Per ora aggiorniamo direttamente DB per test
            for key, value in new_metadata.items():
                DatabaseHelper.execute(
                    "INSERT OR REPLACE INTO document_metadata (document_id, key, value, value_type) VALUES (?, ?, ?, ?)",
                    (doc_id, key, value, "string")
                )

            TestReporter.print_result("Updated metadata for document", f"{doc_id[:8]}...")
            TestReporter.print_result("Metadata keys updated", len(new_metadata))

            # Verifica update
            updated = DatabaseHelper.query_dict(
                "SELECT key, value FROM document_metadata WHERE document_id = ? AND key IN (?, ?, ?)",
                (doc_id, "updated_by", "last_modified", "test_marker")
            )
            TestReporter.print_result("Verification", f"Found {len(updated)} updated keys")

        else:
            TestReporter.print_result("No documents available", "for update test")

    def test_delete_document(self, check_services, test_data):
        """Test cancellazione documento"""
        TestReporter.print_header("DELETE DOCUMENT")

        # Crea documento di test specifico per cancellazione
        doc_data = test_data.generate_document_data("test_delete_doc.pdf")
        response = APIClient.post("/api/documents/upload-with-visibility/", doc_data)

        if response.status_code == 200:
            doc_id = response.json().get("document_id")

            # Cancella documento
            delete_response = APIClient.delete(f"/api/documents/{doc_id}")

            if delete_response.status_code in [200, 204]:
                TestReporter.print_result("Document deleted", f"ID: {doc_id[:8]}...")

                # Verifica cancellazione
                remaining = DatabaseHelper.query_dict("SELECT id FROM documents WHERE id = ?", (doc_id,))
                if not remaining:
                    TestReporter.print_result("Database verification", "✅ Removed from database")
                else:
                    TestReporter.print_result("Database verification", "❌ Still in database")

            else:
                TestReporter.print_result("Delete failed", f"Status: {delete_response.status_code}")
        else:
            TestReporter.print_result("Could not create test document", "for deletion")


class TestDocumentMetadataCRUD:
    """Test operazioni CRUD sui metadati documenti"""

    def test_bulk_metadata_operations(self, check_services, test_data):
        """Test operazioni bulk sui metadati"""
        TestReporter.print_header("BULK METADATA OPERATIONS")

        # Trova documenti esistenti
        docs = DatabaseHelper.query_dict("SELECT id FROM documents LIMIT 3")

        if docs:
            # Operazioni bulk
            operations = 0
            for doc in docs:
                # Aggiungi metadati multipli
                metadata_items = [
                    ("bulk_test_key1", f"value_{test_data.get_random_string(5)}"),
                    ("bulk_test_key2", test_data.get_timestamp()),
                    ("bulk_test_key3", "bulk_operation_test")
                ]

                for key, value in metadata_items:
                    DatabaseHelper.execute(
                        "INSERT OR REPLACE INTO document_metadata (document_id, key, value, value_type) VALUES (?, ?, ?, ?)",
                        (doc['id'], key, value, "string")
                    )
                    operations += 1

            TestReporter.print_result("Performed metadata operations", operations)
            TestReporter.print_result("Documents updated", len(docs))

            # Verifica
            total_metadata = DatabaseHelper.query_dict(
                "SELECT COUNT(*) as count FROM document_metadata WHERE key LIKE 'bulk_test_%'"
            )
            if total_metadata:
                TestReporter.print_result("Total metadata entries", total_metadata[0]['count'])

        else:
            TestReporter.print_result("No documents available", "for bulk metadata test")


class TestVectorstoreCRUDOperations:
    """Test operazioni CRUD sul vectorstore"""

    def test_vectorstore_document_addition(self, check_services, test_data):
        """Test aggiunta documento al vectorstore"""
        TestReporter.print_header("VECTORSTORE DOCUMENT ADDITION")

        try:
            # Crea documento di test
            doc_data = test_data.generate_document_data("test_vectorstore.pdf")

            # Aggiungi al vectorstore
            response = APIClient.post(f"{ServiceConfig.VECTORSTORE_URL}/documents/add", {
                "filename": doc_data["filename"],
                "content": doc_data["content"],
                "collection": "test_collection"
            })

            if response.status_code == 200:
                result = response.json()
                TestReporter.print_result("Document added to vectorstore", "success")
                TestReporter.print_result("Response", str(result)[:100] + "...")
            else:
                TestReporter.print_result("Vectorstore add failed", f"Status: {response.status_code}")

        except Exception as e:
            TestReporter.print_result("Vectorstore test error", str(e))

    def test_vectorstore_search(self, check_services):
        """Test ricerca nel vectorstore"""
        TestReporter.print_header("VECTORSTORE SEARCH")

        try:
            # Query di ricerca
            search_query = {
                "query": "test document",
                "collection": "test_collection",
                "limit": 5
            }

            response = APIClient.post(f"{ServiceConfig.VECTORSTORE_URL}/documents/search", search_query)

            if response.status_code == 200:
                results = response.json()
                result_count = len(results.get("results", []))

                TestReporter.print_result("Search completed", f"{result_count} results")
                TestReporter.print_result("Query", search_query["query"])

                if result_count > 0:
                    for i, result in enumerate(results["results"][:3]):
                        TestReporter.print_result(f"Result {i+1}", f"Score: {result.get('score', 'N/A'):.3f}")

            else:
                TestReporter.print_result("Search failed", f"Status: {response.status_code}")

        except Exception as e:
            TestReporter.print_result("Search test error", str(e))


class TestDatabaseStatistics:
    """Test statistiche e integrità database"""

    def test_database_integrity_check(self, check_services):
        """Test integrità database"""
        TestReporter.print_header("DATABASE INTEGRITY CHECK")

        integrity_checks = []

        # Verifica foreign keys
        try:
            # Documents senza metadati orfani
            orphaned_docs = DatabaseHelper.query_dict("""
                SELECT d.id, d.filename
                FROM documents d
                LEFT JOIN document_metadata dm ON d.id = dm.document_id
                WHERE dm.document_id IS NULL
            """)

            if orphaned_docs:
                integrity_checks.append(f"⚠️ {len(orphaned_docs)} documents without metadata")
            else:
                integrity_checks.append("✅ All documents have metadata")

        except Exception as e:
            integrity_checks.append(f"❌ Integrity check failed: {e}")

        # Verifica workflow senza nodi
        try:
            empty_workflows = DatabaseHelper.query_dict("""
                SELECT w.id, w.name
                FROM workflows w
                LEFT JOIN workflow_nodes wn ON w.id = wn.workflow_id
                WHERE wn.workflow_id IS NULL AND w.is_active = 1
            """)

            if empty_workflows:
                integrity_checks.append(f"⚠️ {len(empty_workflows)} active workflows without nodes")
            else:
                integrity_checks.append("✅ All active workflows have nodes")

        except Exception as e:
            integrity_checks.append(f"❌ Workflow integrity check failed: {e}")

        # Report risultati
        TestReporter.print_result("Database integrity check completed", "")
        for check in integrity_checks:
            TestReporter.print_result("Check", check)

    def test_database_statistics(self, check_services):
        """Test raccolta statistiche database"""
        TestReporter.print_header("DATABASE STATISTICS")

        stats = {}

        # Conta documenti
        doc_count = DatabaseHelper.query_dict("SELECT COUNT(*) as count FROM documents")
        stats["Total Documents"] = doc_count[0]['count'] if doc_count else 0

        # Conta workflow
        wf_count = DatabaseHelper.query_dict("SELECT COUNT(*) as count FROM workflows")
        stats["Total Workflows"] = wf_count[0]['count'] if wf_count else 0

        # Conta trigger attivi
        trigger_count = DatabaseHelper.query_dict("SELECT COUNT(*) as count FROM workflow_triggers WHERE active = 1")
        stats["Active Triggers"] = trigger_count[0]['count'] if trigger_count else 0

        # Conta metadati
        meta_count = DatabaseHelper.query_dict("SELECT COUNT(*) as count FROM document_metadata")
        stats["Metadata Entries"] = meta_count[0]['count'] if meta_count else 0

        # Database size
        try:
            db_path = ServiceConfig.get_db_path()
            if Path(db_path).exists():
                size_mb = Path(db_path).stat().st_size / (1024 * 1024)
                stats["Database Size"] = ".2f"
        except:
            stats["Database Size"] = "Unknown"

        TestReporter.print_result("Database statistics collected", "")
        for key, value in stats.items():
            TestReporter.print_result(key, str(value))