"""
Workflow Validator

Valida la struttura e la compatibilità dei dati tra nodi in un workflow.
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

from backend.engine.data_types import DataType, DataCompatibilityChecker, DataTypeRegistry
from backend.engine.node_schemas import NodeSchemaRegistry
from backend.db.workflow_models import Workflow as WorkflowModel
from backend.utils import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationError:
    """Rappresenta un errore di validazione."""
    node_id: str
    node_name: str
    error_type: str
    message: str
    severity: str = "error"  # error, warning, info


@dataclass
class ValidationResult:
    """Risultato della validazione di un workflow."""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0
    
    def get_summary(self) -> str:
        """Ottieni un riassunto della validazione."""
        if self.is_valid:
            summary = "✅ Workflow valido"
            if self.has_warnings():
                summary += f" (con {len(self.warnings)} avvertimenti)"
        else:
            summary = f"❌ Workflow non valido: {len(self.errors)} errori"
            if self.has_warnings():
                summary += f", {len(self.warnings)} avvertimenti"
        return summary


class WorkflowValidator:
    """
    Validatore per workflow.
    
    Verifica:
    - Struttura del workflow (nodi e connessioni)
    - Compatibilità tra tipi di dati
    - Configurazioni dei nodi
    - Cicli nel grafo
    - Nodi isolati
    """
    
    def __init__(self):
        self.schema_registry = NodeSchemaRegistry()
        self.compatibility_checker = DataCompatibilityChecker()
    
    def validate_workflow(self, workflow: WorkflowModel) -> ValidationResult:
        """
        Valida un workflow completo.
        
        Args:
            workflow: Il workflow da validare
            
        Returns:
            ValidationResult con errori e avvertimenti
        """
        errors = []
        warnings = []
        
        logger.info(
            "Inizio validazione workflow",
            details={"workflow_name": workflow.name}
        )
        
        # Parse dei dati del workflow - convertire ORM in dict
        try:
            # Converti WorkflowNode ORM objects in dict per compatibilità
            nodes = [
                {
                    "id": node.node_id,
                    "name": node.name,
                    "type": node.node_type,
                    "config": node.config if hasattr(node, 'config') else {}
                }
                for node in (workflow.nodes or [])
            ]
            
            # Converti WorkflowConnection ORM objects in dict
            connections = [
                {
                    "from_node_id": conn.from_node_id,
                    "to_node_id": conn.to_node_id,
                    "from_port": conn.from_port if hasattr(conn, 'from_port') else "",
                    "to_port": conn.to_port if hasattr(conn, 'to_port') else ""
                }
                for conn in (workflow.connections or [])
            ]
        except Exception as e:
            errors.append(ValidationError(
                node_id="",
                node_name="",
                error_type="parsing",
                message=f"Errore nel parsing del workflow: {str(e)}"
            ))
            return ValidationResult(False, errors, warnings)
        
        # Validazione strutturale
        struct_errors, struct_warnings = self._validate_structure(nodes, connections)
        errors.extend(struct_errors)
        warnings.extend(struct_warnings)
        
        # Validazione nodi
        node_errors, node_warnings = self._validate_nodes(nodes)
        errors.extend(node_errors)
        warnings.extend(node_warnings)
        
        # Validazione connessioni e compatibilità tipi
        conn_errors, conn_warnings = self._validate_connections(nodes, connections)
        errors.extend(conn_errors)
        warnings.extend(conn_warnings)
        
        # Validazione configurazioni
        config_errors, config_warnings = self._validate_configurations(nodes)
        errors.extend(config_errors)
        warnings.extend(config_warnings)
        
        is_valid = len(errors) == 0
        
        logger.info(
            "Validazione workflow completata",
            details={
                "workflow_name": workflow.name,
                "errors_count": len(errors),
                "warnings_count": len(warnings)
            }
        )
        
        return ValidationResult(is_valid, errors, warnings)
    
    def _validate_structure(self, nodes: List[Dict], connections: List[Dict]) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Valida la struttura base del workflow."""
        errors = []
        warnings = []
        
        # Verifica che ci siano nodi
        if not nodes:
            errors.append(ValidationError(
                node_id="",
                node_name="",
                error_type="structure",
                message="Il workflow deve contenere almeno un nodo"
            ))
            return errors, warnings
        
        # Verifica nodi duplicati
        node_ids = [node.get("id", "") for node in nodes]
        duplicate_ids = [nid for nid in node_ids if node_ids.count(nid) > 1]
        if duplicate_ids:
            errors.append(ValidationError(
                node_id=duplicate_ids[0],
                node_name="",
                error_type="structure",
                message=f"ID nodo duplicato: {duplicate_ids[0]}"
            ))
        
        # Verifica connessioni a nodi inesistenti
        for conn in connections:
            from_id = conn.get("from_node_id", "")
            to_id = conn.get("to_node_id", "")
            
            if from_id not in node_ids:
                errors.append(ValidationError(
                    node_id=from_id,
                    node_name="",
                    error_type="connection",
                    message=f"Connessione da nodo inesistente: {from_id}"
                ))
            
            if to_id not in node_ids:
                errors.append(ValidationError(
                    node_id=to_id,
                    node_name="",
                    error_type="connection",
                    message=f"Connessione a nodo inesistente: {to_id}"
                ))
        
        # Verifica cicli nel grafo
        cycles = self._detect_cycles(nodes, connections)
        if cycles:
            warnings.append(ValidationError(
                node_id="",
                node_name="",
                error_type="structure",
                message=f"Rilevati cicli nel workflow: {cycles}",
                severity="warning"
            ))
        
        # Verifica nodi isolati
        isolated_nodes = self._find_isolated_nodes(nodes, connections)
        for node_id in isolated_nodes:
            node = next((n for n in nodes if n.get("id") == node_id), {})
            warnings.append(ValidationError(
                node_id=node_id,
                node_name=node.get("name", ""),
                error_type="structure",
                message="Nodo isolato (non connesso)",
                severity="warning"
            ))
        
        return errors, warnings
    
    def _validate_nodes(self, nodes: List[Dict]) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Valida i singoli nodi."""
        errors = []
        warnings = []
        
        for node in nodes:
            node_id = node.get("id", "")
            node_name = node.get("name", "")
            node_type = node.get("type", "")
            
            # Verifica che il tipo di nodo sia supportato
            if not node_type:
                errors.append(ValidationError(
                    node_id=node_id,
                    node_name=node_name,
                    error_type="node_type",
                    message="Tipo di nodo non specificato"
                ))
                continue
            
            schema = self.schema_registry.get_schema(node_type)
            if not schema:
                errors.append(ValidationError(
                    node_id=node_id,
                    node_name=node_name,
                    error_type="node_type",
                    message=f"Tipo di nodo non supportato: {node_type}"
                ))
                continue
            
            # Verifica dati richiesti del nodo
            if not node_name.strip():
                warnings.append(ValidationError(
                    node_id=node_id,
                    node_name=node_name,
                    error_type="node_data",
                    message="Nome del nodo vuoto",
                    severity="warning"
                ))
        
        return errors, warnings
    
    def _validate_connections(self, nodes: List[Dict], connections: List[Dict]) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Valida le connessioni e la compatibilità dei tipi."""
        errors = []
        warnings = []
        
        # Crea una mappa per accesso rapido ai nodi
        node_map = {node.get("id"): node for node in nodes}
        
        for conn in connections:
            from_node_id = conn.get("from_node_id", "")
            to_node_id = conn.get("to_node_id", "")
            from_port = conn.get("from_port", "")
            to_port = conn.get("to_port", "")
            
            from_node = node_map.get(from_node_id)
            to_node = node_map.get(to_node_id)
            
            if not from_node or not to_node:
                continue  # Già gestito in validate_structure
            
            # Ottieni schemi dei nodi
            from_schema = self.schema_registry.get_schema(from_node.get("type", ""))
            to_schema = self.schema_registry.get_schema(to_node.get("type", ""))
            
            if not from_schema or not to_schema:
                continue  # Già gestito in validate_nodes
            
            # Trova le porte di output del nodo sorgente
            output_ports = from_schema.get("output_ports", [])
            if from_port:
                output_port = next((p for p in output_ports if p.name == from_port), None)
                if not output_port:
                    errors.append(ValidationError(
                        node_id=from_node_id,
                        node_name=from_node.get("name", ""),
                        error_type="connection",
                        message=f"Porta di output non esistente: {from_port}"
                    ))
                    continue
            else:
                # Se non specificata, usa la prima porta di output
                if output_ports:
                    output_port = output_ports[0]
                else:
                    errors.append(ValidationError(
                        node_id=from_node_id,
                        node_name=from_node.get("name", ""),
                        error_type="connection",
                        message="Nodo senza porte di output"
                    ))
                    continue
            
            # Trova le porte di input del nodo destinazione
            input_ports = to_schema.get("input_ports", [])
            if to_port:
                input_port = next((p for p in input_ports if p.name == to_port), None)
                if not input_port:
                    errors.append(ValidationError(
                        node_id=to_node_id,
                        node_name=to_node.get("name", ""),
                        error_type="connection",
                        message=f"Porta di input non esistente: {to_port}"
                    ))
                    continue
            else:
                # Se non specificata, usa la prima porta di input
                if input_ports:
                    input_port = input_ports[0]
                else:
                    # Alcuni nodi (come input) potrebbero non avere porte di input
                    warnings.append(ValidationError(
                        node_id=to_node_id,
                        node_name=to_node.get("name", ""),
                        error_type="connection",
                        message="Connessione a nodo senza porte di input",
                        severity="warning"
                    ))
                    continue
            
            # Verifica compatibilità tipi
            output_type = output_port.schema.data_type
            input_type = input_port.schema.data_type
            
            if not self.compatibility_checker.are_compatible(output_type, input_type):
                errors.append(ValidationError(
                    node_id=to_node_id,
                    node_name=to_node.get("name", ""),
                    error_type="type_mismatch",
                    message=f"Tipi incompatibili: {output_type.value} -> {input_type.value}"
                ))
            elif output_type != input_type:
                # Compatibili ma diversi - avvertimento per conversione
                warning_msg = self.compatibility_checker.get_conversion_warning(output_type, input_type)
                if warning_msg:
                    warnings.append(ValidationError(
                        node_id=to_node_id,
                        node_name=to_node.get("name", ""),
                        error_type="type_conversion",
                        message=warning_msg,
                        severity="warning"
                    ))
        
        return errors, warnings
    
    def _validate_configurations(self, nodes: List[Dict]) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Valida le configurazioni dei nodi."""
        errors = []
        warnings = []
        
        for node in nodes:
            node_id = node.get("id", "")
            node_name = node.get("name", "")
            node_type = node.get("type", "")
            config = node.get("config", {})
            
            # Ottieni schema di configurazione (se disponibile)
            try:
                config_schema = self.schema_registry.get_config_schema(node_type)
            except AttributeError:
                # Metodo non ancora implementato, skip validazione config
                logger.debug(
                    "get_config_schema non disponibile",
                    details={"node_type": node_type}
                )
                continue
                
            if not config_schema:
                continue
            
            # Verifica configurazioni richieste
            for key, schema_def in config_schema.items():
                if schema_def.get("required", False) and key not in config:
                    errors.append(ValidationError(
                        node_id=node_id,
                        node_name=node_name,
                        error_type="config",
                        message=f"Configurazione richiesta mancante: {key}"
                    ))
            
            # Verifica tipi delle configurazioni
            for key, value in config.items():
                if key in config_schema:
                    expected_type = config_schema[key].get("type")
                    if expected_type and not self._validate_config_type(value, expected_type):
                        errors.append(ValidationError(
                            node_id=node_id,
                            node_name=node_name,
                            error_type="config",
                            message=f"Tipo configurazione non valido per {key}: atteso {expected_type}"
                        ))
        
        return errors, warnings
    
    def _validate_config_type(self, value: Any, expected_type: str) -> bool:
        """Valida il tipo di una configurazione."""
        type_mapping = {
            "string": str,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True  # Tipo non riconosciuto, assume valido
    
    def _detect_cycles(self, nodes: List[Dict], connections: List[Dict]) -> List[str]:
        """Rileva cicli nel grafo del workflow."""
        # Crea grafo di adiacenza
        graph = {node.get("id"): [] for node in nodes}
        for conn in connections:
            from_id = conn.get("from_node_id", "")
            to_id = conn.get("to_node_id", "")
            if from_id in graph:
                graph[from_id].append(to_id)
        
        # DFS per rilevare cicli
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node_id, path):
            if node_id in rec_stack:
                # Trovato ciclo
                cycle_start = path.index(node_id)
                cycle = path[cycle_start:] + [node_id]
                cycles.append(" -> ".join(cycle))
                return
            
            if node_id in visited:
                return
            
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in graph.get(node_id, []):
                dfs(neighbor, path + [node_id])
            
            rec_stack.remove(node_id)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def _find_isolated_nodes(self, nodes: List[Dict], connections: List[Dict]) -> List[str]:
        """Trova nodi isolati (senza connessioni)."""
        connected_nodes = set()
        
        for conn in connections:
            connected_nodes.add(conn.get("from_node_id", ""))
            connected_nodes.add(conn.get("to_node_id", ""))
        
        isolated = []
        for node in nodes:
            node_id = node.get("id", "")
            if node_id not in connected_nodes:
                isolated.append(node_id)
        
        return isolated


class DataFlowValidator:
    """Validatore specifico per il flusso di dati nel workflow."""
    
    def __init__(self):
        self.type_registry = DataTypeRegistry()
        self.compatibility_checker = DataCompatibilityChecker()
    
    def validate_data_flow(self, workflow_data: Dict, input_data: Dict[str, Any]) -> ValidationResult:
        """
        Valida che i dati di input possano fluire attraverso il workflow.
        
        Args:
            workflow_data: Dati del workflow (nodi e connessioni)
            input_data: Dati di input del workflow
            
        Returns:
            ValidationResult con eventuali problemi nel flusso dati
        """
        errors = []
        warnings = []
        
        # Simula l'esecuzione per verificare il flusso dati
        nodes = workflow_data.get("nodes", [])
        connections = workflow_data.get("connections", [])
        
        # Crea mappa dei nodi
        node_map = {node.get("id"): node for node in nodes}
        
        # Simula i dati che fluiscono attraverso il workflow
        node_outputs = {}
        
        # Ordina i nodi topologicamente
        sorted_nodes = self._topological_sort(nodes, connections)
        
        for node_id in sorted_nodes:
            node = node_map.get(node_id)
            if not node:
                continue
            
            node_type = node.get("type", "")
            schema = NodeSchemaRegistry.get_schema(node_type)
            
            if not schema:
                continue
            
            # Verifica input del nodo
            input_ports = schema.get("input_ports", [])
            for input_port in input_ports:
                # Trova le connessioni verso questa porta
                input_connections = [
                    conn for conn in connections
                    if conn.get("to_node_id") == node_id and 
                       (not conn.get("to_port") or conn.get("to_port") == input_port.name)
                ]
                
                if input_port.schema.required and not input_connections:
                    # Verifica se c'è un input diretto dal workflow
                    if input_port.name not in input_data:
                        errors.append(ValidationError(
                            node_id=node_id,
                            node_name=node.get("name", ""),
                            error_type="missing_input",
                            message=f"Input richiesto mancante: {input_port.display_name}"
                        ))
            
            # Simula output del nodo
            output_ports = schema.get("output_ports", [])
            for output_port in output_ports:
                # Per la simulazione, usa un valore dummy del tipo corretto
                node_outputs[f"{node_id}.{output_port.name}"] = output_port.schema.data_type
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def _topological_sort(self, nodes: List[Dict], connections: List[Dict]) -> List[str]:
        """Ordina i nodi topologicamente per simulare l'esecuzione."""
        from collections import defaultdict, deque
        
        # Crea grafo di adiacenza
        graph = defaultdict(list)
        in_degree = {node.get("id"): 0 for node in nodes}
        
        for conn in connections:
            from_id = conn.get("from_node_id", "")
            to_id = conn.get("to_node_id", "")
            graph[from_id].append(to_id)
            in_degree[to_id] += 1
        
        # Algoritmo di Kahn
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            node_id = queue.popleft()
            result.append(node_id)
            
            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
