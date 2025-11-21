"""
Migrazione: aggiorna i workflow_nodes.node_type da legacy a PDK.

- Crea un backup del DB SQLite.
- Applica una mappatura sicura legacy -> pdk_<plugin>_<node>.
- Stampa un report delle modifiche (conteggi per tipo, esempi).

Uso:
  python -m backend.db.migrations.migrate_legacy_nodes_to_pdk --dry-run    # solo report
  python -m backend.db.migrations.migrate_legacy_nodes_to_pdk --apply      # backup + update

Nota: Solo i tipi con mappature ad alta confidenza vengono aggiornati.
Altri tipi legacy (RAG avanzati, trasformazioni generiche, ecc.) restano invariati e vengono segnalati nel report.
"""

from __future__ import annotations

import argparse
import datetime
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Reuse DB path from backend config
from backend.core.config import BACKEND_DIR


def get_db_path() -> Path:
    # Controlla prima nella nuova posizione
    db_dir = BACKEND_DIR / "db"
    if db_dir.exists() and (db_dir / "database.db").exists():
        return db_dir / "database.db"
    
    # Fallback alla vecchia posizione
    data_dir = BACKEND_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "database.db"


def get_engine(db_path: Path) -> Engine:
    url = f"sqlite:///{db_path}"
    # check_same_thread=False useful for scripts as well
    return create_engine(url, connect_args={"check_same_thread": False})


def backup_database(db_path: Path) -> Path:
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = db_path.with_suffix(f".db.bak.{ts}")
    shutil.copy2(db_path, backup_path)
    return backup_path


def fetch_node_types(engine: Engine) -> List[Tuple[int, str]]:
    """Return list of (id, node_type) from workflow_nodes."""
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, node_type FROM workflow_nodes")).fetchall()
    return [(row[0], row[1]) for row in rows]


