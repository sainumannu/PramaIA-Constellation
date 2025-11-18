#!/usr/bin/env python3
"""
Test Workflow Execution - Test completo dei workflow CRUD PDF

Questo script testa l'esecuzione end-to-end dei workflow CRUD PDF
con i processori reali implementati.
"""

import asyncio
import sqlite3
import json
import tempfile
import os
from datetime import datetime
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Percorsi
DB_PATH = "backend/db/database.db"

# Import PramaIA modules
try:
    from backend.engine.node_registry import NodeRegistry
    from backend.engine.execution_context import ExecutionContext
    from backend.models.workflow import Workflow, WorkflowNode
    IMPORTS_OK = True
except ImportError as e:
    logger.error(f"❌ Errore import moduli PramaIA: {e}")
    IMPORTS_OK = False

def create_test_pdf():
    """Crea un file PDF di test per i workflow."""
    try:
        # Crea un file di testo semplice come PDF mock
        test_content = """Test Document for PramaIA Workflow
        
This is a test document created for testing the PDF processing workflow.
It contains multiple paragraphs and various text elements.

Key features:
- Multiple lines of text
- Different paragraphs 
- Special characters: àèéìòù
- Numbers: 123, 456.78
- Punctuation and symbols!

This document will be processed by the FileParsingProcessor
to extract text and metadata for workflow testing.

End of test document.
"""
        
        # Crea file temporaneo
        temp_dir = Path("temp_files")
        temp_dir.mkdir(exist_ok=True)
        
        test_file = temp_dir / "test_document.txt"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        logger.info(f"✅ File di test creato: {test_file}")
        return str(test_file)
        
    except Exception as e:
        logger.error(f"❌ Errore creazione file test: {e}")
        return None

