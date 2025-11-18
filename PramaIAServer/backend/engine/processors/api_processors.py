"""
API and HTTP Node Processors

Processori per interazioni con API REST, webhook, e servizi esterni.
"""

import aiohttp
import json
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse
import logging

from backend.engine.node_registry import BaseNodeProcessor

logger = logging.getLogger(__name__)


class HTTPRequestProcessor(BaseNodeProcessor):
    """
    Processore per richieste HTTP.
    Supporta GET, POST, PUT, DELETE con headers e autenticazione.
    """
    
    async def execute(self, node, context) -> Dict[str, Any]:
        """
        Esegue richieste HTTP.
        
        Configurazioni supportate:
        - method: "GET", "POST", "PUT", "DELETE"
        - url: URL della richiesta
        - headers: headers HTTP
        - auth_type: "none", "basic", "bearer", "api_key"
        - auth_config: configurazione autenticazione
        - timeout: timeout in secondi
        - retry_count: numero di retry
        """
        config = node.configuration or {}
        method = config.get("method", "GET").upper()
        url = config.get("url", "")
        
        if not url:
            raise ValueError("URL richiesta non specificata")
        
        # Ottieni dati di input per il body della richiesta
        input_data = self._get_input_data(node, context)
        
        # Prepara headers
        headers = self._prepare_headers(config)
        
        # Prepara body della richiesta
        body = self._prepare_body(input_data, config)
        
        # Esegui la richiesta
        try:
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=config.get("timeout", 30))
                
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body if body else None,
                    timeout=timeout
                ) as response:
                    
                    response_data = await self._process_response(response)
                    
                    return {
                        "status": "success",
                        "data": response_data,
                        "http_status": response.status,
                        "headers": dict(response.headers),
                        "url": str(response.url)
                    }
        
        except aiohttp.ClientError as e:
            logger.error(f"Errore HTTP nella richiesta a {url}: {str(e)}")
            raise ValueError(f"Errore HTTP: {str(e)}")
        except Exception as e:
            logger.error(f"Errore generico nella richiesta HTTP: {str(e)}")
            raise ValueError(f"Errore richiesta: {str(e)}")
    
    def _get_input_data(self, node, context) -> Any:
        """Ottiene i dati di input dai nodi predecessori."""
        for conn in context.workflow.connections:
            if conn.to_node_id == node.node_id:
                return context.get_node_result(conn.from_node_id)
        return {}
    
    def _prepare_headers(self, config: Dict) -> Dict[str, str]:
        """Prepara gli headers HTTP."""
        headers = config.get("headers", {}).copy()
        
        # Aggiungi Content-Type se non presente
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"
        
        # Gestione autenticazione
        auth_type = config.get("auth_type", "none")
        auth_config = config.get("auth_config", {})
        
        if auth_type == "bearer":
            token = auth_config.get("token", "")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        
        elif auth_type == "api_key":
            api_key = auth_config.get("api_key", "")
            header_name = auth_config.get("header_name", "X-API-Key")
            if api_key:
                headers[header_name] = api_key
        
        return headers
    
    def _prepare_body(self, input_data: Any, config: Dict) -> Optional[Dict]:
        """Prepara il body della richiesta."""
        if config.get("method", "GET").upper() in ["GET", "DELETE"]:
            return None
        
        if isinstance(input_data, dict):
            if "data" in input_data:
                return input_data["data"]
            return input_data
        
        return {"data": input_data}
    
    async def _process_response(self, response: aiohttp.ClientResponse) -> Any:
        """Elabora la risposta HTTP."""
        content_type = response.headers.get("Content-Type", "")
        
        if "application/json" in content_type:
            try:
                return await response.json()
            except json.JSONDecodeError:
                return await response.text()
        else:
            return await response.text()
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida la configurazione del nodo."""
        if not config.get("url"):
            return False
        
        method = config.get("method", "GET").upper()
        if method not in ["GET", "POST", "PUT", "DELETE"]:
            return False
        
        auth_type = config.get("auth_type", "none")
        if auth_type not in ["none", "basic", "bearer", "api_key"]:
            return False
        
        return True


class WebhookProcessor(BaseNodeProcessor):
    """
    Processore per invio webhook.
    Invia dati a endpoint webhook configurati.
    """
    
    async def execute(self, node, context) -> Dict[str, Any]:
        """
        Invia webhook.
        
        Configurazioni supportate:
        - webhook_url: URL del webhook
        - method: metodo HTTP (default POST)
        - headers: headers aggiuntivi
        - secret: secret per firma HMAC
        - retry_count: numero di retry
        """
        config = node.configuration or {}
        webhook_url = config.get("webhook_url", "")
        
        if not webhook_url:
            raise ValueError("URL webhook non specificata")
        
        # Ottieni dati da inviare
        input_data = self._get_input_data(node, context)
        
        # Prepara payload
        payload = self._prepare_payload(input_data, config)
        
        # Prepara headers
        headers = self._prepare_webhook_headers(config, payload)
        
        # Invia webhook
        try:
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=config.get("timeout", 30))
                
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=timeout
                ) as response:
                    
                    response_text = await response.text()
                    
                    return {
                        "status": "success",
                        "webhook_url": webhook_url,
                        "http_status": response.status,
                        "response": response_text,
                        "sent_at": context.get_current_time()
                    }
        
        except Exception as e:
            logger.error(f"Errore invio webhook a {webhook_url}: {str(e)}")
            raise ValueError(f"Errore webhook: {str(e)}")
    
    def _get_input_data(self, node, context) -> Any:
        """Ottiene i dati di input dai nodi predecessori."""
        for conn in context.workflow.connections:
            if conn.to_node_id == node.node_id:
                return context.get_node_result(conn.from_node_id)
        return {}
    
    def _prepare_payload(self, input_data: Any, config: Dict) -> Dict[str, Any]:
        """Prepara il payload del webhook."""
        payload = {
            "timestamp": context.get_current_time() if hasattr(context, 'get_current_time') else None,
            "data": input_data
        }
        
        # Aggiungi metadati se configurati
        if config.get("include_metadata", True):
            payload["metadata"] = {
                "node_id": config.get("node_id"),
                "workflow_id": config.get("workflow_id"),
                "execution_id": config.get("execution_id")
            }
        
        return payload
    
    def _prepare_webhook_headers(self, config: Dict, payload: Dict) -> Dict[str, str]:
        """Prepara headers per il webhook."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "PramaIA-Workflow-Engine/1.0"
        }
        
        # Aggiungi headers personalizzati
        custom_headers = config.get("headers", {})
        headers.update(custom_headers)
        
        # Aggiungi firma HMAC se configurata
        secret = config.get("secret", "")
        if secret:
            # TODO: Implementare firma HMAC
            pass
        
        return headers

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida la configurazione del nodo Webhook."""
        if not config.get("webhook_url"):
            return False
        
        method = config.get("method", "POST").upper()
        if method not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            return False
        
        return True


class APICallProcessor(BaseNodeProcessor):
    """
    Processore per chiamate API avanzate.
    Supporta paginazione, rate limiting, e trasformazione dati.
    """
    
    async def execute(self, node, context) -> Dict[str, Any]:
        """
        Esegue chiamate API avanzate.
        
        Configurazioni supportate:
        - base_url: URL base dell'API
        - endpoint: endpoint specifico
        - method: metodo HTTP
        - pagination: configurazione paginazione
        - rate_limit: limite di richieste
        - transform_response: trasformazione risposta
        """
        config = node.configuration or {}
        base_url = config.get("base_url", "")
        endpoint = config.get("endpoint", "")
        
        if not base_url:
            raise ValueError("URL base API non specificata")
        
        # Costruisci URL completo
        full_url = urljoin(base_url, endpoint)
        
        # Ottieni dati di input
        input_data = self._get_input_data(node, context)
        
        # Gestisci paginazione se configurata
        if config.get("pagination", {}).get("enabled", False):
            results = await self._execute_paginated_request(full_url, config, input_data)
        else:
            results = await self._execute_single_request(full_url, config, input_data)
        
        # Trasforma risposta se configurato
        if config.get("transform_response", {}).get("enabled", False):
            results = self._transform_response(results, config)
        
        return {
            "status": "success",
            "data": results,
            "url": full_url,
            "total_requests": 1 if not config.get("pagination", {}).get("enabled", False) else len(results)
        }
    
    def _get_input_data(self, node, context) -> Any:
        """Ottiene i dati di input dai nodi predecessori."""
        for conn in context.workflow.connections:
            if conn.to_node_id == node.node_id:
                return context.get_node_result(conn.from_node_id)
        return {}
    
    async def _execute_single_request(self, url: str, config: Dict, input_data: Any) -> Any:
        """Esegue una singola richiesta API."""
        method = config.get("method", "GET").upper()
        headers = config.get("headers", {})
        
        async with aiohttp.ClientSession() as session:
            timeout = aiohttp.ClientTimeout(total=config.get("timeout", 30))
            
            if method == "GET":
                params = input_data if isinstance(input_data, dict) else {}
                async with session.get(url, params=params, headers=headers, timeout=timeout) as response:
                    return await response.json()
            
            elif method == "POST":
                body = input_data if isinstance(input_data, dict) else {"data": input_data}
                async with session.post(url, json=body, headers=headers, timeout=timeout) as response:
                    return await response.json()
            
            else:
                raise ValueError(f"Metodo HTTP non supportato: {method}")
    
    async def _execute_paginated_request(self, url: str, config: Dict, input_data: Any) -> List[Any]:
        """Esegue richieste API con paginazione."""
        pagination_config = config.get("pagination", {})
        page_param = pagination_config.get("page_param", "page")
        size_param = pagination_config.get("size_param", "size")
        page_size = pagination_config.get("page_size", 10)
        max_pages = pagination_config.get("max_pages", 10)
        
        results = []
        page = 1
        
        while page <= max_pages:
            params = {page_param: page, size_param: page_size}
            if isinstance(input_data, dict):
                params.update(input_data)
            
            try:
                page_results = await self._execute_single_request(url, config, params)
                
                if isinstance(page_results, list):
                    results.extend(page_results)
                    if len(page_results) < page_size:
                        break  # Ultima pagina
                elif isinstance(page_results, dict):
                    # Gestione formato paginazione standard
                    items = page_results.get("items", page_results.get("data", []))
                    results.extend(items)
                    
                    # Controlla se ci sono altre pagine
                    if not page_results.get("has_next", True):
                        break
                
                page += 1
                
            except Exception as e:
                logger.error(f"Errore pagina {page}: {str(e)}")
                break
        
        return results
    
    def _transform_response(self, data: Any, config: Dict) -> Any:
        """Trasforma la risposta API."""
        transform_config = config.get("transform_response", {})
        transform_type = transform_config.get("type", "extract")
        
        if transform_type == "extract":
            # Estrai campi specifici
            fields = transform_config.get("fields", [])
            if isinstance(data, list):
                return [
                    {field: item.get(field) for field in fields if field in item}
                    for item in data if isinstance(item, dict)
                ]
            elif isinstance(data, dict):
                return {field: data.get(field) for field in fields if field in data}
        
        elif transform_type == "map":
            # Applica mapping campi
            field_mapping = transform_config.get("field_mapping", {})
            if isinstance(data, list):
                return [
                    {new_field: item.get(old_field) for old_field, new_field in field_mapping.items()}
                    for item in data if isinstance(item, dict)
                ]
            elif isinstance(data, dict):
                return {new_field: data.get(old_field) for old_field, new_field in field_mapping.items()}
        
        return data

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida la configurazione del nodo API Call."""
        if not config.get("base_url"):
            return False
        
        method = config.get("method", "GET").upper()
        if method not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            return False
        
        # Valida configurazione paginazione se presente
        if "pagination" in config:
            pagination = config["pagination"]
            if not isinstance(pagination, dict):
                return False
            if pagination.get("enabled", False):
                if not isinstance(pagination.get("page_size", 10), int):
                    return False
                if not isinstance(pagination.get("max_pages", 10), int):
                    return False
        
        return True
