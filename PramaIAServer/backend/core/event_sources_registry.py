"""
Event Sources Registry per PramaIA
Sistema per la registrazione dinamica di sorgenti di eventi che possono triggere workflow
"""
import json
import os
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class EventSourceRegistry:
    """Registry per la gestione dinamica delle sorgenti di eventi"""
    
    def __init__(self, sources_directory: str = None):
        self.sources: Dict[str, dict] = {}
        # Nota: PramaIA-EventSources è stata rimossa ma manteniamo il riferimento per retrocompatibilità
        self.sources_directory = sources_directory or "PramaIA-EventSources"
        self.pdk_sources_directory = "PramaIA-PDK/event-sources"
        self._load_built_in_sources()
        self._discover_external_sources()
    
    def _load_built_in_sources(self):
        """Carica le sorgenti built-in del sistema"""
        built_in_sources = [
            {
                "id": "system",
                "name": "Sistema",
                "description": "Eventi interni del sistema PramaIA",
                "version": "1.0.0",
                "type": "built-in",
                "eventTypes": [
                    {
                        "type": "user_login",
                        "label": "Login Utente",
                        "description": "Quando un utente effettua il login",
                        "schema": {
                            "properties": {
                                "userId": {"type": "string"},
                                "timestamp": {"type": "string", "format": "datetime"},
                                "ipAddress": {"type": "string"}
                            }
                        }
                    },
                    {
                        "type": "workflow_completed",
                        "label": "Workflow Completato",
                        "description": "Quando un workflow termina l'esecuzione",
                        "schema": {
                            "properties": {
                                "workflowId": {"type": "string"},
                                "status": {"type": "string", "enum": ["success", "error"]},
                                "duration": {"type": "number"},
                                "timestamp": {"type": "string", "format": "datetime"}
                            }
                        }
                    }
                ],
                "configSchema": {
                    "type": "object",
                    "properties": {
                        "logLevel": {
                            "type": "string",
                            "enum": ["debug", "info", "warning", "error"],
                            "default": "info",
                            "title": "Livello di log"
                        }
                    }
                },
                "webhookEndpoint": "/api/events/system",
                "status": "active"
            },
            {
                "id": "api-webhook",
                "name": "API Webhook",
                "description": "Endpoint HTTP per ricevere eventi esterni",
                "version": "1.0.0",
                "type": "built-in",
                "eventTypes": [
                    {
                        "type": "webhook_received",
                        "label": "Webhook Ricevuto",
                        "description": "Quando viene ricevuta una chiamata webhook",
                        "schema": {
                            "properties": {
                                "payload": {"type": "object"},
                                "headers": {"type": "object"},
                                "method": {"type": "string"},
                                "timestamp": {"type": "string", "format": "datetime"}
                            }
                        }
                    }
                ],
                "configSchema": {
                    "type": "object",
                    "properties": {
                        "customEndpoint": {
                            "type": "string",
                            "title": "Endpoint personalizzato",
                            "description": "Percorso personalizzato per il webhook"
                        },
                        "requireAuth": {
                            "type": "boolean",
                            "default": True,
                            "title": "Richiedi autenticazione"
                        },
                        "secretKey": {
                            "type": "string",
                            "title": "Chiave segreta",
                            "description": "Chiave per validare le richieste"
                        }
                    }
                },
                "webhookEndpoint": "/api/events/webhook",
                "status": "active"
            }
        ]
        
        for source in built_in_sources:
            self.sources[source["id"]] = source
            logger.info(f"Caricata sorgente built-in: {source['name']}")
    
    def _discover_external_sources(self):
        """Scopre e carica sorgenti esterne dalle directory specificate"""
        # Cerca nelle directory tradizionali (vecchio formato)
        # Nota: La cartella PramaIA-EventSources è stata rimossa, questa parte è 
        # mantenuta per retrocompatibilità con eventuali installazioni esistenti
        self._discover_sources_in_directory(self.sources_directory, manifest_name="source.json")
        
        # Cerca nelle directory PDK (nuovo formato integrato)
        self._discover_sources_in_directory(self.pdk_sources_directory, manifest_name="plugin.json")
    
    def _discover_sources_in_directory(self, directory_path: str, manifest_name: str = "source.json"):
        """Cerca sorgenti in una directory specifica"""
        sources_path = Path(directory_path)
        if not sources_path.exists():
            logger.info(f"Directory sorgenti {directory_path} non trovata")
            return
        
        for source_dir in sources_path.iterdir():
            if source_dir.is_dir():
                manifest_path = source_dir / manifest_name
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            source_config = json.load(f)
                        
                        # Adattamento per formato plugin.json del PDK
                        if manifest_name == "plugin.json":
                            # Verifica che sia effettivamente un event-source
                            if source_config.get("type") != "event-source":
                                continue
                                
                            # Estrai ID dal nome se non presente
                            if "id" not in source_config:
                                source_config["id"] = source_config.get("name", "").replace(" ", "-").lower()
                            
                            # Se ci sono eventTypes ma con formato diverso, adatta
                            if "eventTypes" in source_config:
                                for event_type in source_config["eventTypes"]:
                                    # Converte "id" a "type" se necessario
                                    if "id" in event_type and "type" not in event_type:
                                        event_type["type"] = event_type["id"]
                                    
                                    # Converte "name" a "label" se necessario
                                    if "name" in event_type and "label" not in event_type:
                                        event_type["label"] = event_type["name"]
                        
                        # Validazione base del manifest
                        if self._validate_source_config(source_config):
                            source_config["type"] = "external"
                            source_config["path"] = str(source_dir)
                            self.sources[source_config["id"]] = source_config
                            logger.info(f"Caricata sorgente esterna: {source_config.get('name', source_config['id'])} da {directory_path}")
                        else:
                            logger.warning(f"Manifest non valido per {source_dir.name} in {directory_path}")
                    
                    except Exception as e:
                        logger.error(f"Errore nel caricamento di {source_dir.name} da {directory_path}: {e}")
    
    def _validate_source_config(self, config: dict) -> bool:
        """Valida la configurazione di una sorgente"""
        # Campi obbligatori
        required_fields = ["name", "description", "version", "eventTypes"]
        
        # Verifica che l'ID esista o possa essere derivato
        if "id" not in config:
            if "name" in config:
                # Creeremo l'ID dal nome
                pass
            else:
                logger.error("Campo obbligatorio mancante: id o name")
                return False
        
        # Verifica i campi richiesti
        for field in required_fields:
            if field not in config:
                logger.error(f"Campo obbligatorio mancante: {field}")
                return False
        
        # Valida eventTypes
        if not isinstance(config["eventTypes"], list) or len(config["eventTypes"]) == 0:
            logger.error("eventTypes deve essere una lista non vuota")
            return False
        
        # Verifica che ogni event type abbia le info necessarie (supportando entrambi i formati)
        for event_type in config["eventTypes"]:
            type_name = event_type.get("type") or event_type.get("id")
            label = event_type.get("label") or event_type.get("name")
            description = event_type.get("description")
            
            if not type_name or not label or not description:
                logger.error(f"Tipo di evento non valido: {event_type}")
                return False
        
        return True
    
    def register_source(self, source_config: dict) -> bool:
        """Registra una nuova sorgente di eventi"""
        if not self._validate_source_config(source_config):
            return False
        
        self.sources[source_config["id"]] = source_config
        logger.info(f"Registrata sorgente: {source_config['name']}")
        return True
    
    def get_available_sources(self) -> List[dict]:
        """Ritorna tutte le sorgenti disponibili"""
        return list(self.sources.values())
    
    def get_source(self, source_id: str) -> Optional[dict]:
        """Ritorna una sorgente specifica"""
        return self.sources.get(source_id)
    
    def get_event_types_for_source(self, source_id: str) -> List[dict]:
        """Ritorna i tipi di eventi per una sorgente specifica"""
        source = self.sources.get(source_id)
        return source["eventTypes"] if source else []
    
    def get_all_event_types(self) -> List[dict]:
        """Ritorna tutti i tipi di eventi disponibili con la sorgente di origine"""
        all_events = []
        for source_id, source in self.sources.items():
            for event_type in source["eventTypes"]:
                event_with_source = {
                    **event_type,
                    "sourceId": source_id,
                    "sourceName": source["name"]
                }
                all_events.append(event_with_source)
        return all_events
    
    def unregister_source(self, source_id: str) -> bool:
        """Rimuove una sorgente dal registry"""
        if source_id in self.sources:
            removed_source = self.sources.pop(source_id)
            logger.info(f"Rimossa sorgente: {removed_source['name']}")
            return True
        return False

# Istanza globale del registry
event_source_registry = EventSourceRegistry()
