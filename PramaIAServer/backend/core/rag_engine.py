import uuid
import json
from datetime import datetime
import os
import shutil
from dotenv import load_dotenv

from backend.core.models_rag import RAGProcessedResponse
import tiktoken
from typing import Optional # Aggiunto per type hinting

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
# from langchain_community.vectorstores import Chroma # Rimosso (VectorstoreService)
# from langchain.embeddings.openai import OpenAIEmbeddings # Ora in rag_chains_prompts
# from langchain.llms import OpenAI # Ora in rag_chains_prompts
# from langchain.chains import ConversationalRetrievalChain # Ora creato da rag_chains_prompts
# from langchain.memory import ConversationBufferMemory # Ora in rag_memory

# In backend/core/rag_engine.py
from backend.core.config import (
    OPENAI_API_KEY,
    RAG_TOKEN_LOG_PATH,
    RAG_STATE_FILE_PATH,
    RAG_DATA_DIR,
    RAG_INDEXES_DIR,
    DEBUG_CLASSIFICATION # Se vuoi mantenerlo
)
import logging # Usare il logger
# Rimosso import rag_vectorstore
from backend.core import rag_chains_prompts as rcp # Importa il modulo delle chain e prompt
from backend.app.clients.vectorstore_client import VectorstoreServiceClient
from backend.core import rag_memory # Importa il nuovo modulo per la memoria
from backend.services import chat_service
from backend.core.rag_chains_prompts import run_rag_with_token_count

logger = logging.getLogger(__name__)


# LangChain setup
# L'oggetto embeddings può rimanere globale se non ha stato interno che cambia per richiesta.
# L'istanza di embeddings viene creata qui e passata dove necessario.
# Potrebbe anche essere creata e gestita all'interno di rag_chains_prompts o rag_vectorstore
# se si volesse un incapsulamento ancora maggiore. Per ora, la manteniamo qui.
embeddings = rcp.get_openai_embeddings()


# PDF ingest
def ingest_pdf(path: str, filename: Optional[str] = None):
    try:
        loader = PyPDFLoader(path)
        documents = loader.load()
        if not documents:
            print(f"⚠️ Nessun contenuto trovato in {filename}.")
            return

        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = text_splitter.split_documents(documents)

        # Usa VectorstoreService per aggiungere documenti
        client = VectorstoreServiceClient()
        
        # Prepara i dati per il client
        doc_texts = [doc.page_content for doc in docs]
        metadatas = []
        
        for i, doc in enumerate(docs):
            metadata = doc.metadata.copy()
            metadata["source_filename"] = filename if filename else os.path.basename(path)
            metadata["ingest_time_utc"] = datetime.utcnow().isoformat()
            metadata["chunk_id"] = f"{uuid.uuid4()}"
            metadatas.append(metadata)
            
        # Aggiungi documenti al vectorstore
        collection_name = "pdf_documents"  # Nome collezione predefinita
        response = client.add_documents(collection_name, doc_texts, metadatas)
        
        if response.get("success", False):
            logger.info(f"✅ Aggiunti {len(doc_texts)} documenti al vectorstore per {filename}")
            return response.get("document_ids", [])
        else:
            logger.error(f"❌ Errore nell'aggiungere documenti al vectorstore: {response.get('error', 'Errore sconosciuto')}")
            return []
    except Exception as e:
        logger.error(f"Errore ingest_pdf per file '{filename}': {e}", exc_info=True)
        return []

# Elenco PDF
def list_pdfs():
    if not RAG_DATA_DIR.exists():
        return []
    return [f.name for f in RAG_DATA_DIR.glob("*.pdf")]

# Rimuovi PDF
def remove_pdf(filename: str) -> bool:
    filepath = RAG_DATA_DIR / filename
    if not filepath.exists():
        return False
    try:
        filepath.unlink()
        # Usa VectorstoreService per rimuovere documenti
        client = VectorstoreServiceClient()
        collection_name = "pdf_documents"
        
        # Filtra per filename nei metadati
        metadata_filter = {"source_filename": filename}
        
        # Ottieni documenti con questo filename
        response = client._request("GET", f"/collections/{collection_name}/documents", 
                                 params={"metadata_filter": json.dumps(metadata_filter)})
        
        # Elimina i documenti trovati
        for doc in response.get("documents", []):
            doc_id = doc.get("id")
            if doc_id:
                client._request("DELETE", f"/collections/{collection_name}/documents/{doc_id}")
        
        return True
    except Exception as e:
        logger.error(f"Errore durante la rimozione del PDF '{filename}': {e}", exc_info=True)
        return False