class WorkflowTester:
    """Classe per testare l'esecuzione dei workflow."""
    
    def __init__(self):
        self.registry = None
        self.workflows = []
        
    def initialize(self):
        """Inizializza il tester."""
        if not IMPORTS_OK:
            logger.error("❌ Moduli PramaIA non disponibili")
            return False
        
        try:
            # Inizializza registry
            self.registry = NodeRegistry()
            logger.info("✅ NodeRegistry inizializzato")
            
            # Carica workflow dal database
            self.load_workflows()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore inizializzazione: {e}")
            return False
    
    def load_workflows(self):
        """Carica workflow dal database."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Carica workflow con nodi
        cursor.execute("""
            SELECT w.workflow_id, w.name, w.description, w.trigger_type
            FROM workflows w
            ORDER BY w.name
        """)
        
        for row in cursor.fetchall():
            workflow_id, name, description, trigger_type = row
            
            # Carica nodi del workflow
            cursor.execute("""
                SELECT node_id, name, node_type, config, position_x, position_y
                FROM workflow_nodes
                WHERE workflow_id = ?
                ORDER BY name
            """, (workflow_id,))
            
            nodes = []
            for node_row in cursor.fetchall():
                node_id, node_name, node_type, config_json, pos_x, pos_y = node_row
                config = json.loads(config_json) if config_json else {}
                
                # Crea oggetto nodo mockup
                node = type('WorkflowNode', (), {
                    'node_id': node_id,
                    'name': node_name,
                    'node_type': node_type,
                    'config': config,
                    'position_x': pos_x,
                    'position_y': pos_y
                })()
                
                nodes.append(node)
            
            # Crea oggetto workflow mockup
            workflow = type('Workflow', (), {
                'workflow_id': workflow_id,
                'name': name,
                'description': description,
                'trigger_type': trigger_type,
                'nodes': nodes
            })()
            
            self.workflows.append(workflow)
        
        conn.close()
        logger.info(f"✅ Caricati {len(self.workflows)} workflow")
    
    async def test_single_processor(self, processor_type: str, test_data: dict):
        """Testa un singolo processore in isolamento."""
        logger.info(f"🧪 Test processore: {processor_type}")
        
        try:
            processor = self.registry.get_processor(processor_type)
            if not processor:
                logger.error(f"❌ Processore non trovato: {processor_type}")
                return False
            
            # Crea contesto mock
            context = type('ExecutionContext', (), {
                'execution_id': f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'get_input_for_node': lambda node_id: test_data,
                'workflow': type('Workflow', (), {'workflow_id': 'test_workflow'})(),
                'started_at': datetime.now()
            })()
            
            # Crea nodo mock
            node = type('Node', (), {
                'node_id': 'test_node',
                'name': f'Test {processor_type}',
                'node_type': processor_type,
                'config': {}
            })()
            
            # Esegui processore
            result = await processor.execute(node, context)
            
            logger.info(f"   ✅ Risultato: {type(result).__name__}")
            logger.info(f"   📊 Keys: {list(result.keys()) if isinstance(result, dict) else 'Non-dict'}")
            
            return True
            
        except Exception as e:
            logger.error(f"   ❌ Errore: {e}")
            return False
    
    async def test_workflow_execution(self, workflow, test_data: dict):
        """Testa l'esecuzione completa di un workflow."""
        logger.info(f"🔄 Test workflow: {workflow.name}")
        
        try:
            # Simula esecuzione sequenziale dei nodi
            current_data = test_data.copy()
            
            for i, node in enumerate(workflow.nodes):
                logger.info(f"   📍 Nodo {i+1}/{len(workflow.nodes)}: {node.name} ({node.node_type})")
                
                # Ottieni processore
                processor = self.registry.get_processor(node.node_type)
                if not processor:
                    logger.error(f"   ❌ Processore non trovato: {node.node_type}")
                    return False
                
                # Crea contesto per il nodo
                context = type('ExecutionContext', (), {
                    'execution_id': f"test_wf_{workflow.workflow_id}_{datetime.now().strftime('%H%M%S')}",
                    'get_input_for_node': lambda node_id: current_data,
                    'workflow': workflow,
                    'started_at': datetime.now()
                })()
                
                # Esegui nodo
                result = await processor.execute(node, context)
                
                if isinstance(result, dict):
                    # Aggiorna dati per prossimo nodo
                    current_data.update(result)
                    logger.info(f"   ✅ Output keys: {list(result.keys())}")
                else:
                    logger.warning(f"   ⚠️ Output non-dict: {type(result)}")
            
            logger.info(f"   🎉 Workflow completato con successo!")
            return True
            
        except Exception as e:
            logger.error(f"   ❌ Errore workflow: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def run_all_tests(self):
        """Esegue tutti i test."""
        logger.info("🚀 AVVIO TEST COMPLETI")
        logger.info("="*50)
        
        # Crea file di test
        test_file = create_test_pdf()
        if not test_file:
            logger.error("❌ Impossibile creare file di test")
            return
        
        # Dati di test base
        test_data = {
            "event_type": "document_upload",
            "file_path": test_file,
            "payload": {
                "file_path": test_file,
                "user_id": "test_user",
                "metadata": {
                    "source": "test",
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
        
        # Test 1: Processori individuali
        logger.info("📋 FASE 1: Test processori individuali")
        logger.info("-" * 30)
        
        real_processors = [
            "event_input_node",
            "file_parsing", 
            "metadata_manager",
            "document_processor",
            "vector_store_operations",
            "event_logger"
        ]
        
        processor_results = {}
        for processor_type in real_processors:
            success = await self.test_single_processor(processor_type, test_data)
            processor_results[processor_type] = success
        
        # Riepilogo processori
        logger.info("")
        logger.info("📊 RIEPILOGO PROCESSORI:")
        for proc, success in processor_results.items():
            status = "✅ OK" if success else "❌ FAIL"
            logger.info(f"   {status} {proc}")
        
        # Test 2: Workflow completi
        if any(processor_results.values()):
            logger.info("")
            logger.info("📋 FASE 2: Test workflow completi")
            logger.info("-" * 30)
            
            workflow_results = {}
            for workflow in self.workflows:
                success = await self.test_workflow_execution(workflow, test_data)
                workflow_results[workflow.name] = success
            
            # Riepilogo workflow
            logger.info("")
            logger.info("📊 RIEPILOGO WORKFLOW:")
            for wf_name, success in workflow_results.items():
                status = "✅ OK" if success else "❌ FAIL"
                logger.info(f"   {status} {wf_name}")
        
        # Cleanup
        if test_file and os.path.exists(test_file):
            os.remove(test_file)
            logger.info("🧹 File di test rimosso")
        
        # Risultato finale
        logger.info("")
        logger.info("="*50)
        logger.info("🎯 RISULTATO FINALE:")
        
        working_processors = sum(1 for success in processor_results.values() if success)
        total_processors = len(processor_results)
        
        if 'workflow_results' in locals():
            working_workflows = sum(1 for success in workflow_results.values() if success)
            total_workflows = len(workflow_results)
            logger.info(f"   Processori: {working_processors}/{total_processors}")
            logger.info(f"   Workflow: {working_workflows}/{total_workflows}")
            
            if working_processors == total_processors and working_workflows == total_workflows:
                logger.info("   🎉 TUTTI I TEST SUPERATI!")
            else:
                logger.info("   ⚠️ Alcuni test falliti - verificare i log")
        else:
            logger.info(f"   Processori: {working_processors}/{total_processors}")
            logger.info("   Workflow: Test saltati per errori processori")

async def main():
    """Funzione principale di test."""
    print("""
🧪 TEST WORKFLOW CRUD PDF CON PROCESSORI REALI
==============================================

Test completo dell'esecuzione workflow con i processori 
reali implementati.
""")
    
    # Verifica prerequisiti
    if not Path(DB_PATH).exists():
        logger.error(f"❌ Database non trovato: {DB_PATH}")
        return
    
    # Inizializza tester
    tester = WorkflowTester()
    if not tester.initialize():
        logger.error("❌ Errore inizializzazione tester")
        return
    
    if not tester.workflows:
        logger.error("❌ Nessun workflow trovato nel database")
        logger.info("💡 Suggerimento: Esegui prima import_crud_workflows.py")
        return
    
    # Esegui test
    await tester.run_all_tests()

if __name__ == "__main__":
    if IMPORTS_OK:
        asyncio.run(main())
    else:
        logger.error("❌ Impossibile eseguire test senza moduli PramaIA")
        logger.info("💡 Assicurati che il PYTHONPATH includa la directory backend")