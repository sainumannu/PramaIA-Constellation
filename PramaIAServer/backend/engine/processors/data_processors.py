"""
Data Processing Node Processors

Processori per operazioni di manipolazione, trasformazione e filtraggio dei dati.
"""

import json
import re
from typing import Dict, Any, List, Optional
from backend.engine.node_registry import BaseNodeProcessor


class DataTransformProcessor(BaseNodeProcessor):
    """
    Processore per trasformazione dei dati.
    Supporta operazioni di mapping, filtraggio, aggregazione.
    """
    
    async def execute(self, node, context) -> Dict[str, Any]:
        """
        Esegue trasformazioni sui dati.
        
        Configurazioni supportate:
        - transform_type: "map", "filter", "aggregate", "extract"
        - field_mapping: mappatura campi per trasformazioni
        - filter_conditions: condizioni per filtraggio
        - aggregation_functions: funzioni di aggregazione
        """
        config = node.configuration or {}
        transform_type = config.get("transform_type", "map")
        
        # Ottieni dati di input dai nodi precedenti
        input_data = self._get_input_data(node, context)
        
        if transform_type == "map":
            result = self._transform_map(input_data, config)
        elif transform_type == "filter":
            result = self._transform_filter(input_data, config)
        elif transform_type == "aggregate":
            result = self._transform_aggregate(input_data, config)
        elif transform_type == "extract":
            result = self._transform_extract(input_data, config)
        else:
            raise ValueError(f"Tipo di trasformazione non supportato: {transform_type}")
        
        return {
            "status": "success",
            "data": result,
            "transform_type": transform_type,
            "processed_count": len(result) if isinstance(result, list) else 1
        }
    
    def _get_input_data(self, node, context) -> Any:
        """Ottiene i dati di input dai nodi predecessori."""
        input_data = []
        
        # Cerca connessioni in ingresso
        for conn in context.workflow.connections:
            if conn.to_node_id == node.node_id:
                predecessor_result = context.get_node_result(conn.from_node_id)
                if predecessor_result:
                    # Estrai i dati dal risultato
                    data = predecessor_result.get("data", predecessor_result)
                    input_data.append(data)
        
        # Se c'è un solo input, restituiscilo direttamente
        if len(input_data) == 1:
            return input_data[0]
        
        return input_data
    
    def _transform_map(self, data: Any, config: Dict) -> Any:
        """Applica trasformazioni di mapping."""
        field_mapping = config.get("field_mapping", {})
        
        if isinstance(data, dict):
            # Trasforma un singolo oggetto
            result = {}
            for old_key, new_key in field_mapping.items():
                if old_key in data:
                    result[new_key] = data[old_key]
            return result
        
        elif isinstance(data, list):
            # Trasforma una lista di oggetti
            return [self._transform_map(item, config) for item in data]
        
        return data
    
    def _transform_filter(self, data: Any, config: Dict) -> Any:
        """Applica filtraggio ai dati."""
        filter_conditions = config.get("filter_conditions", [])
        
        if isinstance(data, list):
            filtered_data = []
            for item in data:
                if self._matches_conditions(item, filter_conditions):
                    filtered_data.append(item)
            return filtered_data
        
        elif isinstance(data, dict):
            if self._matches_conditions(data, filter_conditions):
                return data
            return {}
        
        return data
    
    def _transform_aggregate(self, data: Any, config: Dict) -> Dict[str, Any]:
        """Applica funzioni di aggregazione."""
        if not isinstance(data, list):
            return {"error": "Aggregazione richiede dati di tipo lista"}
        
        aggregation_functions = config.get("aggregation_functions", ["count"])
        result = {}
        
        for func in aggregation_functions:
            if func == "count":
                result["count"] = len(data)
            elif func == "sum" and config.get("sum_field"):
                field = config["sum_field"]
                total = sum(item.get(field, 0) for item in data if isinstance(item, dict))
                result[f"sum_{field}"] = total
            elif func == "avg" and config.get("avg_field"):
                field = config["avg_field"]
                values = [item.get(field, 0) for item in data if isinstance(item, dict)]
                result[f"avg_{field}"] = sum(values) / len(values) if values else 0
        
        return result
    
    def _transform_extract(self, data: Any, config: Dict) -> Any:
        """Estrae campi specifici dai dati."""
        extract_fields = config.get("extract_fields", [])
        
        if isinstance(data, dict):
            result = {}
            for field in extract_fields:
                if field in data:
                    result[field] = data[field]
            return result
        
        elif isinstance(data, list):
            return [self._transform_extract(item, config) for item in data]
        
        return data
    
    def _matches_conditions(self, item: Dict, conditions: List[Dict]) -> bool:
        """Verifica se un elemento soddisfa le condizioni di filtraggio."""
        for condition in conditions:
            field = condition.get("field")
            operator = condition.get("operator", "equals")
            value = condition.get("value")
            
            if field not in item:
                return False
            
            item_value = item[field]
            
            if operator == "equals":
                if item_value != value:
                    return False
            elif operator == "not_equals":
                if item_value == value:
                    return False
            elif operator == "greater_than":
                if item_value <= value:
                    return False
            elif operator == "less_than":
                if item_value >= value:
                    return False
            elif operator == "contains":
                if str(value).lower() not in str(item_value).lower():
                    return False
        
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida la configurazione del nodo."""
        transform_type = config.get("transform_type", "map")
        if transform_type not in ["map", "filter", "aggregate", "extract"]:
            return False
        
        if transform_type == "map" and not config.get("field_mapping"):
            return False
        
        if transform_type == "filter" and not config.get("filter_conditions"):
            return False
        
        if transform_type == "aggregate" and not config.get("aggregation_functions"):
            return False
        
        if transform_type == "extract" and not config.get("extract_fields"):
            return False
        
        return True


class TextProcessor(BaseNodeProcessor):
    """
    Processore per elaborazione di testo.
    Supporta operazioni di parsing, regex, formatting.
    """
    
    async def execute(self, node, context) -> Dict[str, Any]:
        """
        Esegue operazioni di elaborazione testo.
        
        Configurazioni supportate:
        - operation: "extract_regex", "replace", "split", "join", "format"
        - pattern: pattern regex per estrazione
        - replacement: testo sostitutivo
        - separator: separatore per split/join
        - template: template per formatting
        """
        config = node.configuration or {}
        operation = config.get("operation", "extract_regex")
        
        # Ottieni testo di input
        input_data = self._get_input_data(node, context)
        text = str(input_data.get("data", input_data) if isinstance(input_data, dict) else input_data)
        
        if operation == "extract_regex":
            result = self._extract_regex(text, config)
        elif operation == "replace":
            result = self._replace_text(text, config)
        elif operation == "split":
            result = self._split_text(text, config)
        elif operation == "join":
            result = self._join_text(input_data, config)
        elif operation == "format":
            result = self._format_text(text, config)
        else:
            raise ValueError(f"Operazione non supportata: {operation}")
        
        return {
            "status": "success",
            "data": result,
            "operation": operation,
            "original_length": len(text)
        }
    
    def _get_input_data(self, node, context) -> Any:
        """Ottiene i dati di input dai nodi predecessori."""
        for conn in context.workflow.connections:
            if conn.to_node_id == node.node_id:
                return context.get_node_result(conn.from_node_id)
        return ""
    
    def _extract_regex(self, text: str, config: Dict) -> List[str]:
        """Estrae pattern usando regex."""
        pattern = config.get("pattern", r".*")
        flags = re.IGNORECASE if config.get("ignore_case", False) else 0
        
        matches = re.findall(pattern, text, flags=flags)
        return matches
    
    def _replace_text(self, text: str, config: Dict) -> str:
        """Sostituisce testo usando regex o stringa."""
        pattern = config.get("pattern", "")
        replacement = config.get("replacement", "")
        use_regex = config.get("use_regex", False)
        
        if use_regex:
            flags = re.IGNORECASE if config.get("ignore_case", False) else 0
            return re.sub(pattern, replacement, text, flags=flags)
        else:
            return text.replace(pattern, replacement)
    
    def _split_text(self, text: str, config: Dict) -> List[str]:
        """Divide il testo usando un separatore."""
        separator = config.get("separator", " ")
        max_split = config.get("max_split", -1)
        
        if max_split == -1:
            return text.split(separator)
        else:
            return text.split(separator, max_split)
    
    def _join_text(self, data: Any, config: Dict) -> str:
        """Unisce elementi in una stringa."""
        separator = config.get("separator", " ")
        
        if isinstance(data, list):
            return separator.join(str(item) for item in data)
        elif isinstance(data, dict) and "data" in data:
            items = data["data"]
            if isinstance(items, list):
                return separator.join(str(item) for item in items)
        
        return str(data)
    
    def _format_text(self, text: str, config: Dict) -> str:
        """Formatta il testo usando un template."""
        template = config.get("template", "{text}")
        
        return template.format(text=text)
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida la configurazione del nodo."""
        operation = config.get("operation", "extract_regex")
        if operation not in ["extract_regex", "replace", "split", "join", "format"]:
            return False
        
        if operation == "extract_regex" and not config.get("pattern"):
            return False
        
        if operation == "replace" and not config.get("pattern"):
            return False
        
        if operation == "split" and not config.get("separator"):
            return False
        
        if operation == "format" and not config.get("template"):
            return False
        
        return True


