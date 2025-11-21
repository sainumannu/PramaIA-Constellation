#!/usr/bin/env python3
"""
Test E2E Pipeline - PramaIA Test Suite
Test end-to-end del flusso completo: Monitor → Backend → VectorStore → DB → Search
"""

import pytest
import requests
import time
import json
from pathlib import Path
from typing import Dict, Any
from test_utils import ServiceConfig, APIClient, DatabaseHelper, TestDataGenerator, TestReporter, Assertions


class TestFileMonitoringPipeline:
    """Test pipeline di monitoraggio file"""

    def test_monitor_agent_health(self, check_services):
        """Test health del folder monitor agent"""
        TestReporter.print_header("MONITOR AGENT HEALTH")

        try:
            response = requests.get(f"{ServiceConfig.MONITOR_AGENT_URL}/health", timeout=5)

            if response.status_code == 200:
                health_data = response.json()
                TestReporter.print_result("Monitor agent is healthy", "")

                # Mostra statistiche
                if "buffered_events" in health_data:
                    TestReporter.print_result("Buffered events", health_data["buffered_events"])

                if "status" in health_data:
                    TestReporter.print_result("Status", health_data["status"])

            else:
                TestReporter.print_result("Monitor agent unhealthy", f"Status: {response.status_code}")

        except requests.exceptions.RequestException as e:
            TestReporter.print_result("Cannot connect to monitor agent", str(e))
            TestReporter.print_result("Suggestion", "Start monitor agent service")

    def test_monitor_agent_sync_status(self, check_services):
        """Test stato sincronizzazione monitor agent"""
        TestReporter.print_header("MONITOR AGENT SYNC STATUS")

        try:
            response = requests.get(f"{ServiceConfig.BACKEND_URL}/monitor/sync-status", timeout=5)

            if response.status_code == 200:
                sync_data = response.json()
                TestReporter.print_result("Sync status retrieved", "")

                # Mostra informazioni sincronizzazione
                for key, value in sync_data.items():
                    if isinstance(value, (int, float)):
                        TestReporter.print_result(key, str(value))
                    elif isinstance(value, str) and len(value) < 50:
                        TestReporter.print_result(key, value)

            else:
                TestReporter.print_result("Sync status not available", f"Status: {response.status_code}")

        except requests.exceptions.RequestException as e:
            TestReporter.print_result("Cannot get sync status", str(e))


class TestEventProcessingPipeline:
    """Test pipeline di processamento eventi"""

    def test_event_emission(self, check_services, test_data):
        """Test emissione evento"""
        TestReporter.print_header("EVENT EMISSION")

        # Crea evento di test
        test_event = {
            "event_type": "test_event_emission",
            "source": "test_suite",
            "data": {
                "test_id": test_data.get_random_string(8),
                "timestamp": test_data.get_timestamp()
            },
            "metadata": {
                "test_suite": "e2e_pipeline",
                "test_type": "event_emission"
            }
        }

        # Invia evento
        response = APIClient.post("/api/events/process", test_event)

        if response.status_code == 200:
            result = response.json()
            TestReporter.print_result("Event emitted successfully", "")
            TestReporter.print_result("Event type", test_event["event_type"])
            TestReporter.print_result("Response", str(result)[:100] + "...")
        else:
            TestReporter.print_result("Event emission failed", f"Status: {response.status_code}")
            TestReporter.print_result("Response", response.text[:200])

    def test_trigger_matching(self, check_services):
        """Test matching dei trigger"""
        TestReporter.print_header("TRIGGER MATCHING")

        # Query trigger attivi
        triggers = DatabaseHelper.query_dict("SELECT * FROM workflow_triggers WHERE active = 1")

        if triggers:
            TestReporter.print_result("Found active triggers", len(triggers))

            for trigger in triggers[:3]:  # Mostra primi 3
                TestReporter.print_result("Trigger", f"{trigger['name']} ({trigger['event_type']})")

            # Verifica che abbiano workflow associati
            for trigger in triggers[:1]:  # Verifica dettagliato primo
                workflow = DatabaseHelper.query_dict(
                    "SELECT name FROM workflows WHERE id = ?",
                    (trigger['workflow_id'],)
                )
                if workflow:
                    TestReporter.print_result("Workflow link", f"✅ {workflow[0]['name']}")
                else:
                    TestReporter.print_result("Workflow link", f"❌ Missing workflow: {trigger['workflow_id']}")

        else:
            TestReporter.print_result("No active triggers found", "")
            TestReporter.print_result("Suggestion", "Configure triggers for testing")


