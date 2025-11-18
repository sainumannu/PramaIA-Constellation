from fastapi import APIRouter
from typing import List

router = APIRouter()

@router.get("/providers", response_model=List[str])
def get_llm_providers():
    """Restituisce la lista dei provider LLM disponibili."""
    return [
        "openai",
        "ollama",
        "anthropic",
        "gemini"
    ]
