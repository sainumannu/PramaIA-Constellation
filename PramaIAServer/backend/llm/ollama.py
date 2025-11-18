"""
Ollama LLM Provider

Provider per modelli LLM locali tramite Ollama.
Supporta tutti i modelli disponibili localmente.
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from .base import LLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """
    Provider per Ollama - esegue modelli LLM localmente.
    
    Caratteristiche:
    - Nessun costo per token
    - Privacy completa (tutto locale)
    - Supporto streaming
    - Modelli personalizzabili
    """
    
    def __init__(self):
        # Configurazione di default per Ollama
        self.base_url = "http://localhost:11434"
        self.timeout = 300  # 5 minuti per modelli più lenti
        self.available_models = []
        self._session = None
        
        # Modelli comuni disponibili su Ollama
        self.common_models = {
            "llama2": "Llama 2 7B - Modello generale",
            "llama2:13b": "Llama 2 13B - Più potente",
            "codellama": "Code Llama - Specializzato per codice",
            "mistral": "Mistral 7B - Veloce e efficiente", 
            "neural-chat": "Neural Chat - Conversazioni",
            "starling-lm": "Starling LM - Istruzioni",
            "orca-mini": "Orca Mini - Modello compatto",
            "vicuna": "Vicuna - Conversazioni avanzate",
            "wizardcoder": "Wizard Coder - Programmazione",
            "dolphin-mixtral": "Dolphin Mixtral - Versatile"
        }
        
        logger.info("🦙 OllamaProvider inizializzato")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Ottieni o crea una sessione HTTP."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Effettua una richiesta HTTP a Ollama."""
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error {response.status}: {error_text}")
        
        except aiohttp.ClientError as e:
            raise Exception(f"Connection error to Ollama: {str(e)}")
    
    async def check_health(self) -> bool:
        """Verifica se Ollama è in esecuzione e raggiungibile."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/version") as response:
                if response.status == 200:
                    version_info = await response.json()
                    logger.info(f"✅ Ollama is running - Version: {version_info.get('version', 'unknown')}")
                    return True
                return False
        except Exception as e:
            logger.warning(f"❌ Ollama health check failed: {str(e)}")
            return False
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """Lista tutti i modelli disponibili in Ollama."""
        try:
            result = await self._make_request("api/tags", {})
            models = result.get("models", [])
            
            self.available_models = [model["name"] for model in models]
            
            logger.info(f"📋 Found {len(models)} Ollama models: {self.available_models}")
            return models
            
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {str(e)}")
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """Scarica un modello se non è già presente."""
        try:
            logger.info(f"📥 Pulling model {model_name}...")
            
            # Verifica se il modello è già presente
            models = await self.list_models()
            if model_name in self.available_models:
                logger.info(f"✅ Model {model_name} already available")
                return True
            
            # Effettua il pull del modello
            session = await self._get_session()
            url = f"{self.base_url}/api/pull"
            data = {"name": model_name}
            
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    # Il pull può richiedere molto tempo, monitora il progresso
                    async for line in response.content:
                        if line:
                            try:
                                progress = json.loads(line.decode())
                                if "status" in progress:
                                    logger.info(f"📥 {progress['status']}")
                                if progress.get("status") == "success":
                                    logger.info(f"✅ Model {model_name} pulled successfully")
                                    return True
                            except json.JSONDecodeError:
                                continue
                else:
                    logger.error(f"Failed to pull model {model_name}: HTTP {response.status}")
                    return False
        
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {str(e)}")
            return False
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Genera una risposta usando Ollama.
        
        Args:
            prompt: Il prompt per il modello
            **kwargs: Parametri aggiuntivi (model, temperature, max_tokens, etc.)
        
        Returns:
            La risposta generata dal modello
        """
        # Configurazione di default
        model = kwargs.get("model", "llama2")
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)
        system_prompt = kwargs.get("system_prompt", "")
        
        # Verifica che Ollama sia disponibile
        if not await self.check_health():
            raise Exception("Ollama is not running or not accessible")
        
        # Verifica che il modello sia disponibile
        await self.list_models()
        if model not in self.available_models:
            logger.info(f"🔄 Model {model} not found, attempting to pull...")
            if not await self.pull_model(model):
                raise Exception(f"Failed to pull model {model}")
        
        # Prepara la richiesta
        request_data = {
            "model": model,
            "prompt": prompt,
            "stream": False,  # Per ora non streaming
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        # Aggiungi system prompt se fornito
        if system_prompt:
            request_data["system"] = system_prompt
        
        logger.info(f"🦙 Generating with Ollama model '{model}'...")
        
        try:
            result = await self._make_request("api/generate", request_data)
            
            response_text = result.get("response", "")
            
            # Log delle statistiche se disponibili
            if "eval_count" in result and "eval_duration" in result:
                tokens = result["eval_count"]
                duration_ns = result["eval_duration"]
                tokens_per_second = tokens / (duration_ns / 1e9) if duration_ns > 0 else 0
                
                logger.info(f"✅ Generated {tokens} tokens in {duration_ns/1e9:.2f}s ({tokens_per_second:.1f} tokens/s)")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Ollama generation failed: {str(e)}")
            raise Exception(f"Ollama generation error: {str(e)}")
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Genera una risposta in streaming usando Ollama.
        
        Args:
            prompt: Il prompt per il modello
            **kwargs: Parametri aggiuntivi
            
        Yields:
            Chunks della risposta in streaming
        """
        model = kwargs.get("model", "llama2")
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)
        system_prompt = kwargs.get("system_prompt", "")
        
        # Verifica disponibilità
        if not await self.check_health():
            raise Exception("Ollama is not running or not accessible")
        
        await self.list_models()
        if model not in self.available_models:
            if not await self.pull_model(model):
                raise Exception(f"Failed to pull model {model}")
        
        # Prepara richiesta streaming
        request_data = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        if system_prompt:
            request_data["system"] = system_prompt
        
        logger.info(f"🦙 Starting streaming generation with model '{model}'...")
        
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/generate"
            
            async with session.post(url, json=request_data) as response:
                if response.status == 200:
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line.decode())
                                if "response" in chunk:
                                    yield chunk["response"]
                                
                                # Fine dello stream
                                if chunk.get("done", False):
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                else:
                    error_text = await response.text()
                    raise Exception(f"Ollama streaming error {response.status}: {error_text}")
        
        except Exception as e:
            logger.error(f"Ollama streaming failed: {str(e)}")
            raise Exception(f"Ollama streaming error: {str(e)}")
    
    def get_recommended_models(self) -> Dict[str, str]:
        """Restituisce un dizionario dei modelli raccomandati con descrizioni."""
        return self.common_models
    
    async def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Ottieni informazioni dettagliate su un modello specifico.
        """
        try:
            # Verifica prima se il modello è installato
            models = await self.list_models()
            model_info = None
            
            for model in models:
                if model.get("name") == model_name:
                    model_info = model
                    break
            
            if not model_info:
                return None
            
            # Arricchisci con informazioni aggiuntive
            model_info["recommended"] = model_name in self.common_models
            if model_name in self.common_models:
                model_info["description"] = self.common_models[model_name]
            
            return model_info
            
        except Exception as e:
            logger.error(f"Error getting model info for {model_name}: {str(e)}")
            return None

    async def cleanup(self):
        """Pulisci le risorse."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("🧹 Ollama session cleaned up")