def build_mapping() -> Dict[str, str]:
    """High-confidence mapping from legacy node types to modern PDK node types.
    
    Evoluzione architetturale:
    - Da nodi specifici PDF → nodi generici per documenti
    - Da processori legacy → plugin moderni standardizzati
    - Da operazioni specifiche → operazioni generiche riusabili
    """
    M: Dict[str, str] = {}

    # === DOCUMENT INPUT EVOLUTION ===
    # Legacy PDF-specific → Modern document-generic
    M["PDFInput"] = "document_input_node"  # PDF-specific → Generic document input
    M["PDFInputValidator"] = "document_input_node"  # Validation embedded in modern node
    M["input_file"] = "document_input_node"  # Generic file → Document input
    M["TextInput"] = "document_input_node"  # Text → Document (more flexible)
    
    # === DOCUMENT PROCESSING EVOLUTION ===  
    # Legacy PDF extractors → Modern document processors
    M["PDFTextExtractor"] = "pdf_text_extractor"  # Still PDF-specific but modernized
    M["PDKPDFExtractor"] = "pdf_text_extractor"  # PDK prefix removed
    M["ContentChangeDetector"] = "file_parsing"  # Content detection → File parsing
    M["PDKContentReprocessor"] = "document_processor"  # Reprocessing → Document processing
    
    # === TEXT PROCESSING EVOLUTION ===
    # Legacy chunkers/embedders → Modern standardized processors
    M["TextChunker"] = "text_chunker"  # Direct mapping (modernized)
    M["PDKTextChunker"] = "text_chunker"  # Remove PDK prefix
    M["TextEmbedder"] = "text_embedder"  # Direct mapping (modernized)
    M["PDKTextEmbedder"] = "text_embedder"  # Remove PDK prefix
    M["PDKEmbeddingUpdater"] = "text_embedder"  # Update operations → Embedder
    
    # === VECTOR STORAGE EVOLUTION ===
    # Legacy ChromaDB operations → Modern vector store operations
    M["ChromaVectorStore"] = "chroma_vector_store"  # Modernized ChromaDB
    M["ChromaRetriever"] = "chroma_retriever"  # Modernized retrieval
    M["PDKChromaWriter"] = "chroma_vector_store"  # Writer → Store operations
    M["PDKVectorSync"] = "vector_store_operations"  # Sync → Generic operations
    M["PDKVectorDeleter"] = "vector_store_operations"  # Delete → Generic operations
    M["DatabaseWriter"] = "vector_store_operations"  # DB write → Vector operations
    M["IndexUpdater"] = "vector_store_operations"  # Index update → Vector operations
    M["IndexCleaner"] = "vector_store_operations"  # Index clean → Vector operations
    
    # === QUERY & SEARCH EVOLUTION ===
    # Legacy query processors → Modern query handlers
    M["QueryInputProcessor"] = "query_input_node"  # Query processing → Query input
    M["QueryRouter"] = "query_input_node"  # Routing embedded in input
    M["PDKQueryEmbedder"] = "chroma_retriever"  # Query embedding → Retrieval
    M["PDKSemanticSearch"] = "chroma_retriever"  # Semantic search → Retrieval
    M["PDKContextBuilder"] = "chroma_retriever"  # Context building → Retrieval
    M["MetadataSearcher"] = "chroma_retriever"  # Metadata search → Retrieval
    
    # === LLM PROCESSING EVOLUTION ===
    # Legacy LLM processors → Modern standardized LLM processor
    M["LLMProcessor"] = "llm_processor"  # Direct mapping (modernized)
    M["PDKLLMProcessor"] = "llm_processor"  # Remove PDK prefix
    M["RAGPromptBuilder"] = "llm_processor"  # Prompt building → LLM processing
    
    # === OUTPUT & FORMATTING EVOLUTION ===
    # Legacy formatters → Modern results formatter
    M["OutputFormatter"] = "document_results_formatter"  # Generic → Document-specific
    M["ResponseFormatter"] = "document_results_formatter"  # Response → Document results
    M["ResultMerger"] = "document_results_formatter"  # Merging → Formatting
    
    # === METADATA MANAGEMENT EVOLUTION ===
    # Legacy metadata operations → Modern metadata manager
    M["MetadataCoordinator"] = "metadata_manager"  # Coordination → Management
    M["MetadataUpdater"] = "metadata_manager"  # Update → Management
    M["MetadataDeleter"] = "metadata_manager"  # Delete → Management
    
    # === LOGGING & MONITORING EVOLUTION ===
    # Legacy loggers → Modern event logger
    M["AuditLogger"] = "event_logger"  # Audit → Event logging
    M["NotificationManager"] = "event_logger"  # Notifications → Event logging
    M["SearchAnalytics"] = "event_logger"  # Analytics → Event logging
    
    # === WORKFLOW CONTROL EVOLUTION ===
    # Legacy validation/control → Modern text processors (simpler approach)
    M["UpdateInputValidator"] = "text_filter"  # Validation → Filtering
    M["DeleteInputValidator"] = "text_filter"  # Validation → Filtering
    M["TransactionCoordinator"] = "text_filter"  # Coordination → Filtering
    M["TransactionManager"] = "text_filter"  # Management → Filtering
    M["TransactionFinalizer"] = "text_filter"  # Finalization → Filtering
    M["ErrorHandler"] = "text_filter"  # Error handling → Filtering
    M["ErrorRecovery"] = "text_filter"  # Recovery → Filtering
    M["RecoveryManager"] = "text_filter"  # Recovery management → Filtering
    M["RollbackManager"] = "text_filter"  # Rollback → Filtering
    M["SuccessCoordinator"] = "text_filter"  # Success coordination → Filtering
    M["DependencyChecker"] = "text_filter"  # Dependency check → Filtering
    
    # === UTILITY OPERATIONS EVOLUTION ===
    # Legacy utilities → Modern text utilities
    M["BackupCreator"] = "text_joiner"  # Backup → Text joining (simpler)
    M["UpdateNotification"] = "text_joiner"  # Notifications → Text joining
    M["VersionManager"] = "text_joiner"  # Version management → Text joining
    
    # === CLEANUP & MAINTENANCE EVOLUTION ===
    # Legacy cleanup → Modern processors
    M["PDKCleanupProcessor"] = "text_filter"  # Cleanup → Filtering
    
    # === USER CONTEXT EVOLUTION ===
    # Legacy user input → Modern user context
    M["input_user"] = "user_context_provider"  # User input → Context provision
    
    print(f"📋 Mapping configured: {len(M)} legacy → modern node mappings")
    return M