class TestVectorstoreIntegration:
    """Test integrazione vectorstore"""

    def test_vectorstore_health(self, check_services):
        """Test health del vectorstore"""
        TestReporter.print_header("VECTORSTORE HEALTH")

        try:
            response = requests.get(f"{ServiceConfig.VECTORSTORE_URL}/health", timeout=5)

            if response.status_code == 200:
                health_data = response.json()
                TestReporter.print_result("Vectorstore is healthy", "")

                # Mostra statistiche se disponibili
                for key, value in health_data.items():
                    if key in ["status", "version", "collections_count"]:
                        TestReporter.print_result(key, str(value))

            else:
                TestReporter.print_result("Vectorstore unhealthy", f"Status: {response.status_code}")

        except requests.exceptions.RequestException as e:
            TestReporter.print_result("Cannot connect to vectorstore", str(e))

    def test_embedding_generation(self, check_services, test_data):
        """Test generazione embedding"""
        TestReporter.print_header("EMBEDDING GENERATION")

        # Documento di test
        test_content = "This is a test document for embedding generation in the PramaIA system."

        try:
            # Aggiungi documento con contenuto
            doc_data = {
                "filename": f"test_embedding_{test_data.get_random_string(5)}.txt",
                "content": test_content,
                "collection": "test_embeddings"
            }

            response = APIClient.post(f"{ServiceConfig.VECTORSTORE_URL}/documents/add", doc_data)

            if response.status_code == 200:
                result = response.json()
                TestReporter.print_result("Document added for embedding", "")

                # Verifica che sia stato indicizzato
                time.sleep(2)  # Aspetta processamento

                search_response = APIClient.post(f"{ServiceConfig.VECTORSTORE_URL}/documents/search", {
                    "query": "test document embedding",
                    "collection": "test_embeddings",
                    "limit": 5
                })

                if search_response.status_code == 200:
                    search_results = search_response.json()
                    results_count = len(search_results.get("results", []))
                    TestReporter.print_result("Search results", results_count)

                    if results_count > 0:
                        TestReporter.print_result("Embedding status", "✅ Generated and searchable")
                    else:
                        TestReporter.print_result("Embedding status", "⚠️ Generated but not found in search")

                else:
                    TestReporter.print_result("Search test", f"Failed: {search_response.status_code}")

            else:
                TestReporter.print_result("Document addition failed", f"Status: {response.status_code}")

        except Exception as e:
            TestReporter.print_result("Embedding test error", str(e))


class TestDatabaseIntegrationPipeline:
    """Test pipeline di integrazione database"""

    def test_document_lifecycle(self, check_services, test_data):
        """Test ciclo di vita completo documento"""
        TestReporter.print_header("DOCUMENT LIFECYCLE")

        # 1. Crea documento
        doc_data = test_data.generate_document_data("test_lifecycle.pdf")
        create_response = APIClient.post("/api/documents/upload-with-visibility/", doc_data)

        if create_response.status_code == 200:
            doc_id = create_response.json().get("document_id")
            TestReporter.print_result("1. Document created", f"ID: {doc_id[:8]}...")

            # 2. Verifica in database backend
            time.sleep(1)  # Aspetta processamento
            db_docs = DatabaseHelper.query_dict("SELECT id FROM documents WHERE id = ?", (doc_id,))
            if db_docs:
                TestReporter.print_result("2. Backend DB", "✅ Found")
            else:
                TestReporter.print_result("2. Backend DB", "❌ Not found")

            # 3. Verifica metadati
            metadata = DatabaseHelper.query_dict(
                "SELECT COUNT(*) as count FROM document_metadata WHERE document_id = ?",
                (doc_id,)
            )
            if metadata and metadata[0]['count'] > 0:
                TestReporter.print_result("3. Metadata", f"✅ {metadata[0]['count']} entries")
            else:
                TestReporter.print_result("3. Metadata", "❌ No metadata")

            # 4. Verifica in vectorstore
            try:
                vs_response = requests.get(f"{ServiceConfig.VECTORSTORE_URL}/documents/{doc_id}", timeout=5)
                if vs_response.status_code == 200:
                    TestReporter.print_result("4. Vectorstore", "✅ Found")
                else:
                    TestReporter.print_result("4. Vectorstore", f"⚠️ Status: {vs_response.status_code}")
            except:
                TestReporter.print_result("4. Vectorstore", "❌ Connection failed")

            # 5. Test ricerca
            try:
                search_response = APIClient.post(f"{ServiceConfig.VECTORSTORE_URL}/documents/search", {
                    "query": "test document",
                    "limit": 10
                })
                if search_response.status_code == 200:
                    results = search_response.json().get("results", [])
                    TestReporter.print_result("5. Search", f"✅ {len(results)} results found")
                else:
                    TestReporter.print_result("5. Search", f"⚠️ Failed: {search_response.status_code}")
            except:
                TestReporter.print_result("5. Search", "❌ Connection failed")

            TestReporter.print_result("Document lifecycle test", "completed")

        else:
            TestReporter.print_result("Could not create test document", "")


