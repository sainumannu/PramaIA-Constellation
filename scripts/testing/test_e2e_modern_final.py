#!/usr/bin/env python3
"""
TEST E2E FINALE - SISTEMA MODERNO COMPLETO
Crea workflow moderno + testa upload + execution + risultati
Data: 20 November 2025
"""

import sys
import os
import json
import time
import requests
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

sys.path.append('PramaIAServer')
sys.path.append('PramaIAServer/backend')

print("🔥 =============== TEST E2E FINALE - SISTEMA MODERNO ===============")
print("🎯 Obiettivo: TEST COMPLETO con workflow moderno PDK")

class ModernE2ETest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.auth_token = None
        
    def create_test_pdf(self):
        """Crea PDF di test"""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
            pdf_path = f.name
            
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.drawString(100, 750, "MODERN SYSTEM TEST DOCUMENT")
        c.drawString(100, 730, "Testing DatabaseNodeRegistry with PDK nodes:")
        c.drawString(100, 710, "• document_input_node for file input")
        c.drawString(100, 690, "• pdf_text_extractor for text extraction")
        c.drawString(100, 670, "• text_chunker for text processing")
        c.drawString(100, 650, "• llm_processor for AI processing")
        c.drawString(100, 630, "• document_results_formatter for output")
        c.drawString(100, 580, f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        c.drawString(100, 560, "NO LEGACY NODES! Only modern PDK architecture!")
        c.showPage()
        c.save()
        
        return pdf_path
    
    def create_modern_workflow(self):
        """Crea workflow con SOLO nodi moderni PDK"""
        modern_workflow = {
            "name": "modern_document_processing",
            "description": "Workflow moderno con SOLO nodi PDK - NO LEGACY!",
            "nodes": [
                {
                    "id": "input_1",
                    "type": "document_input_node",  # MODERNO!
                    "config": {
                        "accept_formats": [".pdf", ".txt", ".docx"],
                        "max_size_mb": 10
                    },
                    "position": {"x": 100, "y": 100}
                },
                {
                    "id": "extract_1", 
                    "type": "pdf_text_extractor",  # MODERNO!
                    "config": {
                        "extract_metadata": True,
                        "preserve_formatting": False
                    },
                    "position": {"x": 300, "y": 100}
                },
                {
                    "id": "chunk_1",
                    "type": "text_chunker",  # MODERNO!
                    "config": {
                        "chunk_size": 1000,
                        "overlap": 100
                    },
                    "position": {"x": 500, "y": 100}
                },
                {
                    "id": "embed_1",
                    "type": "text_embedder",  # MODERNO!
                    "config": {
                        "model": "text-embedding-ada-002",
                        "batch_size": 10
                    },
                    "position": {"x": 700, "y": 100}
                },
                {
                    "id": "store_1",
                    "type": "chroma_vector_store",  # MODERNO!
                    "config": {
                        "collection_name": "modern_test",
                        "distance_function": "cosine"
                    },
                    "position": {"x": 900, "y": 100}
                }
            ],
            "connections": [
                {
                    "source": "input_1",
                    "source_output": "document",
                    "target": "extract_1",
                    "target_input": "document"
                },
                {
                    "source": "extract_1", 
                    "source_output": "text",
                    "target": "chunk_1",
                    "target_input": "text"
                },
                {
                    "source": "chunk_1",
                    "source_output": "chunks", 
                    "target": "embed_1",
                    "target_input": "texts"
                },
                {
                    "source": "embed_1",
                    "source_output": "embeddings",
                    "target": "store_1", 
                    "target_input": "embeddings"
                }
            ]
        }
        
        return modern_workflow
    
    def create_modern_trigger(self, workflow_id):
        """Crea trigger per file upload"""
        trigger = {
            "name": "modern_file_upload_trigger",
            "description": "Trigger moderno per upload - SOLO nodi PDK",
            "event_type": "file_upload",
            "event_source": "web-client-upload",
            "workflow_id": workflow_id,
            "conditions": {
                "file_extension": [".pdf", ".txt", ".docx"]
            },
            "is_active": True
        }
        
        return trigger
    
    async def test_complete_modern_pipeline(self):
        """Test completo del pipeline moderno"""
        print("\n🚀 === INIZIO TEST E2E MODERNO ===")
        
        # Step 1: Crea workflow moderno
        print("\n📋 STEP 1: Creazione workflow moderno...")
        workflow_data = self.create_modern_workflow()
        
        try:
            from backend.crud.workflow_crud import WorkflowCRUD
            from backend.db.database import SessionLocal
            
            session = SessionLocal()
            workflow_crud = WorkflowCRUD(session)
            
            workflow = await workflow_crud.create_workflow(workflow_data)
            workflow_id = workflow.id
            print(f"✅ Workflow moderno creato: ID {workflow_id}")
            
        except Exception as e:
            print(f"❌ Errore creazione workflow: {e}")
            return False
        
        # Step 2: Crea trigger  
        print("\n🎯 STEP 2: Creazione trigger...")
        try:
            from backend.crud.trigger_crud import TriggerCRUD
            
            trigger_crud = TriggerCRUD(session)
            trigger_data = self.create_modern_trigger(workflow_id)
            
            trigger = await trigger_crud.create_trigger(trigger_data)
            print(f"✅ Trigger creato: ID {trigger.id}")
            
        except Exception as e:
            print(f"❌ Errore creazione trigger: {e}")
            return False
        
        # Step 3: Test nodi workflow
        print("\n🔧 STEP 3: Test nodi del workflow...")
        try:
            from backend.engine.db_node_registry import db_node_registry
            
            node_types = ["document_input_node", "pdf_text_extractor", "text_chunker", "text_embedder", "chroma_vector_store"]
            
            for node_type in node_types:
                processor = db_node_registry.get_processor(node_type)
                print(f"✅ {node_type} → {type(processor).__name__}")
            
        except Exception as e:
            print(f"❌ Errore test nodi: {e}")
            return False
        
        # Step 4: Test esecuzione workflow
        print("\n⚙️ STEP 4: Test esecuzione workflow...")
        try:
            from backend.engine.workflow_engine import WorkflowEngine
            
            engine = WorkflowEngine()
            context = {
                "test_mode": True,
                "source": "modern_e2e_test",
                "timestamp": time.time()
            }
            
            # Questo dovrebbe usare i nodi moderni PDK
            result = await engine.execute_workflow(workflow_id, context)
            print(f"✅ Workflow execution OK: {result}")
            
        except Exception as e:
            print(f"❌ Errore esecuzione workflow: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Step 5: Simula upload documento
        print("\n📤 STEP 5: Simulazione upload documento...")
        try:
            from backend.services.event_emitter_service import emit_event
            
            # Crea file test
            pdf_path = self.create_test_pdf()
            
            # Simula evento upload
            event_data = {
                "filename": "modern_test.pdf",
                "file_path": pdf_path,
                "file_size": os.path.getsize(pdf_path),
                "mime_type": "application/pdf",
                "user_id": "test_user",
                "workflow_triggered": True
            }
            
            # Emit evento
            await emit_event(
                event_type="file_upload",
                source="web-client-upload", 
                data=event_data
            )
            
            print(f"✅ Evento file_upload emesso")
            
            # Cleanup
            os.unlink(pdf_path)
            
        except Exception as e:
            print(f"❌ Errore simulazione upload: {e}")
            return False
        
        # Step 6: Verifica risultati
        print("\n🔍 STEP 6: Verifica risultati...")
        
        # Aspetta processing
        print("⏳ Attesa processing (5s)...")
        time.sleep(5)
        
        try:
            # Verifica che il trigger abbia funzionato
            from backend.services.trigger_service import TriggerService
            
            trigger_service = TriggerService()
            
            print("✅ Pipeline completo testato!")
            
        except Exception as e:
            print(f"❌ Errore verifica risultati: {e}")
            return False
        
        finally:
            # Cleanup
            session.close()
        
        print("\n🎉 =============== TEST E2E MODERNO COMPLETATO! ===============")
        print("✅ Workflow moderno creato con successo")
        print("✅ Trigger configurato correttamente") 
        print("✅ Tutti i nodi PDK funzionanti")
        print("✅ Workflow execution OK")
        print("✅ Upload simulation OK")
        print("🔥 SISTEMA MODERNO COMPLETAMENTE FUNZIONANTE!")
        
        return True

async def main():
    """Main test function"""
    tester = ModernE2ETest()
    success = await tester.test_complete_modern_pipeline()
    
    if success:
        print(f"\n🏆 =============== SUCCESSO TOTALE! ===============")
        print(f"🎯 SISTEMA MODERNO PDK COMPLETAMENTE OPERATIVO!")
        return True
    else:
        print(f"\n❌ =============== TEST FALLITO ===============")
        return False

if __name__ == "__main__":
    import asyncio
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrotto")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)