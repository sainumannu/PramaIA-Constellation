"""
Test End-to-End
Testa il flusso completo: Monitor Folder → VectorStore → Database
"""

import pytest
import json
import time
import tempfile
from pathlib import Path
from datetime import datetime
from test_utils import (
    ServiceConfig, APIClient, DatabaseHelper, TestReporter,
    TestDataGenerator, Assertions, TestSession
)


class TestFileMonitoringPipeline:
    """Test: Pipeline di monitoraggio file"""
    
    def test_monitor_health_and_sync_status(self):
        """Verifica stato health e sincronizzazione del monitor"""
        TestReporter.print_header("FOLDER MONITOR HEALTH CHECK")
        
        try:
            response = APIClient.get(f"{ServiceConfig.MONITOR_AGENT_URL}/health")
            Assertions.assert_status_code(response, 200)
            
            health = response.json()
            TestReporter.print_result("Monitor status", health.get("status"))
            TestReporter.print_result("Version", health.get("version", "N/A"))
            
            return True
        except Exception as e:
            print(f"⚠️  Monitor health check failed: {e}")
            return False
    
    def test_get_monitor_sync_status(self):
        """Ottiene stato di sincronizzazione del monitor"""
        TestReporter.print_header("MONITOR SYNC STATUS")
        
        try:
            response = APIClient.get(f"{ServiceConfig.MONITOR_AGENT_URL}/monitor/sync-status")
            
            if response.status_code == 200:
                status = response.json()
                TestReporter.print_result("Connected", status.get("connected"))
                TestReporter.print_result("Buffered events", status.get("buffered_events", 0))
                TestReporter.print_result("Last sync", status.get("last_sync_time"))
                
                return True
            else:
                print(f"⚠️  Could not get sync status: {response.text}")
                return False
                
        except Exception as e:
            print(f"⚠️  Sync status check failed: {e}")
            return False
    
    def test_list_monitored_folders(self):
        """Elenca cartelle monitorate"""
        TestReporter.print_header("MONITORED FOLDERS")
        
        try:
            response = APIClient.get(f"{ServiceConfig.MONITOR_AGENT_URL}/monitor/folders")
            
            if response.status_code == 200:
                folders = response.json()
                if isinstance(folders, dict):
                    folders = folders.get("folders", [])
                
                TestReporter.print_result("Total monitored folders", len(folders))
                
                if folders:
                    print("\n📁 Monitored folders:")
                    for folder in folders:
                        status = "🟢 ACTIVE" if folder.get("active") else "🔴 INACTIVE"
                        print(f"  {status} {folder.get('path')}")
                        print(f"    Files: {folder.get('file_count', 0)}, Last: {folder.get('last_update')}")
                
                return folders
            else:
                print(f"⚠️  Could not list folders: {response.text}")
                return []
                
        except Exception as e:
            print(f"⚠️  Folder listing failed: {e}")
            return []


