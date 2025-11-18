"""
Input Node Processors

Processori per nodi di input (user input, file upload, etc.)
"""

import logging
from typing import Dict, Any

from backend.engine.node_registry import BaseNodeProcessor
from backend.engine.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


class UserInputProcessor(BaseNodeProcessor):
    """
    Processore per nodi di input utente.
    
    Riceve input testuali dall'utente e li passa al workflow.
    """
    
    async def execute(self, node, context: ExecutionContext) -> str:
        """
        Esegue il nodo di input utente.
        
        Prende l'input dell'utente dai dati di input del contesto.
        """
        logger.info(f"📝 Processando input utente per nodo '{node.name}'")
        
        # Ottieni i dati di input per questo nodo
        input_data = context.get_input_for_node(node.node_id)
        
        # Cerca l'input utente nei dati
        user_input = None
        
        # Prova diverse chiavi possibili
        possible_keys = ["user_input", "input", "text", "message", "query"]
        for key in possible_keys:
            if key in input_data:
                user_input = input_data[key]
                break
        
        # Se non trovato, usa il primo valore stringa disponibile
        if user_input is None:
            for value in input_data.values():
                if isinstance(value, str) and value.strip():
                    user_input = value
                    break
        
        if user_input is None:
            raise ValueError(f"Nessun input utente trovato per il nodo '{node.name}'")
        
        # Applica eventuali trasformazioni dalla configurazione
        config = node.config or {}
        
        # Placeholder replacement se configurato
        if "placeholder" in config and config["placeholder"] in str(user_input):
            user_input = str(user_input).replace(config["placeholder"], "")
        
        # Validazione lunghezza se configurata
        if "max_length" in config:
            max_length = config["max_length"]
            if len(str(user_input)) > max_length:
                user_input = str(user_input)[:max_length]
                logger.warning(f"Input troncato a {max_length} caratteri per nodo '{node.name}'")
        
        # Validazione required se configurata
        if config.get("required", False) and not str(user_input).strip():
            raise ValueError(f"Input richiesto per il nodo '{node.name}' ma non fornito")
        
        result = str(user_input).strip()
        logger.info(f"✅ Input utente processato: {len(result)} caratteri")
        
        return result
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida la configurazione del nodo."""
        # Configurazioni opzionali supportate
        allowed_keys = {"placeholder", "max_length", "required", "validation_regex"}
        
        # Verifica che non ci siano chiavi non supportate
        unknown_keys = set(config.keys()) - allowed_keys
        if unknown_keys:
            logger.warning(f"Chiavi di configurazione non riconosciute: {unknown_keys}")
        
        # Valida max_length se presente
        if "max_length" in config:
            max_length = config["max_length"]
            if not isinstance(max_length, int) or max_length <= 0:
                return False
        
        # Valida required se presente
        if "required" in config:
            if not isinstance(config["required"], bool):
                return False
        
        return True


class FileInputProcessor(BaseNodeProcessor):
    """
    Processore per nodi di upload file.
    
    Gestisce file caricati dall'utente e ne estrae il contenuto.
    """
    
    async def execute(self, node, context: ExecutionContext) -> str:
        """
        Esegue il nodo di input file.
        
        Estrae il contenuto dal file caricato.
        """
        logger.info(f"📁 Processando file input per nodo '{node.name}'")
        
        # Ottieni i dati di input per questo nodo
        input_data = context.get_input_for_node(node.node_id)
        
        # Cerca file nei dati di input
        file_content = None
        file_path = None
        
        # Prova diverse chiavi possibili
        if "file_content" in input_data:
            file_content = input_data["file_content"]
        elif "file_path" in input_data:
            file_path = input_data["file_path"]
        elif "file" in input_data:
            # Potrebbe essere contenuto o percorso
            file_data = input_data["file"]
            if isinstance(file_data, str):
                if file_data.startswith("/") or file_data.startswith("C:"):
                    file_path = file_data
                else:
                    file_content = file_data
        
        # Se abbiamo un percorso, leggi il file
        if file_path and not file_content:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                logger.info(f"📖 File letto da: {file_path}")
            except Exception as e:
                logger.error(f"❌ Errore lettura file {file_path}: {str(e)}")
                raise ValueError(f"Impossibile leggere il file: {str(e)}")
        
        if not file_content:
            raise ValueError(f"Nessun contenuto file trovato per il nodo '{node.name}'")
        
        # Applica filtri dalla configurazione
        config = node.config or {}
        
        # Filtro per tipo di file se configurato
        accepted_types = config.get("acceptedTypes", [])
        if accepted_types and file_path:
            file_extension = file_path.split('.')[-1].lower()
            if file_extension not in [t.lower() for t in accepted_types]:
                raise ValueError(f"Tipo di file non supportato: {file_extension}")
        
        # Limite dimensione se configurato
        max_size = config.get("maxSize")
        if max_size and len(file_content) > max_size:
            raise ValueError(f"File troppo grande: {len(file_content)} > {max_size}")
        
        logger.info(f"✅ File processato: {len(file_content)} caratteri")
        
        return file_content
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida la configurazione del nodo."""
        allowed_keys = {"acceptedTypes", "maxSize"}
        
        # Verifica che non ci siano chiavi non supportate
        unknown_keys = set(config.keys()) - allowed_keys
        if unknown_keys:
            logger.warning(f"Chiavi di configurazione non riconosciute: {unknown_keys}")
        
        # Valida acceptedTypes se presente
        if "acceptedTypes" in config:
            accepted_types = config["acceptedTypes"]
            if not isinstance(accepted_types, list):
                return False
            if not all(isinstance(t, str) for t in accepted_types):
                return False
        
        # Valida maxSize se presente
        if "maxSize" in config:
            max_size = config["maxSize"]
            if not isinstance(max_size, (int, str)):
                return False
        
        return True
