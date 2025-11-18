"""
Ollama Management API Router

Endpoints per gestire modelli Ollama locali.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
import logging

from backend.auth.dependencies import get_current_user
from backend.db.models import User
from backend.llm.ollama import OllamaProvider

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/ollama",
    tags=["ollama"],
    responses={404: {"description": "Not found"}},
)

# Istanza globale del provider Ollama
ollama_provider = OllamaProvider()


@router.get("/health")
async def check_ollama_health(
    current_user: User = Depends(get_current_user)
):
    """
    Verifica lo stato di Ollama
    """
    try:
        is_healthy = await ollama_provider.check_health()
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "is_running": is_healthy,
            "base_url": ollama_provider.base_url,
            "message": "Ollama is running" if is_healthy else "Ollama is not accessible"
        }
        
    except Exception as e:
        logger.error(f"Error checking Ollama health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error checking Ollama: {str(e)}"
        )


@router.get("/models", response_model=List[Dict[str, Any]])
async def list_ollama_models(
    current_user: User = Depends(get_current_user)
):
    """
    Lista tutti i modelli disponibili in Ollama
    """
    try:
        models = await ollama_provider.list_models()
        
        # Arricchisci con informazioni sui modelli raccomandati
        recommended = ollama_provider.get_recommended_models()
        
        for model in models:
            model_name = model.get("name", "")
            if model_name in recommended:
                model["description"] = recommended[model_name]
                model["recommended"] = True
            else:
                model["recommended"] = False
        
        return models
        
    except Exception as e:
        logger.error(f"Error listing Ollama models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing models: {str(e)}"
        )


@router.get("/models/recommended")
async def get_recommended_models(
    current_user: User = Depends(get_current_user)
):
    """
    Ottieni la lista dei modelli raccomandati per Ollama
    """
    try:
        recommended = ollama_provider.get_recommended_models()
        
        # Verifica quali sono già installati
        available_models = await ollama_provider.list_models()
        installed_names = [model["name"] for model in available_models]
        
        result = []
        for model_name, description in recommended.items():
            result.append({
                "name": model_name,
                "description": description,
                "installed": model_name in installed_names,
                "size": "Unknown",  # Ollama API non fornisce sempre la size
                "category": _get_model_category(model_name)
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting recommended models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting recommended models: {str(e)}"
        )


@router.post("/models/{model_name}/pull")
async def pull_model(
    model_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Scarica un modello Ollama
    """
    try:
        logger.info(f"User {current_user.email} requested to pull model {model_name}")
        
        # Verifica se il modello è già presente
        models = await ollama_provider.list_models()
        installed_names = [model["name"] for model in models]
        
        if model_name in installed_names:
            return {
                "status": "already_installed",
                "message": f"Model {model_name} is already installed",
                "model_name": model_name
            }
        
        # Effettua il pull
        success = await ollama_provider.pull_model(model_name)
        
        if success:
            return {
                "status": "success",
                "message": f"Model {model_name} pulled successfully",
                "model_name": model_name
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to pull model {model_name}"
            )
        
    except Exception as e:
        logger.error(f"Error pulling model {model_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error pulling model: {str(e)}"
        )


@router.get("/models/{model_name}/info")
async def get_model_info(
    model_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Ottieni informazioni dettagliate su un modello
    """
    try:
        info = await ollama_provider.get_model_info(model_name)
        
        if not info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_name} not found"
            )
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info for {model_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting model info: {str(e)}"
        )


@router.post("/test")
async def test_ollama_generation(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Testa la generazione con Ollama
    """
    try:
        prompt = request.get("prompt", "Hello, how are you?")
        model = request.get("model", "llama2")
        temperature = request.get("temperature", 0.7)
        max_tokens = request.get("max_tokens", 100)
        
        logger.info(f"Testing Ollama generation with model {model}")
        
        response = await ollama_provider.generate(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            "status": "success",
            "prompt": prompt,
            "response": response,
            "model": model,
            "config": {
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        }
        
    except Exception as e:
        logger.error(f"Error testing Ollama generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing generation: {str(e)}"
        )


@router.get("/status")
async def get_ollama_status(
    current_user: User = Depends(get_current_user)
):
    """
    Ottieni stato completo di Ollama
    """
    try:
        is_healthy = await ollama_provider.check_health()
        models = await ollama_provider.list_models() if is_healthy else []
        recommended = ollama_provider.get_recommended_models()
        
        return {
            "is_running": is_healthy,
            "base_url": ollama_provider.base_url,
            "total_models": len(models),
            "available_models": [model["name"] for model in models],
            "recommended_models": list(recommended.keys()),
            "status": "ready" if is_healthy and len(models) > 0 else "needs_setup"
        }
        
    except Exception as e:
        logger.error(f"Error getting Ollama status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting status: {str(e)}"
        )


def _get_model_category(model_name: str) -> str:
    """Categorizza un modello in base al nome."""
    model_name_lower = model_name.lower()
    
    if "code" in model_name_lower or "wizard" in model_name_lower:
        return "Programming"
    elif "chat" in model_name_lower or "neural" in model_name_lower:
        return "Conversation"
    elif "mini" in model_name_lower or "orca" in model_name_lower:
        return "Compact"
    elif "instruct" in model_name_lower or "starling" in model_name_lower:
        return "Instruction"
    else:
        return "General"


# Cleanup al shutdown dell'app
async def cleanup_ollama():
    """Cleanup delle risorse Ollama."""
    await ollama_provider.cleanup()