# Funzione helper per contare i token (esempio per modelli OpenAI)
def count_tokens(text: str, model_name: str = "gpt-3.5-turbo") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base") # Fallback generico
    return len(encoding.encode(text))

def process_question(
    question: str,
    user_id: str,
    session_id: Optional[str] = None,
    model: str = "gpt-4o",
    db=None,
    max_history: int = 5,
    mode: str = "rag",  # "rag" (solo fonti interne) o "gpt" (fallback GPT classico)
    system_prompt: Optional[str] = None,  # Nuovo parametro per prompt personalizzato
    provider: str = "openai"  # <--- AGGIUNTO: provider LLM
) -> RAGProcessedResponse:
    session_id = session_id or str(uuid.uuid4())
    logger.info(f"[DEBUG] SESSION_ID: {session_id}")
    logger.info(f"[DEBUG] DOMANDA: {question}")

    # Inizializza variabili di ritorno per evitare errori
    answer_text = None
    source_text = "unknown"
    total_tokens = 0

    # Recupera o aggiorna il system_prompt nel DB se necessario
    if db is not None and session_id:
        session = db.query(chat_service.models.ChatSession).filter_by(session_id=session_id).first()
        if not session:
            db_user = db.query(chat_service.models.User).filter_by(user_id=user_id).first()
            session = chat_service.get_or_create_session(db, db_user, session_id=session_id, first_prompt=system_prompt if system_prompt is not None else "", first_question=question)
            # system_prompt ora è già scritto nel DB
        else:
            # Se viene passato un nuovo system_prompt e diverso da quello già salvato, aggiorna
            if system_prompt and (not session.system_prompt or session.system_prompt != system_prompt):
                session.system_prompt = system_prompt
                db.commit()
            # Se non passato esplicitamente, usa quello del DB
            if not system_prompt and hasattr(session, "system_prompt"):
                system_prompt = session.system_prompt
        # Se la sessione non esiste, verrà creata da get_or_create_session (altrove)
    
    tokens_prompt = count_tokens(question)
    tokens_completion = 0
    category_text = None

    try:
        logger.info(f"[DEBUG] DOMANDA ORIGINALE: {question}")
        logger.info("RAG Engine: Esecuzione catena di classificazione...")
        category = rcp.classification_chain.run(question).strip().lower()
        logger.info(f"[DEBUG] CATEGORY CLASSIFICATA: '{category}' (domanda: {question})")
        category_text = category if DEBUG_CLASSIFICATION else None

        if category == "smalltalk":
            logger.info("[DEBUG] Entrato nel ramo SMALLTALK")
            logger.info("RAG Engine: Esecuzione catena smalltalk...")
            # --- GESTIONE PROVIDER MODULARE ---
            from backend.llm.dispatcher import get_provider
            llm = get_provider(provider)
            answer_text = llm.generate(prompt=question, model=model, system_prompt=system_prompt)
            source_text = provider
            tokens_completion = count_tokens(str(answer_text))
            total_tokens = tokens_prompt + tokens_completion
            logger.info(f"RAG Engine: Catena smalltalk completata. Risposta: {answer_text}")
        elif category == "rischio_dati_sensibili":
            logger.info("[DEBUG] Entrato nel ramo RISCHIO DATI SENSIBILI")
            answer_text = "Mi dispiace, ma non posso elaborare contenuti sensibili o documenti riservati."
            source_text = "blocked"
            logger.info(f"RAG Engine: Risposta dati sensibili: {answer_text}")
            tokens_completion = count_tokens(answer_text)
            total_tokens = tokens_prompt + tokens_completion
        elif category == "richiesta_informativa":
            logger.info("[DEBUG] Entrato nel ramo RICHIESTA INFORMATIVA")
            logger.info("RAG Engine: Esecuzione process_question_rag...")
            rag_result = process_question_rag(question, session_id, db, model=model, max_history=max_history, system_prompt=system_prompt)
            # Se la funzione è una coroutine, va attesa
            import asyncio
            if asyncio.iscoroutine(rag_result):
                rag_result = asyncio.run(rag_result)
            logger.info(f"[DEBUG] Risultato process_question_rag: {rag_result}")
            answer_text = rag_result["answer"]
            source_text = rag_result.get("source", "docs")
            # Usa il conteggio token se disponibile
            if rag_result.get("total_tokens") is not None:
                total_tokens = rag_result["total_tokens"]
            else:
                tokens_completion = count_tokens(answer_text)
                total_tokens = tokens_prompt + tokens_completion
            logger.info(f"RAG Engine: process_question_rag completato. Risposta: {answer_text}")
            # Modalità GPT classico: se la risposta è vuota o generica, fai fallback
            if mode == "gpt" and (not answer_text or answer_text.strip() == "Non ho trovato informazioni rilevanti nei documenti."):
                logger.info("[MODALITÀ GPT CLASSICO] Fallback a provider LLM generico...")
                from backend.llm.dispatcher import get_provider
                llm = get_provider(provider)
                fallback_answer = llm.generate(prompt=question, model=model, system_prompt=system_prompt)
                answer_text = fallback_answer
                source_text = provider
                total_tokens = count_tokens(str(answer_text))
        else: # unknown
            logger.info("[DEBUG] Entrato nel ramo UNKNOWN")
            answer_text = "Non ho capito la tua richiesta. Puoi riformularla?"
            source_text = "unknown"
            logger.info(f"RAG Engine: Risposta unknown: {answer_text}")
            tokens_completion = count_tokens(answer_text)
            total_tokens = tokens_prompt + tokens_completion

        logger.info(f"[DEBUG] RISPOSTA: {answer_text}")

    except Exception as e:
        logger.error(f"Error in RAG process_question for user {user_id}: {e}", exc_info=True)
        answer_text = f"Si è verificato un errore durante l'elaborazione: {str(e)}"
        source_text = "error"
        tokens_completion = count_tokens(answer_text)
        total_tokens = tokens_prompt + tokens_completion
    
    # Garantisco che answer_text sia una stringa e non una coroutine prima del logging
    import asyncio
    if asyncio.iscoroutine(answer_text):
        answer_text = asyncio.run(answer_text)
    if answer_text is None:
        answer_text = ""

    # Logging sicuro della risposta
    if answer_text:
        logger.info(f"RAG Engine: Fine process_question. Risposta: {str(answer_text)[:50]}...")
    else:
        logger.warning("RAG Engine: Fine process_question. Risposta è None o vuota!")
        answer_text = "Errore: risposta vuota"

    return RAGProcessedResponse(
        answer=str(answer_text),
        source=source_text,
        session_id=session_id,
        tokens=total_tokens
    )

