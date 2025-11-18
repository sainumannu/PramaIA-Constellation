import logging
from typing import Optional
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import Chroma # Per il type hinting del retriever
import openai

from backend.core.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

def get_openai_embeddings() -> OpenAIEmbeddings:
    """Restituisce un'istanza di OpenAIEmbeddings."""
    return OpenAIEmbeddings()

def get_openai_llm(model_name: str = "gpt-4o") -> ChatOpenAI:
    """Restituisce un'istanza di OpenAI LLM con il modello specificato."""
    return ChatOpenAI(model=model_name)

# --- Prompt e Chain di Classificazione ---
CLASSIFICATION_PROMPT_TEMPLATE = """
Classifica la seguente domanda dell'utente in una delle seguenti categorie:

- smalltalk → se è un saluto, ringraziamento, o frase generica non informativa
- richiesta_informativa → se contiene una domanda che può richiedere contesto o contenuto del documento
- rischio_dati_sensibili → se contiene riferimenti a informazioni personali, documenti riservati o allegati

Domanda: {question}
Categoria:
"""
classification_prompt = PromptTemplate.from_template(CLASSIFICATION_PROMPT_TEMPLATE)
classification_chain = LLMChain(
    llm=get_openai_llm(),
    prompt=classification_prompt
)

# --- Prompt e Chain per Smalltalk ---
SMALLTALK_PROMPT_TEMPLATE = """
Sei un assistente virtuale amichevole e conciso. Rispondi in modo naturale e diretto a saluti, ringraziamenti o frasi generiche.

Domanda: {question}
Risposta:
"""
smalltalk_prompt = PromptTemplate.from_template(SMALLTALK_PROMPT_TEMPLATE)
smalltalk_chain = LLMChain(
    llm=get_openai_llm(),
    prompt=smalltalk_prompt
)

# --- Prompt per RAG (ConversationalRetrievalChain) ---
RAG_CUSTOM_PROMPT_TEMPLATE = """
Hai a disposizione alcune informazioni da un documento caricato. Usale **solo** se sono chiaramente utili per rispondere alla domanda.

Se la domanda è un saluto, una richiesta generica o non ha attinenza diretta con il contenuto, rispondi in modo cortese **senza usare il documento**.

Contesto disponibile:
{context}

Domanda dell'utente:
{question}

Risposta:
"""
rag_custom_prompt = PromptTemplate.from_template(RAG_CUSTOM_PROMPT_TEMPLATE)

def get_classification_chain(model_name: str = "gpt-4o"):
    return LLMChain(
        llm=get_openai_llm(model_name),
        prompt=classification_prompt
    )

def get_smalltalk_chain(model_name: str = "gpt-4o"):
    return LLMChain(
        llm=get_openai_llm(model_name),
        prompt=smalltalk_prompt
    )

FALLBACK_GPT_PROMPT_TEMPLATE = """
Non sono riuscito a classificare la domanda o a trovare una risposta adeguata. Rispondi in modo cortese e generico, invitando eventualmente l'utente a riformulare la domanda o a fornire maggiori dettagli.

Domanda: {question}
Risposta:
"""
fallback_gpt_prompt = PromptTemplate.from_template(FALLBACK_GPT_PROMPT_TEMPLATE)

def get_fallback_gpt_chain(model_name: str = "gpt-4o"):
    return LLMChain(
        llm=get_openai_llm(model_name),
        prompt=fallback_gpt_prompt
    )

def create_conversational_rag_chain(
    vectorstore_retriever: Chroma,
    memory: ConversationBufferMemory,
    model_name: str = "gpt-4o"
) -> ConversationalRetrievalChain:
    return ConversationalRetrievalChain.from_llm(
        llm=get_openai_llm(model_name),
        retriever=vectorstore_retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": rag_custom_prompt}
    )

def run_rag_with_token_count(
    question: str,
    retriever,
    history=None,
    model_name: str = "gpt-4o",
    max_history: int = 5,  # <-- numero di interazioni da dashboard
    system_prompt: Optional[str] = None  # <-- nuovo parametro opzionale
):
    """
    Esegue una richiesta RAG includendo tutti i documenti rilevanti e solo le ultime N interazioni dalla history.
    max_history: numero di interazioni (user+assistant) da includere dalla cronologia.
    """
    # 1. Recupera TUTTI i documenti rilevanti (senza taglio)
    docs = retriever.get_relevant_documents(question)
    context = "\n\n".join([doc.page_content for doc in docs])

    prompt = rag_custom_prompt.format(context=context, question=question)
    if system_prompt:
        prompt = f"[ISTRUZIONI DI SISTEMA]: {str(system_prompt)}\n\n{prompt}"

    # 2. Limita la history alle ultime N interazioni (N*2 messaggi: user+assistant)
    messages = []
    if system_prompt is not None:
        messages.append({"role": "system", "content": str(system_prompt)})
    if history:
        messages.extend([m for m in history[-max_history*2:] if m["role"] in ("user", "assistant")])
    messages.append({"role": "user", "content": prompt})

    # Qui inserisci il blocco di debug:
    logger.info(f"[RAG][DEBUG] Messaggi inviati a OpenAI:\n" + "\n".join([f"{m['role']}: {m['content'][:200]}" for m in messages]))
    print("[RAG][DEBUG] Messaggi inviati a OpenAI:")
    for m in messages:
        print(f"{m['role']}: {m['content'][:200]}")

    logger.info(f"[RAG] MODELLO GPT UTILIZZATO: {model_name}")
    logger.info(f"History inviata a OpenAI: {history}")
    logger.info(f"[DEBUG] system_prompt passato a RAG: {system_prompt}")
    print(f"[DEBUG] system_prompt passato a RAG: {system_prompt}")

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=model_name,
        messages=messages
    )
    answer = response.choices[0].message.content
    total_tokens = response.usage.total_tokens if response.usage else 0
    return {"answer": answer, "total_tokens": total_tokens, "source": "docs"}