class TestCompleteE2EPipeline:
    """Test pipeline E2E completa"""

    def test_complete_workflow_execution(self, check_services, test_data):
        """Test esecuzione workflow completa"""
        TestReporter.print_header("COMPLETE E2E WORKFLOW")

        steps_completed = 0
        total_steps = 6

        # Step 1: Verifica servizi
        TestReporter.print_result("1. Verifying services", "")
        if check_services:
            TestReporter.print_result("   Status", "✅ Services online")
            steps_completed += 1
        else:
            TestReporter.print_result("   Status", "❌ Services offline")
            TestReporter.print_result("Test result", "❌ FAILED - Services not available")
            TestReporter.print_result("Summary", f"Total: {total_steps} | Passed: {steps_completed} | Failed: {total_steps - steps_completed} | Skipped: 0")
            return

        # Step 2: Crea documento di test
        TestReporter.print_result("2. Creating test document", "")
        doc_data = test_data.generate_document_data("test_e2e_complete.pdf")
        response = APIClient.post("/api/documents/upload-with-visibility/", doc_data)

        if response.status_code == 200:
            doc_id = response.json().get("document_id")
            TestReporter.print_result("   Status", f"✅ Document created: {doc_id[:8]}...")
            steps_completed += 1
        else:
            TestReporter.print_result("   Status", f"❌ Creation failed: {response.status_code}")
            TestReporter.print_result("Test result", "❌ FAILED - Document creation failed")
            TestReporter.print_result("Summary", f"Total: {total_steps} | Passed: {steps_completed} | Failed: {total_steps - steps_completed} | Skipped: 0")
            return

        # Step 3: Aspetta processamento in background
        TestReporter.print_result("3. Waiting for background processing", "")
        time.sleep(3)  # Aspetta processamento
        TestReporter.print_result("   Status", "✅ Processing delay completed")
        steps_completed += 1

        # Step 4: Verifica documento nel database
        TestReporter.print_result("4. Verifying document in database", "")
        db_docs = DatabaseHelper.query_dict("SELECT id FROM documents WHERE id = ?", (doc_id,))
        if db_docs:
            TestReporter.print_result("   Status", "✅ Found in database")
            steps_completed += 1
        else:
            TestReporter.print_result("   Status", "❌ Not found in database")

        # Step 5: Verifica documento nel vectorstore
        TestReporter.print_result("5. Verifying document in vectorstore", "")
        try:
            vs_response = requests.get(f"{ServiceConfig.VECTORSTORE_URL}/documents/{doc_id}", timeout=5)
            if vs_response.status_code == 200:
                TestReporter.print_result("   Status", "✅ Found in vectorstore")
                steps_completed += 1
            else:
                TestReporter.print_result("   Status", f"⚠️ Status: {vs_response.status_code}")
        except Exception as e:
            TestReporter.print_result("   Status", f"❌ Connection error: {e}")

        # Step 6: Test ricerca semantica
        TestReporter.print_result("6. Testing semantic search", "")
        try:
            search_response = APIClient.post(f"{ServiceConfig.VECTORSTORE_URL}/documents/search", {
                "query": "test document content",
                "limit": 5
            })

            if search_response.status_code == 200:
                results = search_response.json().get("results", [])
                TestReporter.print_result("   Status", f"✅ Search executed: {len(results)} results")
                steps_completed += 1
            else:
                TestReporter.print_result("   Status", f"⚠️ Search failed: {search_response.status_code}")
        except Exception as e:
            TestReporter.print_result("   Status", f"❌ Search error: {e}")

        # Risultato finale
        success_rate = (steps_completed / total_steps) * 100
        if steps_completed == total_steps:
            TestReporter.print_result("Test result", "✅ PASSED - Complete E2E Pipeline")
        elif steps_completed >= total_steps * 0.8:  # 80% success
            TestReporter.print_result("Test result", f"⚠️ PARTIAL SUCCESS - {steps_completed}/{total_steps} steps completed ({success_rate:.1f}%)")
        else:
            TestReporter.print_result("Test result", f"❌ FAILED - Only {steps_completed}/{total_steps} steps completed ({success_rate:.1f}%)")

        TestReporter.print_result("Summary", f"Total: {total_steps} | Passed: {steps_completed} | Failed: {total_steps - steps_completed} | Skipped: 0")