def process_question_rag(question: str, session_id: str, db, model: str = "gpt-4o", max_history: int = 5, system_prompt: Optional[str] = None) -> dict:
    session = db.query(chat_service.models.ChatSession).filter_by(session_id=session_id).first()
    if not session:
        # Recupera l'utente dal database o crea un utente temporaneo
        db_user = db.query(chat_service.models.User).filter_by(user_id=session_id).first()
        if not db_user:
            # Crea un utente temporaneo se non esiste
            db_user = chat_service.get_or_create_user(db, session_id)
        session = chat_service.get_or_create_session(db, db_user, session_id=session_id, first_prompt=system_prompt or "", first_question=question)
    history = chat_service.get_history_for_session(db, session.id)
    logger.info(f"[DEBUG] HISTORY per session_id={session_id}: {history}")
    
    # Usa VectorstoreService per le query semantiche
    try:
        # Inizializza il client
        client = VectorstoreServiceClient()
        collection_name = "pdf_documents"
        
        # Esegui la query semantica
        response = client.query(collection_name, question, top_k=5)
        
        # Se non ci sono risultati, restituisci un errore
        if not response.get("matches"):
            logger.error("No documents found in vectorstore.")
            return {"answer": "Errore: non ho trovato documenti pertinenti alla tua domanda.", "source": "error", "total_tokens": 0}
        
        # Crea un retriever simulato con i risultati ottenuti
        documents = []
        for match in response.get("matches", []):
            doc_content = match.get("document", "")
            doc_metadata = match.get("metadata", {})
            # Crea un oggetto Document compatibile con Langchain
            documents.append({
                "page_content": doc_content,
                "metadata": doc_metadata
            })
        # Ora possiamo usare questi documenti come contesto per la generazione
        context = "\n\n".join([doc["page_content"] for doc in documents])
        
        # Crea un retriever simulato che restituisce i documenti già recuperati
        class SimpleRetriever:
            def get_relevant_documents(self, query):
                # Restituisce i documenti già recuperati
                from langchain.docstore.document import Document
                return [Document(page_content=doc["page_content"], metadata=doc["metadata"]) for doc in documents]
        
        # Crea un'istanza del retriever simulato
        retriever = SimpleRetriever()
        
    except Exception as e:
        logger.error(f"Error querying vectorstore: {e}")
        return {"answer": "Errore: il sistema non è pronto per rispondere (servizio non disponibile).", "source": "error", "total_tokens": 0}
    
    logger.info(f"[DEBUG] system_prompt PRIMA di chiamare process_question_rag: {system_prompt}")
    print(f">>> system_prompt in run_rag_with_token_count: {system_prompt}")
    return run_rag_with_token_count(
        question=question,
        retriever=retriever,
        history=history,
        model_name=model,
        max_history=max_history,
        system_prompt=system_prompt
    )


