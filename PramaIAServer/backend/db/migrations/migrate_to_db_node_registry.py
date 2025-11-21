#!/usr/bin/env python3
"""
Script di migrazione per inizializzare le nuove tabelle del NodeRegistry

Questo script:
1. Crea le nuove tabelle node_types, node_type_mappings, etc.
2. Popola i nodi di base 
3. Crea i mapping legacy → modern per compatibilità
4. Migra i dati esistenti
"""

import sys
from pathlib import Path

# Aggiungi la root del progetto al path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import sessionmaker
from backend.db.database import Base, engine, SessionLocal
from backend.db.node_registry_models import NodeType, NodeTypeMapping, PluginRegistry


def create_tables():
    """Crea le nuove tabelle per il NodeRegistry"""
    print("🗄️ Creando tabelle del NodeRegistry...")
    
    # Crea tutte le tabelle definite nei modelli
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelle create con successo")


def populate_default_data():
    """Popola il database con i nodi di default"""
    print("📝 Popolando il database con i nodi di default...")
    
    db = SessionLocal()
    
    try:
        # Controlla se i nodi di base esistono già
        existing_count = db.query(NodeType).count()
        if existing_count > 0:
            print(f"📋 {existing_count} nodi già presenti nel database")
            return
        
        # Definizione nodi di base e moderni
        base_nodes = [
            # Nodi moderni PDK (quelli che usiamo realmente)
            {
                "node_type": "document_input_node",
                "processor_class": "PDKProxyProcessor",
                "display_name": "Document Input",
                "description": "Input di documenti generico",
                "category": "input",
                "plugin_id": "core-input-plugin"
            },
            {
                "node_type": "pdf_text_extractor",
                "processor_class": "PDKProxyProcessor", 
                "display_name": "PDF Text Extractor",
                "description": "Estrazione testo da PDF",
                "category": "processing",
                "plugin_id": "core-data-plugin"
            },
            {
                "node_type": "text_chunker",
                "processor_class": "PDKProxyProcessor",
                "display_name": "Text Chunker", 
                "description": "Divisione testo in chunk",
                "category": "processing",
                "plugin_id": "core-data-plugin"
            },
            {
                "node_type": "text_embedder", 
                "processor_class": "PDKProxyProcessor",
                "display_name": "Text Embedder",
                "description": "Creazione embedding",
                "category": "processing", 
                "plugin_id": "core-rag-plugin"
            },
            {
                "node_type": "chroma_vector_store",
                "processor_class": "PDKProxyProcessor",
                "display_name": "ChromaDB Vector Store",
                "description": "Storage vettori ChromaDB",
                "category": "storage",
                "plugin_id": "core-rag-plugin"
            },
            {
                "node_type": "chroma_retriever",
                "processor_class": "PDKProxyProcessor", 
                "display_name": "ChromaDB Retriever",
                "description": "Recupero vettori ChromaDB",
                "category": "retrieval",
                "plugin_id": "core-rag-plugin"
            },
            {
                "node_type": "llm_processor",
                "processor_class": "PDKProxyProcessor",
                "display_name": "LLM Processor",
                "description": "Processore LLM generico", 
                "category": "llm",
                "plugin_id": "core-llm-plugin"
            },
            {
                "node_type": "document_results_formatter",
                "processor_class": "PDKProxyProcessor",
                "display_name": "Results Formatter", 
                "description": "Formattazione risultati",
                "category": "output",
                "plugin_id": "core-output-plugin"
            },
            {
                "node_type": "query_input_node",
                "processor_class": "PDKProxyProcessor", 
                "display_name": "Query Input",
                "description": "Input query utente",
                "category": "input",
                "plugin_id": "core-input-plugin"
            },
            {
                "node_type": "text_filter",
                "processor_class": "PDKProxyProcessor",
                "display_name": "Text Filter",
                "description": "Filtro e validazione testo",
                "category": "processing", 
                "plugin_id": "internal-processors-plugin"
            },
            {
                "node_type": "text_joiner", 
                "processor_class": "PDKProxyProcessor",
                "display_name": "Text Joiner",
                "description": "Unione testi",
                "category": "processing",
                "plugin_id": "internal-processors-plugin"
            },
            
            # Nodi legacy (deprecati ma con mapping)
            {
                "node_type": "PDFInput",
                "processor_class": "DeprecatedProcessor",
                "display_name": "PDF Input (Legacy)",
                "description": "Nodo legacy deprecato - usa document_input_node",
                "category": "deprecated",
                "plugin_id": None,
                "is_legacy": True,
                "is_active": False
            },
            {
                "node_type": "PDFInputValidator",
                "processor_class": "DeprecatedProcessor",
                "display_name": "PDF Input Validator (Legacy)",
                "description": "Nodo legacy deprecato - usa document_input_node",
                "category": "deprecated", 
                "plugin_id": None,
                "is_legacy": True,
                "is_active": False
            },
            {
                "node_type": "UpdateInputValidator",
                "processor_class": "DeprecatedProcessor", 
                "display_name": "Update Input Validator (Legacy)",
                "description": "Nodo legacy deprecato - usa text_filter",
                "category": "deprecated",
                "plugin_id": None,
                "is_legacy": True,
                "is_active": False
            },
            {
                "node_type": "ChromaVectorStore",
                "processor_class": "DeprecatedProcessor",
                "display_name": "Chroma Vector Store (Legacy)",
                "description": "Nodo legacy deprecato - usa chroma_vector_store",
                "category": "deprecated",
                "plugin_id": None,
                "is_legacy": True,
                "is_active": False
            },
            {
                "node_type": "LLMProcessor",
                "processor_class": "DeprecatedProcessor",
                "display_name": "LLM Processor (Legacy)", 
                "description": "Nodo legacy deprecato - usa llm_processor",
                "category": "deprecated",
                "plugin_id": None,
                "is_legacy": True,
                "is_active": False
            }
        ]
        
        # Inserisci nodi nel database
        for node_def in base_nodes:
            node_type = NodeType(**node_def)
            db.add(node_type)
        
        db.commit()
        print(f"✅ Inseriti {len(base_nodes)} nodi nel database")
        
    finally:
        db.close()