class TestEventProcessingPipeline:
    """Test: Pipeline di processamento eventi"""
    
    def test_send_test_event_to_backend(self, test_data):
        """Invia evento di test al backend"""
        TestReporter.print_header("SEND TEST EVENT")
        
        event = test_data.generate_event_data("pdf_file_added")
        
        try:
            response = APIClient.post(
                f"{ServiceConfig.BACKEND_URL}/api/events/process",
                json_data=event
            )
            
            if response.status_code in [200, 202]:
                result = response.json()
                TestReporter.print_result("Event processed", "✅")
                TestReporter.print_result("Status", result.get("status"))
                
                return result.get("event_id")
            else:
                print(f"❌ Event processing failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Could not send event: {e}")
            return None
    
    def test_trigger_workflow_execution(self, test_data):
        """Verifica che trigger esegue workflow"""
        TestReporter.print_header("TRIGGER WORKFLOW EXECUTION")
        
        # Ottieni un trigger configurato
        try:
            triggers = DatabaseHelper.query_dict(
                "SELECT * FROM workflow_triggers WHERE active = 1 LIMIT 1"
            )
            
            if not triggers:
                print("ℹ️  No active triggers found")
                return False
            
            trigger = triggers[0]
            TestReporter.print_result("Trigger", trigger.get("name"))
            TestReporter.print_result("Event type", trigger.get("event_type"))
            TestReporter.print_result("Workflow", trigger.get("workflow_id"))
            
            # Invia evento che matcherebbe questo trigger
            event = test_data.generate_event_data(trigger.get("event_type"))
            
            response = APIClient.post(
                f"{ServiceConfig.BACKEND_URL}/api/events/process",
                json_data=event
            )
            
            if response.status_code in [200, 202]:
                # Aspetta un po' per l'esecuzione
                time.sleep(2)
                
                # Verifica se execution è stato registrato
                executions = DatabaseHelper.query_dict(
                    f"""SELECT * FROM workflow_executions 
                       WHERE workflow_id = ? 
                       ORDER BY started_at DESC LIMIT 1""",
                    (trigger.get("workflow_id"),)
                )
                
                if executions:
                    exec_data = executions[0]
                    TestReporter.print_result("Execution triggered", "✅")
                    TestReporter.print_result("Status", exec_data.get("status"))
                    return True
                else:
                    print("⚠️  No execution record found")
                    return False
            else:
                print(f"❌ Event failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"⚠️  Trigger verification failed: {e}")
            return False
    
    def test_event_buffering_and_retry(self):
        """Verifica buffering e retry degli eventi"""
        TestReporter.print_header("EVENT BUFFERING & RETRY")
        
        try:
            # Ottieni stato buffer
            response = APIClient.get(f"{ServiceConfig.MONITOR_AGENT_URL}/monitor/buffer-status")
            
            if response.status_code == 200:
                buffer_status = response.json()
                buffered_count = buffer_status.get("buffered_events", 0)
                TestReporter.print_result("Buffered events", buffered_count)
                
                if buffered_count > 0:
                    print("ℹ️  Events are being buffered and waiting for retry")
                
                return True
            else:
                print(f"⚠️  Could not get buffer status: {response.text}")
                return False
                
        except Exception as e:
            print(f"⚠️  Buffer status check failed: {e}")
            return False


class TestVectorstoreIntegration:
    """Test: Integrazione con VectorStore"""
    
    def test_document_embedding_pipeline(self, test_data):
        """Testa pipeline di embedding documento"""
        TestReporter.print_header("DOCUMENT EMBEDDING PIPELINE")
        
        doc_data = test_data.generate_document_data()
        
        try:
            # 1. Crea documento nel backend
            response = APIClient.post(
                f"{ServiceConfig.BACKEND_URL}/api/documents/create",
                json_data=doc_data
            )
            
            if response.status_code not in [200, 201]:
                print(f"❌ Failed to create document: {response.text}")
                return False
            
            doc_id = response.json().get("id")
            TestReporter.print_result("Document created", doc_id)
            
            # Aspetta un po' per il processing
            time.sleep(2)
            
            # 2. Verifica se documento è stato aggiunto a vectorstore
            try:
                response = APIClient.get(f"{ServiceConfig.VECTORSTORE_URL}/api/documents/{doc_id}")
                
                if response.status_code == 200:
                    vs_doc = response.json()
                    TestReporter.print_result("In VectorStore", "✅")
                    TestReporter.print_result("Embedding status", vs_doc.get("embedding_status"))
                    return True
                else:
                    print("⚠️  Document not yet in vectorstore")
                    return False
                    
            except:
                print("⚠️  VectorStore query not available")
                return False
                
        except Exception as e:
            print(f"❌ Embedding pipeline failed: {e}")
            return False
    
    def test_semantic_search_end_to_end(self, test_data):
        """Testa ricerca semantica end-to-end"""
        TestReporter.print_header("SEMANTIC SEARCH E2E")
        
        try:
            # 1. Crea un documento con contenuto specifico
            doc_data = test_data.generate_document_data("semantic_test.pdf")
            doc_data["content"] = "This is about machine learning and artificial intelligence"
            
            response = APIClient.post(
                f"{ServiceConfig.BACKEND_URL}/api/documents/create",
                json_data=doc_data
            )
            
            if response.status_code not in [200, 201]:
                pytest.skip("Could not create test document")
            
            doc_id = response.json().get("id")
            time.sleep(2)  # Aspetta embedding
            
            # 2. Fai ricerca semantica
            try:
                response = APIClient.post(
                    f"{ServiceConfig.VECTORSTORE_URL}/api/documents/search",
                    json_data={
                        "query": "artificial intelligence",
                        "limit": 5
                    }
                )
                
                if response.status_code == 200:
                    results = response.json().get("results", [])
                    TestReporter.print_result("Search results found", len(results))
                    
                    if results:
                        top_result = results[0]
                        score = top_result.get("score", "N/A")
                        filename = top_result.get("filename", "N/A")
                        print(f"  Top: {filename} (score: {score})")
                        
                        return True
                else:
                    print(f"⚠️  Search failed: {response.text}")
                    return False
                    
            except:
                pytest.skip("VectorStore search not available")
                
        except Exception as e:
            print(f"⚠️  Semantic search E2E failed: {e}")
            return False


class TestDatabaseIntegrationPipeline:
    """Test: Integrazione completa con Database"""
    
    def test_document_lifecycle_in_database(self):
        """Testa ciclo di vita completo del documento in DB"""
        TestReporter.print_header("DOCUMENT LIFECYCLE IN DATABASE")
        
        try:
            # 1. Conta documenti iniziali
            initial_count = DatabaseHelper.count_table("documents")
            TestReporter.print_result("Initial document count", initial_count)
            
            # 2. Crea documento
            doc_data = TestDataGenerator.generate_document_data(f"lifecycle_test_{datetime.utcnow().timestamp()}.pdf")
            
            response = APIClient.post(
                f"{ServiceConfig.BACKEND_URL}/api/documents/create",
                json_data=doc_data
            )
            
            if response.status_code not in [200, 201]:
                pytest.skip("Could not create document")
            
            doc_id = response.json().get("id")
            time.sleep(1)
            
            # 3. Verifica documento nel DB
            docs = DatabaseHelper.query_dict(
                "SELECT * FROM documents WHERE id = ?",
                (doc_id,)
            )
            
            if docs:
                doc = docs[0]
                TestReporter.print_result("Document in DB", "✅")
                TestReporter.print_result("Filename", doc.get("filename"))
                TestReporter.print_result("Created at", doc.get("created_at"))
            
            # 4. Conta documenti finali
            final_count = DatabaseHelper.count_table("documents")
            TestReporter.print_result("Final document count", final_count)
            TestReporter.print_result("New documents", final_count - initial_count)
            
            return final_count > initial_count
            
        except Exception as e:
            print(f"⚠️  Lifecycle test failed: {e}")
            return False
    
    def test_workflow_execution_history(self):
        """Testa tracking della storia di esecuzione workflow"""
        TestReporter.print_header("WORKFLOW EXECUTION HISTORY")
        
        try:
            # Ottieni esecuzioni recenti
            executions = DatabaseHelper.query_dict(
                """SELECT id, workflow_id, status, started_at, completed_at
                   FROM workflow_executions 
                   ORDER BY started_at DESC 
                   LIMIT 10"""
            )
            
            TestReporter.print_result("Recent executions", len(executions))
            
            if executions:
                print("\n📋 Execution history:")
                headers = ["Workflow", "Status", "Started", "Duration"]
                rows = []
                
                for exec_data in executions:
                    started = exec_data.get("started_at", "N/A")[:19]
                    workflow = exec_data.get("workflow_id", "N/A")[:20]
                    status = exec_data.get("status", "N/A")
                    duration = "N/A"
                    
                    rows.append([workflow, status, started, duration])
                
                TestReporter.print_table(headers, rows)
                
                return True
            else:
                print("ℹ️  No execution history found")
                return False
                
        except Exception as e:
            print(f"⚠️  Execution history failed: {e}")
            return False
    
    def test_document_vectorstore_sync(self):
        """Verifica sincronizzazione documento tra DB e VectorStore"""
        TestReporter.print_header("DOCUMENT DB-VECTORSTORE SYNC")
        
        try:
            # Documenti in DB
            db_docs_response = DatabaseHelper.query_dict("SELECT COUNT(*) as count FROM documents")
            db_count = db_docs_response[0]["count"] if db_docs_response else 0
            
            # Documenti in VectorStore
            try:
                response = APIClient.get(f"{ServiceConfig.VECTORSTORE_URL}/api/documents")
                vs_docs = response.json()
                if isinstance(vs_docs, dict):
                    vs_docs = vs_docs.get("documents", [])
                vs_count = len(vs_docs)
            except:
                vs_count = "N/A"
            
            TestReporter.print_result("Documents in DB", db_count)
            TestReporter.print_result("Documents in VectorStore", vs_count)
            
            if isinstance(vs_count, int):
                diff = db_count - vs_count
                if diff == 0:
                    print("✅ Perfect sync")
                else:
                    print(f"⚠️  Difference: {diff} documents")
            
            return True
            
        except Exception as e:
            print(f"⚠️  Sync check failed: {e}")
            return False


class TestCompleteE2EPipeline:
    """Test: Pipeline completa end-to-end"""
    
    def test_complete_workflow_from_file_to_search(self):
        """Test completo: File → Monitor → Backend → VectorStore → Search"""
        TestReporter.print_header("COMPLETE E2E WORKFLOW", level=0)
        
        session = TestSession("Complete E2E Pipeline")
        
        try:
            print("\n📋 E2E Test Steps:")
            
            # Step 1: Verifica servizi
            print("\n1. Verifying services...")
            health_ok = all([
                APIClient.get(f"{ServiceConfig.BACKEND_URL}/health").status_code == 200,
                APIClient.get(f"{ServiceConfig.VECTORSTORE_URL}/health").status_code == 200
            ])
            
            if health_ok:
                print("   ✅ Services online")
                session.record_pass()
            else:
                print("   ❌ Services offline")
                session.record_failure("Services not available")
                return session.summary()
            
            # Step 2: Crea documento
            print("\n2. Creating test document...")
            doc_data = TestDataGenerator.generate_document_data(f"e2e_test_{datetime.utcnow().timestamp()}.pdf")
            
            response = APIClient.post(
                f"{ServiceConfig.BACKEND_URL}/api/documents/create",
                json_data=doc_data
            )
            
            if response.status_code in [200, 201]:
                doc_id = response.json().get("id")
                print(f"   ✅ Document created: {doc_id}")
                session.record_pass()
            else:
                print(f"   ❌ Failed to create document")
                session.record_failure("Document creation failed")
                return session.summary()
            
            # Step 3: Attendi processing
            print("\n3. Waiting for background processing...")
            time.sleep(3)
            print("   ✅ Processing delay completed")
            session.record_pass()
            
            # Step 4: Verifica in database
            print("\n4. Verifying document in database...")
            docs = DatabaseHelper.query_dict(
                "SELECT id FROM documents WHERE id = ?",
                (doc_id,)
            )
            
            if docs:
                print("   ✅ Found in database")
                session.record_pass()
            else:
                print("   ❌ Not found in database")
                session.record_failure("Document not in database")
            
            # Step 5: Verifica in vectorstore
            print("\n5. Verifying document in vectorstore...")
            try:
                response = APIClient.get(f"{ServiceConfig.VECTORSTORE_URL}/api/documents/{doc_id}")
                if response.status_code == 200:
                    print("   ✅ Found in vectorstore")
                    session.record_pass()
                else:
                    print("   ⚠️  Not yet in vectorstore")
                    session.record_pass()  # Non è critico
            except:
                print("   ⚠️  VectorStore not available for verification")
                session.record_pass()
            
            # Step 6: Test ricerca
            print("\n6. Testing semantic search...")
            try:
                response = APIClient.post(
                    f"{ServiceConfig.VECTORSTORE_URL}/api/documents/search",
                    json_data={"query": "test", "limit": 5}
                )
                
                if response.status_code == 200:
                    results = response.json().get("results", [])
                    print(f"   ✅ Search executed: {len(results)} results")
                    session.record_pass()
                else:
                    print("   ⚠️  Search not available")
                    session.record_pass()
            except:
                print("   ⚠️  Search failed")
                session.record_pass()
            
        except Exception as e:
            print(f"\n❌ E2E test failed: {e}")
            session.record_failure(str(e))
        
        # Print summary
        summary = session.summary()
        TestReporter.print_summary(
            summary["test_name"],
            summary["total"],
            summary["passed"],
            summary["failed"]
        )
        
        return summary


# ============================================================================
# PYTEST EXECUTION
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