# Fallback GPT
import openai

def run_fallback_gpt(question: str, model: str = "gpt-4o", system_prompt: Optional[str] = None) -> dict:
    try:
        logger.info(f"RAG Engine (run_fallback_gpt): Esecuzione fallback GPT via OpenAI API... [DEBUG MODELLO GPT USATO: {model}]")
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": question})
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        answer = response.choices[0].message.content or ""
        total_tokens = getattr(response.usage, 'total_tokens', 0) if response.usage else 0
        logger.info(f"RAG Engine (run_fallback_gpt): Risposta: {answer[:50]}... Token usati: {total_tokens}")
        return {"answer": answer, "source": "gpt", "total_tokens": total_tokens}
    except Exception as e:
        logger.error(f"Errore durante run_fallback_gpt: {e}", exc_info=True)
        return {"answer": f"Errore nel fallback GPT: {str(e)}", "source": "error", "total_tokens": 0}

# Stato indice
def get_index_status():
    # Usa VectorstoreService per ottenere lo stato
    try:
        client = VectorstoreServiceClient()
        
        # Ottieni informazioni sullo stato del servizio
        health = client._request("GET", "/health/dependencies")
        
        # Aggiungi flag per connessione ChromaDB
        if "dependencies" in health and "chroma" in health["dependencies"]:
            health["chroma_connected"] = health["dependencies"]["chroma"].get("connected", 
                                      health["dependencies"]["chroma"].get("status") == "healthy")
        
        # Ottieni statistiche direttamente dall'endpoint frontend compatibile
        frontend_stats = client.get_vectorstore_statistics()
        total_docs_from_stats = frontend_stats.get("total_documents", 0)
        
        # Poiché le statistiche sembrano non funzionare correttamente,
        # ottieni il conteggio dai documenti effettivi
        frontend_docs = client.get_vectorstore_documents()
        total_docs_from_docs = len(frontend_docs.get("documents", []))
        
        # Usa il valore maggiore tra i due
        total_docs = max(total_docs_from_stats, total_docs_from_docs)
        
        # Ottieni statistiche generali
        stats = client.get_stats()
        
        return {
            "status": "ok" if total_docs > 0 else "empty",
            "documents_in_index": total_docs,
            "vector_store": "VectorstoreService",
            "service": "VectorstoreService",
            "chroma_connected": health.get("chroma_connected", True),
            "version": health.get("version", "unknown"),
            "stats": stats,
            "health": health
        }
    except Exception as e:
        logger.error(f"Errore durante recupero stato vectorstore: {e}", exc_info=True)
        return {
            "status": "error",
            "documents_in_index": 0,
            "error": str(e)
        }