def create_legacy_mappings():
    """Crea i mapping per i nodi legacy"""
    print("🔄 Creando mapping legacy → modern...")
    
    db = SessionLocal()
    
    try:
        # Mapping definiti per i nodi problematici
        legacy_mappings = [
            # I nodi che causavano gli errori nel log
            ("PDFInput", "document_input_node"),
            ("PDFInputValidator", "document_input_node"), 
            ("UpdateInputValidator", "text_filter"),
            ("ChromaVectorStore", "chroma_vector_store"),
            ("LLMProcessor", "llm_processor"),
        ]
        
        mappings_created = 0
        
        for legacy_name, modern_name in legacy_mappings:
            # Trova i nodi nel database
            legacy_node = db.query(NodeType).filter_by(node_type=legacy_name).first()
            modern_node = db.query(NodeType).filter_by(node_type=modern_name).first()
            
            if legacy_node and modern_node:
                # Controlla se il mapping esiste già
                existing_mapping = db.query(NodeTypeMapping).filter_by(
                    legacy_type_id=legacy_node.id,
                    modern_type_id=modern_node.id
                ).first()
                
                if not existing_mapping:
                    mapping = NodeTypeMapping(
                        legacy_type_id=legacy_node.id,
                        modern_type_id=modern_node.id,
                        auto_migrate=True,
                        migration_notes=f"Auto-mapping da {legacy_name} a {modern_name}"
                    )
                    db.add(mapping)
                    mappings_created += 1
                    print(f"  ✅ {legacy_name} → {modern_name}")
                else:
                    print(f"  ⚠️ Mapping già esistente: {legacy_name} → {modern_name}")
            else:
                print(f"  ❌ Nodi non trovati: {legacy_name} o {modern_name}")
        
        db.commit()
        print(f"✅ Creati {mappings_created} mapping legacy")
        
    finally:
        db.close()


def verify_migration():
    """Verifica che la migrazione sia andata a buon fine"""
    print("🔍 Verificando la migrazione...")
    
    db = SessionLocal()
    
    try:
        # Conta nodi attivi
        active_nodes = db.query(NodeType).filter_by(is_active=True).count()
        legacy_nodes = db.query(NodeType).filter_by(is_legacy=True).count()
        mappings = db.query(NodeTypeMapping).count()
        
        print(f"📊 Statistiche migrazione:")
        print(f"  • Nodi attivi: {active_nodes}")
        print(f"  • Nodi legacy: {legacy_nodes}")
        print(f"  • Mapping creati: {mappings}")
        
        # Test specifico per i nodi problematici
        print(f"\n🔧 Test nodi problematici:")
        problematic_nodes = ["PDFInput", "UpdateInputValidator", "ChromaVectorStore", "LLMProcessor"]
        
        for node_name in problematic_nodes:
            mapping = db.query(NodeTypeMapping).join(
                NodeType, NodeTypeMapping.legacy_type_id == NodeType.id
            ).filter(NodeType.node_type == node_name).first()
            
            if mapping:
                print(f"  ✅ {node_name} → {mapping.modern_type.node_type}")
            else:
                print(f"  ❌ {node_name} NON MAPPATO")
        
        print(f"\n📋 Nodi attivi disponibili:")
        active_node_types = db.query(NodeType.node_type).filter_by(is_active=True).all()
        for (node_type,) in active_node_types:
            print(f"  • {node_type}")
        
    finally:
        db.close()


def main():
    """Esegue l'intera migrazione"""
    print("🚀 MIGRAZIONE NODEREGISTRY → DATABASE")
    print("=" * 50)
    
    try:
        # 1. Crea tabelle
        create_tables()
        
        # 2. Popola dati di default
        populate_default_data()
        
        # 3. Crea mapping legacy
        create_legacy_mappings()
        
        # 4. Verifica migrazione
        verify_migration()
        
        print("\n🎉 MIGRAZIONE COMPLETATA CON SUCCESSO!")
        print("\nIl nuovo DatabaseNodeRegistry è pronto.")
        print("I nodi legacy verranno automaticamente mappati a quelli moderni.")
        print("\nOra il WorkflowEngine dovrebbe risolvere i nodi correttamente!")
        
    except Exception as e:
        print(f"\n💥 ERRORE DURANTE LA MIGRAZIONE: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)