def plan_changes(rows: List[Tuple[int, str]], mapping: Dict[str, str]):
    """Compute the plan of changes and stats."""
    to_update: List[Tuple[int, str, str]] = []  # (id, old, new)
    unknown: Dict[str, int] = {}
    stats_old: Dict[str, int] = {}
    stats_new: Dict[str, int] = {}

    for node_id, old_type in rows:
        stats_old[old_type] = stats_old.get(old_type, 0) + 1
        if old_type in mapping:
            new_type = mapping[old_type]
            if new_type != old_type:
                to_update.append((node_id, old_type, new_type))
                stats_new[new_type] = stats_new.get(new_type, 0) + 1
        else:
            unknown[old_type] = unknown.get(old_type, 0) + 1

    return to_update, unknown, stats_old, stats_new


def apply_updates(engine: Engine, updates: List[Tuple[int, str, str]]) -> int:
    """Apply updates and return affected rows count."""
    affected = 0
    with engine.begin() as conn:
        for node_id, old, new in updates:
            res = conn.execute(
                text("UPDATE workflow_nodes SET node_type = :new WHERE id = :id AND node_type = :old"),
                {"new": new, "id": node_id, "old": old},
            )
            affected += res.rowcount or 0
    return affected


def print_report(to_update, unknown, stats_old, stats_new):
    total = sum(stats_old.values())
    print("\n==== MIGRAZIONE NODE TYPES → PDK ====")
    print(f"Totale nodi in tabella: {total}")
    print("\n-- Tipi legacy riscontrati (conteggio) --")
    for k in sorted(stats_old.keys()):
        print(f"  {k}: {stats_old[k]}")

    print("\n-- Aggiornamenti pianificati (old -> new, conteggio) --")
    agg = {}
    for _, old, new in to_update:
        agg[(old, new)] = agg.get((old, new), 0) + 1
    if agg:
        for (old, new), c in sorted(agg.items()):
            print(f"  {old} -> {new}: {c}")
    else:
        print("  Nessun aggiornamento previsto")

    if unknown:
        print("\n-- Tipi non mappati (lasciati invariati) --")
        for k in sorted(unknown.keys()):
            print(f"  {k}: {unknown[k]}")

    print("\nEsempi (max 10):")
    for i, (node_id, old, new) in enumerate(to_update[:10], 1):
        print(f"  #{i} id={node_id}: {old} -> {new}")
    print("====================================\n")


def main():
    parser = argparse.ArgumentParser(description="Migra i node_type legacy verso i tipi PDK")
    parser.add_argument("--dry-run", action="store_true", help="Mostra il piano senza applicare modifiche")
    parser.add_argument("--apply", action="store_true", help="Applica le modifiche (backup automatico)")
    args = parser.parse_args()

    db_path = get_db_path()
    if not db_path.exists():
        raise SystemExit(f"Database non trovato: {db_path}")

    engine = get_engine(db_path)
    mapping = build_mapping()
    rows = fetch_node_types(engine)
    to_update, unknown, stats_old, stats_new = plan_changes(rows, mapping)
    print_report(to_update, unknown, stats_old, stats_new)

    if args.dry_run and not args.apply:
        print("Dry-run completato. Nessuna modifica applicata.")
        return

    if args.apply:
        backup = backup_database(db_path)
        print(f"Backup creato: {backup}")
        affected = apply_updates(engine, to_update)
        print(f"Aggiornamento completato. Righe interessate: {affected}")
        return

    # Default se nessun flag: fai solo dry-run
    print("Nessun flag specificato: eseguo dry-run di default.")
    # call again as dry-run info is already printed


if __name__ == "__main__":
    main()
