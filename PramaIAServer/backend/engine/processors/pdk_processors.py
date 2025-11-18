"""
PDK Processors

Processori per i nodi dei plugin PDK.
"""

import logging
import os
from typing import Dict, Any
import httpx

from backend.engine.node_registry import BaseNodeProcessor
from backend.engine.execution_context import ExecutionContext

logger = logging.getLogger(__name__)

class PDKNodeProcessor(BaseNodeProcessor):
    """
    Processore per i nodi PDK.
    Gestisce l'esecuzione di nodi forniti dai plugin PDK.
    """
    
    def __init__(self, plugin_id: str, node_id: str, pdk_server_url: str = None):
        self.plugin_id = plugin_id
        self.node_id = node_id
        # Risolvi PDK server URL da parametro o da variabili d'ambiente
        default_pdk = os.getenv('PDK_SERVER_BASE_URL') or os.getenv('PDK_SERVER_URL') or 'http://localhost:3001'
        if pdk_server_url:
            self.pdk_server_url = pdk_server_url
        else:
            self.pdk_server_url = default_pdk
    
    async def execute(self, node: Dict[str, Any], context: ExecutionContext) -> Any:
        """
        Esegue il nodo PDK inviando la richiesta al server PDK.
        """
        try:
            # Prepara i dati per la richiesta
            input_data = await context.get_input("input")
            config = node.get("config", {})
            
            payload = {
                "input": input_data,
                "config": config
            }
            
            # Esegui la richiesta al server PDK
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.pdk_server_url}/process",
                    json=payload
                )
                result = response.json()
                
                # Imposta l'output nel contesto
                await context.set_output("output", result.get("output"))
                return result.get("output")
                
        except Exception as e:
            logger.error(f"Errore nell'esecuzione del nodo PDK {self.node_id}: {e}")
            raise
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Valida la configurazione del nodo PDK.
        Per ora accetta qualsiasi configurazione valida JSON.
        """
        return isinstance(config, dict)
