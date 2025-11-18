from pydantic import BaseModel, Field
from typing import Optional, Any

class RAGProcessedResponse(BaseModel):
    answer: str
    source: Optional[str] = None # Potrebbe essere 'docs', 'chat', 'gpt', 'blocked', 'error', ecc.
    session_id: str = Field(..., description="L'ID della sessione RAG, potrebbe essere nuovo o esistente.")
    tokens: int = Field(..., ge=0, description="Numero di token totali (prompt + completion) utilizzati per questa interazione.")
    # category: Optional[str] = None # Campo opzionale se vuoi includere la categoria della domanda
    # Potresti aggiungere altri campi se necessario, ad esempio i documenti sorgente recuperati
    # retrieved_documents: Optional[List[Dict[str, Any]]] = None