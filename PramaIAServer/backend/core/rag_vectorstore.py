import logging
from typing import List, Dict, Any
from datetime import datetime

import chromadb
from langchain_community.vectorstores import Chroma
from langchain.embeddings.base import Embeddings # Per il type hinting
from langchain.docstore.document import Document # Per il type hinting

from backend.core.config import RAG_INDEXES_DIR, RAG_DATA_DIR
from backend.core.rag_chains_prompts import get_openai_embeddings

logger = logging.getLogger(__name__)

# --- ChromaDB Setup ---
CHROMA_PERSIST_DIR = str(RAG_INDEXES_DIR / "chroma_db")
CHROMA_COLLECTION_NAME = "prama_documents"

# Inizializza il client ChromaDB.
# Questa istanza può essere condivisa all'interno di questo modulo.
try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    # Assicurati che la collezione esista o creala se necessario
    chroma_client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME
        # Se usi un embedding function custom a livello di client/collezione, specificala qui.
        # Altrimenti, Langchain la gestirà quando si usa Chroma.from_documents o si inizializza il wrapper.
    )
    logger.info(f"ChromaDB client initialized. Collection '{CHROMA_COLLECTION_NAME}' ensured.")
except Exception as e:
    logger.error(f"Failed to initialize ChromaDB client or ensure collection: {e}", exc_info=True)
    # Potresti voler sollevare un'eccezione qui o avere un meccanismo di fallback
    chroma_client = None # Indica che il client non è disponibile


def add_documents_to_vectorstore(
    docs: List[Document],
    embeddings_service: Embeddings,
    filename: str
):
    """
    Aggiunge una lista di documenti Langchain al vector store ChromaDB.
    I metadati 'source_filename' e 'ingest_time_utc' vengono aggiunti a ciascun documento.
    """
    logger.debug(f"[VECTORSTORE_DEBUG] Inizio inserimento documenti da '{filename}' - {len(docs)} documenti da inserire")
    
    if not chroma_client:
        logger.error("[VECTORSTORE_DEBUG] ChromaDB client non disponibile. Impossibile aggiungere documenti.")
        return

    # Log dei metadati dei documenti per debug
    for i, doc in enumerate(docs):
        doc.metadata = doc.metadata or {}
        doc.metadata["source_filename"] = filename
        doc.metadata["ingest_time_utc"] = datetime.utcnow().isoformat()
        
        # Log dettagliato per ogni documento
        logger.debug(f"[VECTORSTORE_DEBUG] Documento {i+1}/{len(docs)} - Preparazione per inserimento:")
        logger.debug(f"[VECTORSTORE_DEBUG] - ID documento: {doc.metadata.get('document_id', 'Non specificato')}")
        logger.debug(f"[VECTORSTORE_DEBUG] - Tipo documento: {doc.metadata.get('document_type', 'Non specificato')}")
        logger.debug(f"[VECTORSTORE_DEBUG] - Lunghezza contenuto: {len(doc.page_content)} caratteri")
        logger.debug(f"[VECTORSTORE_DEBUG] - Metadati completi: {doc.metadata}")

    try:
        logger.debug(f"[VECTORSTORE_DEBUG] Avvio inserimento in ChromaDB usando embedding service: {type(embeddings_service).__name__}")
        
        start_time = datetime.now()
        Chroma.from_documents(
            documents=docs,
            embedding=embeddings_service,
            collection_name=CHROMA_COLLECTION_NAME,
            client=chroma_client,
        )
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        logger.info(f"✅ Documenti da '{filename}' aggiunti/aggiornati nella collezione Chroma '{CHROMA_COLLECTION_NAME}' in {duration:.2f} secondi.")
        logger.debug(f"[VECTORSTORE_DEBUG] Inserimento completato con successo: {len(docs)} documenti inseriti in {duration:.2f} secondi")
        
        # Verifica post-inserimento
        try:
            collection = chroma_client.get_collection(name=CHROMA_COLLECTION_NAME)
            results = collection.get(where={"source_filename": filename}, include=[])
            logger.debug(f"[VECTORSTORE_DEBUG] Verifica post-inserimento: trovati {len(results.get('ids', []))} documenti con source_filename='{filename}'")
        except Exception as post_check_error:
            logger.error(f"[VECTORSTORE_DEBUG] Errore durante la verifica post-inserimento: {post_check_error}")
            
        return True
    except Exception as e:
        logger.error(f"[VECTORSTORE_DEBUG] ❌ Errore durante l'aggiunta di documenti da '{filename}' a Chroma: {e}", exc_info=True)
        logger.error(f"[VECTORSTORE_DEBUG] Dettagli documenti problematici: {[(i, len(d.page_content), d.metadata) for i, d in enumerate(docs)]}")
        return False


