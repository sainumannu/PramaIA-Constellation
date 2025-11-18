"""
LLM Node Processors

Processori per nodi LLM (OpenAI, Anthropic, etc.)
"""

import logging
from typing import Dict, Any, Optional
import asyncio

from backend.engine.node_registry import BaseNodeProcessor
from backend.engine.execution_context import ExecutionContext
from backend.llm.dispatcher import get_provider

logger = logging.getLogger(__name__)


class BaseLLMProcessor(BaseNodeProcessor):
    """
    Classe base per tutti i processori LLM.
    
    Fornisce funzionalità comuni per interazioni con LLM.
    """
    
    def __init__(self, provider: str):
        self.provider = provider
        self.llm_provider = get_provider(provider)
    
    async def execute(self, node, context: ExecutionContext) -> str:
        """
        Esegue una chiamata LLM.
        
        Template method pattern - le sottoclassi possono personalizzare
        la preparazione del prompt e il post-processing.
        """
        logger.info(f"🤖 Processando nodo LLM '{node.name}' (provider: {self.provider})")
        
        # Ottieni i dati di input per questo nodo
        input_data = context.get_input_for_node(node.node_id)
        
        # Prepara il prompt
        prompt = await self._prepare_prompt(node, input_data)
        
        # Ottieni la configurazione del modello
        model_config = self._get_model_config(node)
        
        # Esegui la chiamata LLM
        try:
            response = await self._call_llm(prompt, model_config)
            
            # Post-process la risposta se necessario
            processed_response = await self._post_process_response(node, response)
            
            logger.info(f"✅ LLM response ricevuta: {len(processed_response)} caratteri")
            return processed_response
            
        except Exception as e:
            logger.error(f"❌ Errore chiamata LLM: {str(e)}")
            raise ValueError(f"Errore LLM nel nodo '{node.name}': {str(e)}")
    
    async def _prepare_prompt(self, node, input_data: Dict[str, Any]) -> str:
        """
        Prepara il prompt per l'LLM.
        
        Combina template del nodo con i dati di input.
        """
        config = node.config or {}
        
        # Prompt template dal nodo
        prompt_template = config.get("prompt", "")
        
        # Se non c'è un template, usa un prompt di default
        if not prompt_template:
            # Cerca il contenuto principale nell'input
            main_content = self._extract_main_content(input_data)
            prompt_template = f"Analizza il seguente contenuto:\n\n{main_content}"
        
        # Sostituzioni di variabili nel template
        prompt = prompt_template
        for key, value in input_data.items():
            placeholder = f"{{{key}}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))
        
        # Sostituzioni di variabili comuni
        common_placeholders = {
            "{input}": self._extract_main_content(input_data),
            "{user_input}": input_data.get("user_input", ""),
            "{text}": input_data.get("text", input_data.get("input", "")),
        }
        
        for placeholder, value in common_placeholders.items():
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))
        
        return prompt
    
    def _extract_main_content(self, input_data: Dict[str, Any]) -> str:
        """Estrae il contenuto principale dai dati di input."""
        # Ordine di priorità per trovare il contenuto principale
        priority_keys = ["input", "text", "user_input", "content", "message"]
        
        for key in priority_keys:
            if key in input_data and input_data[key]:
                return str(input_data[key])
        
        # Se non trovato, prendi il primo valore stringa non vuoto
        for value in input_data.values():
            if isinstance(value, str) and value.strip():
                return value
        
        return ""
    
    def _get_model_config(self, node) -> Dict[str, Any]:
        """Ottieni la configurazione del modello dal nodo."""
        config = node.config or {}
        
        return {
            "model": config.get("model", self._get_default_model()),
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 1000),
            "top_p": config.get("top_p", 1.0),
        }
    
    async def _call_llm(self, prompt: str, model_config: Dict[str, Any]) -> str:
        """Chiama l'LLM specificato."""
        # Usa il provider per chiamare l'LLM appropriato
        response = self.llm_provider.generate(
            prompt=prompt,
            **model_config
        )
        return response
    
    async def _post_process_response(self, node, response: str) -> str:
        """Post-process la risposta dell'LLM se necessario."""
        config = node.config or {}
        
        # Rimozione di prefissi/suffissi se configurati
        if "remove_prefix" in config:
            prefix = config["remove_prefix"]
            if response.startswith(prefix):
                response = response[len(prefix):]
        
        if "remove_suffix" in config:
            suffix = config["remove_suffix"]
            if response.endswith(suffix):
                response = response[:-len(suffix)]
        
        # Trim whitespace
        response = response.strip()
        
        return response
    
    def _get_default_model(self) -> str:
        """Ottieni il modello di default per questo provider."""
        defaults = {
            "openai": "gpt-3.5-turbo",
            "anthropic": "claude-3-sonnet-20240229",
            "gemini": "gemini-pro",
            "ollama": "llama2"
        }
        return defaults.get(self.provider, "gpt-3.5-turbo")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida la configurazione del nodo LLM."""
        allowed_keys = {
            "prompt", "model", "temperature", "max_tokens", "top_p",
            "remove_prefix", "remove_suffix"
        }
        
        # Verifica che non ci siano chiavi non supportate
        unknown_keys = set(config.keys()) - allowed_keys
        if unknown_keys:
            logger.warning(f"Chiavi di configurazione non riconosciute: {unknown_keys}")
        
        # Valida temperature se presente
        if "temperature" in config:
            temp = config["temperature"]
            if not isinstance(temp, (int, float)) or not (0 <= temp <= 2):
                return False
        
        # Valida max_tokens se presente
        if "max_tokens" in config:
            max_tokens = config["max_tokens"]
            if not isinstance(max_tokens, int) or max_tokens <= 0:
                return False
        
        return True


class OpenAIProcessor(BaseLLMProcessor):
    """Processore per nodi OpenAI."""
    
    def __init__(self):
        super().__init__("openai")


class AnthropicProcessor(BaseLLMProcessor):
    """Processore per nodi Anthropic."""
    
    def __init__(self):
        super().__init__("anthropic")


class GeminiProcessor(BaseLLMProcessor):
    """Processore per nodi Gemini."""
    
    def __init__(self):
        super().__init__("gemini")


class OllamaProcessor(BaseLLMProcessor):
    """
    Processore specializzato per nodi Ollama.
    
    Gestisce:
    - Modelli locali Ollama
    - Health check automatico
    - Pull automatico modelli
    - Streaming opzionale
    """
    
    def __init__(self):
        super().__init__("ollama")
    
    async def execute(self, node, context) -> str:
        """
        Esegue un nodo Ollama con controlli specifici.
        """
        logger.info(f"🦙 Eseguendo nodo Ollama '{node.name}'")
        
        try:
            # Verifica che Ollama sia in esecuzione
            if not await self.llm_provider.check_health():
                raise ValueError("Ollama non è in esecuzione. Avvia Ollama prima di eseguire il workflow.")
            
            # Ottieni i dati di input
            input_data = context.get_input_for_node(node.node_id)
            
            # Prepara il prompt
            prompt = await self._prepare_prompt(node, input_data)
            
            # Ottieni configurazione modello
            model_config = self._get_model_config(node)
            
            # Lista modelli disponibili per debug
            available_models = await self.llm_provider.list_models()
            logger.info(f"🦙 Modelli Ollama disponibili: {[m['name'] for m in available_models]}")
            
            # Esegui la chiamata
            response = await self.llm_provider.generate(
                prompt=prompt,
                **model_config
            )
            
            # Post-process la risposta
            processed_response = await self._post_process_response(node, response)
            
            logger.info(f"✅ Ollama response ricevuta: {len(processed_response)} caratteri")
            return processed_response
            
        except Exception as e:
            logger.error(f"❌ Errore nodo Ollama '{node.name}': {str(e)}")
            
            # Fornisci suggerimenti specifici per Ollama
            error_msg = str(e)
            if "not running" in error_msg.lower():
                error_msg += "\n\nSuggerimenti:\n- Avvia Ollama con: ollama serve\n- Verifica che sia in esecuzione su http://localhost:11434"
            elif "model" in error_msg.lower() and "not found" in error_msg.lower():
                error_msg += f"\n\nSuggerimenti:\n- Scarica il modello con: ollama pull {model_config.get('model', 'llama2')}\n- Verifica modelli disponibili con: ollama list"
            
            raise ValueError(f"Errore Ollama nel nodo '{node.name}': {error_msg}")
    
    def _get_default_model(self) -> str:
        """Modello di default per Ollama."""
        return "llama2"
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida configurazione specifica per Ollama."""
        # Chiavi specifiche per Ollama
        ollama_keys = {
            "prompt", "model", "temperature", "max_tokens", "system_prompt",
            "stream", "remove_prefix", "remove_suffix"
        }
        
        # Verifica chiavi non supportate
        unknown_keys = set(config.keys()) - ollama_keys
        if unknown_keys:
            logger.warning(f"Chiavi configurazione Ollama non riconosciute: {unknown_keys}")
        
        # Validazioni specifiche
        if "temperature" in config:
            temp = config["temperature"]
            if not isinstance(temp, (int, float)) or not (0 <= temp <= 2):
                logger.error(f"Temperature deve essere tra 0 e 2, ricevuto: {temp}")
                return False
        
        if "max_tokens" in config:
            max_tokens = config["max_tokens"]
            if not isinstance(max_tokens, int) or max_tokens <= 0:
                logger.error(f"max_tokens deve essere un intero positivo, ricevuto: {max_tokens}")
                return False
        
        # Modelli comuni per Ollama
        common_models = ["llama2", "llama2:13b", "mistral", "codellama", "neural-chat", "orca-mini"]
        if "model" in config:
            model = config["model"]
            if model not in common_models:
                logger.warning(f"Modello '{model}' non nella lista dei modelli comuni: {common_models}")
        
        return True
