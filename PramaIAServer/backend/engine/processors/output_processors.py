import json
from typing import Dict, Any
from datetime import datetime

from backend.engine.node_registry import BaseNodeProcessor
from backend.engine.execution_context import ExecutionContext
from backend.utils import get_logger

logger = get_logger()


class TextOutputProcessor(BaseNodeProcessor):
    """
    Processore per nodi di output testuale.
    
    Formatta e restituisce il testo finale per l'utente.
    """
    async def execute(self, node, context: ExecutionContext) -> str:
        """
        Esegue il nodo di output testuale.
        
        Formatta il testo secondo la configurazione del nodo.
        """
        logger.info("Processando output testuale", details={"node_name": node.name, "node_id": node.node_id})
        
        # Ottieni i dati di input per questo nodo
        input_data = context.get_input_for_node(node.node_id)
        
        # Estrai il contenuto principale
        content = self._extract_content(input_data)
        
        if not content:
            raise ValueError(f"Nessun contenuto da outputtare nel nodo '{node.name}'")
        
        # Applica formattazione dalla configurazione
        config = node.config or {}
        formatted_content = await self._format_content(content, config, context)
        
        logger.info("Output testuale generato", details={"node_name": node.name, "length": len(formatted_content)})
        
        return formatted_content
    
    def _extract_content(self, input_data: Dict[str, Any]) -> str:
        """Estrae il contenuto da outputtare dai dati di input."""
        # Ordine di priorità per il contenuto
        priority_keys = ["output", "result", "response", "text", "content", "input"]
        
        for key in priority_keys:
            if key in input_data and input_data[key]:
                return str(input_data[key])
        
        # Se non trovato, concatena tutti i valori stringa
        content_parts = []
        for value in input_data.values():
            if isinstance(value, str) and value.strip():
                content_parts.append(value)
        
        return "\n\n".join(content_parts) if content_parts else ""
    
    async def _format_content(self, content: str, config: Dict[str, Any], context: ExecutionContext) -> str:
        """Applica formattazione al contenuto."""
        # Template di output se configurato
        output_template = config.get("template", "{content}")
        
        # Sostituzioni nel template
        formatted = output_template.replace("{content}", content)
        
        # Sostituzioni di metadati
        metadata_replacements = {
            "{timestamp}": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "{execution_id}": context.execution_id,
            "{workflow_name}": context.workflow.name,
        }
        
        for placeholder, value in metadata_replacements.items():
            formatted = formatted.replace(placeholder, value)
        
        # Formattazione del testo
        if config.get("uppercase", False):
            formatted = formatted.upper()
        elif config.get("lowercase", False):
            formatted = formatted.lower()
        
        if config.get("trim", True):
            formatted = formatted.strip()
        
        # Limite di lunghezza se configurato
        max_length = config.get("max_length")
        if max_length and len(formatted) > max_length:
            formatted = formatted[:max_length]
            if config.get("add_ellipsis", True):
                formatted += "..."
        
        return formatted
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida la configurazione del nodo."""
        allowed_keys = {
            "template", "uppercase", "lowercase", "trim", "max_length", "add_ellipsis"
        }
        
        # Verifica che non ci siano chiavi non supportate
        unknown_keys = set(config.keys()) - allowed_keys
        if unknown_keys:
            logger.warning(f"Chiavi di configurazione non riconosciute: {unknown_keys}")
        
        # Valida max_length se presente
        if "max_length" in config:
            max_length = config["max_length"]
            if not isinstance(max_length, int) or max_length <= 0:
                return False
        
        # Valida template se presente
        if "template" in config:
            template = config["template"]
            if not isinstance(template, str):
                return False
        
        return True


class FileOutputProcessor(BaseNodeProcessor):
    """
    Processore per nodi di output file.
    
    Genera file da salvare o scaricare.
    """
    
    async def execute(self, node, context: ExecutionContext) -> Dict[str, Any]:
        """
        Esegue il nodo di output file.
        
        Genera un file con il contenuto specificato.
        """
        logger.info("Processando output file", details={"node_name": node.name, "node_id": node.node_id})
        
        # Ottieni i dati di input per questo nodo
        input_data = context.get_input_for_node(node.node_id)
        
        # Estrai il contenuto
        content = self._extract_content(input_data)
        
        if not content:
            raise ValueError(f"Nessun contenuto per generare file nel nodo '{node.name}'")
        
        # Configurazione file
        config = node.config or {}
        
        # Nome file
        filename = config.get("filename", f"output_{context.execution_id}")
        file_extension = config.get("extension", "txt")
        
        # Se il filename non ha estensione, aggiungila
        if "." not in filename:
            filename = f"{filename}.{file_extension}"
        
        # Tipo di contenuto
        content_type = self._get_content_type(file_extension)
        
        # Formatta il contenuto se necessario
        formatted_content = await self._format_file_content(content, config, context)
        
        result = {
            "filename": filename,
            "content": formatted_content,
            "content_type": content_type,
            "size": len(formatted_content),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info("File generato", details={"node_name": node.name, "filename": filename, "size": result['size']})
        
        return result
    
    def _extract_content(self, input_data: Dict[str, Any]) -> str:
        """Estrae il contenuto del file dai dati di input."""
        # Stesso logic del TextOutputProcessor
        priority_keys = ["output", "result", "response", "text", "content", "input"]
        
        for key in priority_keys:
            if key in input_data and input_data[key]:
                return str(input_data[key])
        
        # Concatena tutti i valori stringa
        content_parts = []
        for value in input_data.values():
            if isinstance(value, str) and value.strip():
                content_parts.append(value)
        
        return "\n\n".join(content_parts) if content_parts else ""
    
    async def _format_file_content(self, content: str, config: Dict[str, Any], context: ExecutionContext) -> str:
        """Formatta il contenuto del file."""
        # Per file JSON
        if config.get("extension") == "json":
            try:
                # Se il contenuto è già JSON valido, lascialo così
                json.loads(content)
                return content
            except json.JSONDecodeError:
                # Altrimenti wrappa in un oggetto JSON
                return json.dumps({
                    "content": content,
                    "generated_at": datetime.utcnow().isoformat(),
                    "execution_id": context.execution_id
                }, indent=2)
        
        # Per file di testo, aggiungi header se configurato
        if config.get("add_header", False):
            header = f"""Generated by PramaIA 2.0
