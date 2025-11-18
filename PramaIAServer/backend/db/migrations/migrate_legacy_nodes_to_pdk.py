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
    """High-confidence mapping from legacy node types to PDK node types."""
    M: Dict[str, str] = {}

    # Input
    M["input_user"] = "pdk_core-input-plugin_user_input"
    M["input_file"] = "pdk_core-input-plugin_file_input"

    # LLM
    M["llm_openai"] = "pdk_core-llm-plugin_openai"
    M["llm_anthropic"] = "pdk_core-llm-plugin_anthropic"
    M["llm_gemini"] = "pdk_core-llm-plugin_gemini"
    M["llm_ollama"] = "pdk_core-llm-plugin_ollama"

    # Output
    M["output_text"] = "pdk_core-output-plugin_text_output"
    M["output_file"] = "pdk_core-output-plugin_file_output"
    M["output_email"] = "pdk_core-output-plugin_email_output"

    # Data
    M["json_processor"] = "pdk_core-data-plugin_json_processor"
    M["csv_processor"] = "pdk_core-data-plugin_csv_processor"

    # API
    M["http_request"] = "pdk_core-api-plugin_http_request"
    M["webhook"] = "pdk_core-api-plugin_webhook_handler"
    # Legacy alias to http request
    M["api_call"] = "pdk_core-api-plugin_http_request"

    # Core RAG (presenti come legacy in alcuni workflow)
    M["text_chunker"] = "pdk_core-rag-plugin_text_chunker"
    M["text_embedder"] = "pdk_core-rag-plugin_text_embedder"

    # PDF Semantic Complete plugin (workflow end-to-end)
    M["pdf_input_node"] = "pdk_pdf-semantic-complete-plugin_pdf_input_node"
    M["pdf_text_extractor"] = "pdk_pdf-semantic-complete-plugin_pdf_text_extractor"
    M["chroma_vector_store"] = "pdk_pdf-semantic-complete-plugin_chroma_vector_store"
    M["chroma_retriever"] = "pdk_pdf-semantic-complete-plugin_chroma_retriever"
    M["query_input_node"] = "pdk_pdf-semantic-complete-plugin_query_input_node"
    M["llm_processor"] = "pdk_pdf-semantic-complete-plugin_llm_processor"
    M["pdf_results_formatter"] = "pdk_pdf-semantic-complete-plugin_pdf_results_formatter"

    # Plugin interni
    M["text_joiner"] = "pdk_internal-processors-plugin_text_joiner"

    # RAG: non mappiamo automaticamente tipi ambigui per evitare regressioni
    # Esempi legacy (se presenti) lasciati invariati: rag_query, document_index, rag_generation

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