def remove_documents_from_vectorstore(filename: str) -> bool:
    """
    Rimuove tutti i vettori associati a un dato 'filename' dal vector store ChromaDB.
    """
    logger.debug(f"[VECTORSTORE_DEBUG] Inizio rimozione documenti per '{filename}' dal vectorstore")
    
    if not chroma_client:
        logger.error("[VECTORSTORE_DEBUG] ChromaDB client non disponibile. Impossibile rimuovere documenti.")
        return False
    try:
        start_time = datetime.now()
        collection = chroma_client.get_collection(name=CHROMA_COLLECTION_NAME)
        
        logger.debug(f"[VECTORSTORE_DEBUG] Cercando documenti con source_filename='{filename}'")
        results = collection.get(where={"source_filename": filename}, include=[]) # Solo IDs
        ids_to_delete = results.get("ids", [])
        
        logger.debug(f"[VECTORSTORE_DEBUG] Trovati {len(ids_to_delete)} documenti da eliminare per '{filename}'")
        logger.debug(f"[VECTORSTORE_DEBUG] IDs da eliminare: {ids_to_delete}")

        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"✅ Vettori per '{filename}' eliminati dalla collezione Chroma '{CHROMA_COLLECTION_NAME}' in {duration:.2f} secondi.")
            logger.debug(f"[VECTORSTORE_DEBUG] Eliminazione completata: {len(ids_to_delete)} documenti rimossi in {duration:.2f} secondi")
            
            # Verifica post-eliminazione
            try:
                check_results = collection.get(where={"source_filename": filename}, include=[])
                remaining_ids = check_results.get("ids", [])
                if remaining_ids:
                    logger.warning(f"[VECTORSTORE_DEBUG] ATTENZIONE: dopo l'eliminazione sono rimasti {len(remaining_ids)} documenti per '{filename}'")
                else:
                    logger.debug(f"[VECTORSTORE_DEBUG] Verifica post-eliminazione: nessun documento rimasto per '{filename}'")
            except Exception as post_check_error:
                logger.error(f"[VECTORSTORE_DEBUG] Errore durante la verifica post-eliminazione: {post_check_error}")
        else:
            logger.warning(f"[VECTORSTORE_DEBUG] Nessun vettore trovato per '{filename}' nella collezione Chroma per l'eliminazione.")
            
        return True
    except Exception as e:
        logger.error(f"[VECTORSTORE_DEBUG] ❌ Errore durante la rimozione dei documenti per '{filename}' da Chroma: {e}", exc_info=True)
        return False


def get_vectorstore_status() -> Dict[str, Any]:
    """
    Restituisce lo stato della collezione ChromaDB.
    """
    logger.debug("[VECTORSTORE_DEBUG] Verifica stato vectorstore ChromaDB")
    
    if not chroma_client:
        logger.error("[VECTORSTORE_DEBUG] ChromaDB client non disponibile per verificare lo stato")
        return {"status": "error", "message": "ChromaDB client not available."}
    try:
        collection = chroma_client.get_collection(name=CHROMA_COLLECTION_NAME)
        count = collection.count()
        
        logger.debug(f"[VECTORSTORE_DEBUG] Stato vectorstore ChromaDB: {count} documenti presenti")
        
        # Recupera informazioni aggiuntive per il debug
        try:
            # Ottieni informazioni sui primi 5 documenti per debug
            if count > 0:
                sample_results = collection.get(limit=5, include=["metadatas"])
                sample_ids = sample_results.get("ids", [])
                sample_metadatas = sample_results.get("metadatas", [])
                
                logger.debug(f"[VECTORSTORE_DEBUG] Campione di {len(sample_ids)} documenti:")
                if sample_ids and sample_metadatas:
                    for i in range(min(len(sample_ids), len(sample_metadatas))):
                        doc_id = sample_ids[i]
                        metadata = sample_metadatas[i]
                        logger.debug(f"[VECTORSTORE_DEBUG] - Documento {i+1}: ID={doc_id}, filename={metadata.get('source_filename', 'N/A')}, tipo={metadata.get('document_type', 'N/A')}")
        except Exception as sample_error:
            logger.error(f"[VECTORSTORE_DEBUG] Errore durante il recupero del campione di documenti: {sample_error}")
        
        return {"status": "ok" if count > 0 else "empty", "documents_in_index": count, "vector_store": "ChromaDB"}
    except Exception as e:
        logger.warning(f"[VECTORSTORE_DEBUG] Errore nel recuperare lo stato della collezione Chroma '{CHROMA_COLLECTION_NAME}': {e}")
        return {"status": "error", "message": str(e), "vector_store": "ChromaDB"}


def get_chroma_vectorstore_for_retrieval(embeddings_service: Embeddings) -> Chroma:
    """
    Restituisce un'istanza del wrapper Langchain Chroma per il recupero.
    """
    if not chroma_client:
        logger.error("ChromaDB client not available. Cannot create Chroma vectorstore for retrieval.")
        # Potrebbe sollevare un'eccezione o restituire None, a seconda di come vuoi gestire l'errore
        raise RuntimeError("ChromaDB client is not initialized.")
        
    return Chroma(client=chroma_client, collection_name=CHROMA_COLLECTION_NAME, embedding_function=embeddings_service)

# Supponiamo tu abbia già creato una variabile vectorstore globale
vectorstore = None

def get_vectorstore():
    global vectorstore
    if vectorstore is None:
        embeddings_service = get_openai_embeddings()
        try:
            vectorstore = get_chroma_vectorstore_for_retrieval(embeddings_service)
            logger.info("Vectorstore globale Chroma inizializzato.")
        except Exception as e:
            logger.error(f"Impossibile inizializzare il vectorstore globale: {e}", exc_info=True)
            return None
    return vectorstore