Workflow: {context.workflow.name}
Execution ID: {context.execution_id}
Generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
            content = header + content
        
        return content
    
    def _get_content_type(self, extension: str) -> str:
        """Ottiene il content type per l'estensione file."""
        content_types = {
            "txt": "text/plain",
            "json": "application/json",
            "html": "text/html",
            "csv": "text/csv",
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        return content_types.get(extension.lower(), "text/plain")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida la configurazione del nodo."""
        allowed_keys = {"filename", "extension", "add_header"}
        
        unknown_keys = set(config.keys()) - allowed_keys
        if unknown_keys:
            logger.warning(f"Chiavi di configurazione non riconosciute: {unknown_keys}")
        
        return True


class EmailOutputProcessor(BaseNodeProcessor):
    """
    Processore per nodi di output email.
    
    Invia email con il contenuto specificato.
    """
    
    async def execute(self, node, context: ExecutionContext) -> Dict[str, Any]:
        """
        Esegue il nodo di output email.
        
        Per ora restituisce i dettagli dell'email da inviare.
        L'invio effettivo può essere implementato successivamente.
        """
        logger.info("Processando output email", details={"node_name": node.name, "node_id": node.node_id})
        
        # Ottieni i dati di input per questo nodo
        input_data = context.get_input_for_node(node.node_id)
        
        # Estrai il contenuto
        content = self._extract_content(input_data)
        
        if not content:
            raise ValueError(f"Nessun contenuto per email nel nodo '{node.name}'")
        
        config = node.config or {}
        
        # Configurazione email
        to_email = config.get("to", "test@example.com")
        subject = config.get("subject", f"Output da workflow {context.workflow.name}")
        
        # Sostituzioni nel subject
        subject = subject.replace("{workflow_name}", context.workflow.name)
        subject = subject.replace("{timestamp}", datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
        
        result = {
            "to": to_email,
            "subject": subject,
            "body": content,
            "generated_at": datetime.utcnow().isoformat(),
            "status": "prepared"  # prepared, sent, failed
        }
        
        logger.info("Email preparata", details={"node_name": node.name, "to": to_email, "subject": subject})
        
        # TODO: Implementare invio effettivo email
        # await self._send_email(result)
        
        return result
    
    def _extract_content(self, input_data: Dict[str, Any]) -> str:
        """Estrae il contenuto email dai dati di input."""
        # Stesso logic degli altri output processor
        priority_keys = ["output", "result", "response", "text", "content", "input"]
        
        for key in priority_keys:
            if key in input_data and input_data[key]:
                return str(input_data[key])
        
        return ""
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida la configurazione del nodo."""
        allowed_keys = {"to", "subject", "cc", "bcc"}
        
        # Verifica che non ci siano chiavi non supportate
        unknown_keys = set(config.keys()) - allowed_keys
        if unknown_keys:
            logger.warning(f"Chiavi di configurazione non riconosciute: {unknown_keys}")
        
        # Valida email se presente
        if "to" in config:
            to_email = config["to"]
            if not isinstance(to_email, str) or "@" not in to_email:
                return False
        
        return True