class JSONProcessor(BaseNodeProcessor):
    """
    Processore per operazioni JSON.
    Supporta parsing, serializzazione, query JSONPath.
    """
    
    async def execute(self, node, context) -> Dict[str, Any]:
        """
        Esegue operazioni JSON.
        
        Configurazioni supportate:
        - operation: "parse", "stringify", "query", "merge"
        - json_path: path per query (formato JSONPath semplificato)
        - merge_strategy: strategia per merge ("overwrite", "append")
        """
        config = node.configuration or {}
        operation = config.get("operation", "parse")
        
        # Ottieni dati di input
        input_data = self._get_input_data(node, context)
        
        if operation == "parse":
            result = self._parse_json(input_data, config)
        elif operation == "stringify":
            result = self._stringify_json(input_data, config)
        elif operation == "query":
            result = self._query_json(input_data, config)
        elif operation == "merge":
            result = self._merge_json(input_data, config)
        else:
            raise ValueError(f"Operazione JSON non supportata: {operation}")
        
        return {
            "status": "success",
            "data": result,
            "operation": operation
        }
    
    def _get_input_data(self, node, context) -> Any:
        """Ottiene i dati di input dai nodi predecessori."""
        for conn in context.workflow.connections:
            if conn.to_node_id == node.node_id:
                return context.get_node_result(conn.from_node_id)
        return {}
    
    def _parse_json(self, data: Any, config: Dict) -> Any:
        """Parsing JSON da stringa o dict."""
        # Se data è già un dict, ritorna direttamente
        if isinstance(data, dict):
            # Se ha una chiave "data", estrai quella
            return data.get("data", data)
        
        # Se è una stringa, prova a parsarla come JSON
        if isinstance(data, str):
            json_string = data
        elif isinstance(data, dict) and "data" in data:
            json_string = str(data["data"])
        else:
            json_string = str(data)
        
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            raise ValueError(f"Errore parsing JSON: {str(e)}")
    
    def _stringify_json(self, data: Any, config: Dict) -> str:
        """Serializzazione JSON."""
        indent = config.get("indent", None)
        ensure_ascii = config.get("ensure_ascii", True)
        
        if isinstance(data, dict) and "data" in data:
            obj = data["data"]
        else:
            obj = data
        
        return json.dumps(obj, indent=indent, ensure_ascii=ensure_ascii)
    
    def _query_json(self, data: Any, config: Dict) -> Any:
        """Query JSONPath semplificata."""
        json_path = config.get("json_path", "")
        
        if isinstance(data, dict) and "data" in data:
            obj = data["data"]
        else:
            obj = data
        
        # Implementazione JSONPath semplificata
        # Supporta solo path semplici come "field", "field.subfield", "field[0]"
        if not json_path:
            return obj
        
        parts = json_path.split(".")
        current = obj
        
        for part in parts:
            if "[" in part and "]" in part:
                # Gestione array index
                field_name = part.split("[")[0]
                index = int(part.split("[")[1].split("]")[0])
                
                if isinstance(current, dict) and field_name in current:
                    current = current[field_name]
                    if isinstance(current, list) and 0 <= index < len(current):
                        current = current[index]
                    else:
                        return None
                else:
                    return None
            else:
                # Gestione campo normale
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
        
        return current
    
    def _merge_json(self, data: Any, config: Dict) -> Dict[str, Any]:
        """Merge di oggetti JSON."""
        merge_strategy = config.get("merge_strategy", "overwrite")
        
        # Per ora implementiamo un merge semplice
        if isinstance(data, list) and len(data) >= 2:
            result = {}
            for item in data:
                if isinstance(item, dict):
                    if merge_strategy == "overwrite":
                        result.update(item)
                    elif merge_strategy == "append":
                        for key, value in item.items():
                            if key in result:
                                if isinstance(result[key], list):
                                    result[key].append(value)
                                else:
                                    result[key] = [result[key], value]
                            else:
                                result[key] = value
            return result
        
        return data
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida la configurazione del nodo."""
        operation = config.get("operation", "parse")
        if operation not in ["parse", "stringify", "query", "merge"]:
            return False
        
        if operation == "query" and not config.get("json_path"):
            return False
        
        if operation == "merge" and not config.get("merge_strategy"):
            return False
        
        return True
