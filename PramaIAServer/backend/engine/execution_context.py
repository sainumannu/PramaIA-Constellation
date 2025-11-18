"""
Execution Context

Mantiene lo stato durante l'esecuzione di un workflow,
inclusi i risultati dei nodi e i dati condivisi.
"""

from typing import Dict, Any, Optional
from datetime import datetime


class ExecutionContext:
    """
    Contesto di esecuzione per un workflow.
    
    Mantiene:
    - Risultati dei nodi eseguiti
    - Dati di input originali
    - Stato dell'esecuzione
    - Metadati e logging
    """
    
    def __init__(self, workflow, input_data: Dict[str, Any], execution_id: str):
        self.workflow = workflow
        self.input_data = input_data
        self.execution_id = execution_id
        self.node_results: Dict[str, Any] = {}
        self.node_errors: Dict[str, str] = {}
        self.started_at = datetime.utcnow()
        self.shared_data: Dict[str, Any] = {}
        
    def set_node_result(self, node_id: str, result: Any):
        """Salva il risultato di un nodo."""
        self.node_results[node_id] = result
        
    def get_node_result(self, node_id: str) -> Any:
        """Ottieni il risultato di un nodo."""
        return self.node_results.get(node_id)
        
    def set_node_error(self, node_id: str, error: str):
        """Salva un errore di un nodo."""
        self.node_errors[node_id] = error
        
    def get_node_error(self, node_id: str) -> Optional[str]:
        """Ottieni l'errore di un nodo."""
        return self.node_errors.get(node_id)
        
    def set_shared_data(self, key: str, value: Any):
        """Imposta dati condivisi tra nodi."""
        self.shared_data[key] = value
        
    def get_shared_data(self, key: str, default=None) -> Any:
        """Ottieni dati condivisi tra nodi."""
        return self.shared_data.get(key, default)
        
    def get_input_for_node(self, node_id: str) -> Dict[str, Any]:
        """
        Ottieni i dati di input per un nodo specifico.
        
        Combina:
        - Dati di input originali
        - Risultati dei nodi predecessori
        - Dati condivisi
        """
        from backend.utils import get_logger
        logger = get_logger()
        
        # Inizia con i dati di input originali
        input_data = self.input_data.copy()
        
        print(f"\n{'='*80}")
        print(f"🔍 DEBUG get_input_for_node per '{node_id}'")
        print(f"{'='*80}")
        print(f"   Input originali: {list(input_data.keys())}")
        print(f"   Tipo workflow.connections: {type(self.workflow.connections)}")
        print(f"   Connessioni workflow totali: {len(self.workflow.connections)}")
        
        logger.info(f"🔍 DEBUG get_input_for_node per '{node_id}':")
        logger.info(f"   Input originali: {list(input_data.keys())}")
        logger.info(f"   Connessioni workflow totali: {len(self.workflow.connections)}")
        
        # Aggiungi risultati dei nodi predecessori
        incoming_connections = 0
        for idx, conn in enumerate(self.workflow.connections):
            print(f"\n   [{idx+1}] Connessione:")
            print(f"       from_node_id: {conn.from_node_id} (type: {type(conn.from_node_id)})")
            print(f"       to_node_id:   {conn.to_node_id} (type: {type(conn.to_node_id)})")
            print(f"       Match con '{node_id}'? {conn.to_node_id == node_id}")
            
            logger.info(f"   Verifico connessione: {conn.from_node_id} → {conn.to_node_id}")
            
            if conn.to_node_id == node_id:
                incoming_connections += 1
                print(f"       ✅ MATCH! Connessione in ingresso #{incoming_connections}")
                print(f"       from_port: {conn.from_port}")
                print(f"       to_port: {conn.to_port}")
                
                logger.info(f"   ✅ Match! Connessione in ingresso #{incoming_connections}")
                logger.info(f"      from_node_id: {conn.from_node_id}")
                logger.info(f"      from_port: {conn.from_port}")
                logger.info(f"      to_port: {conn.to_port}")
                
                predecessor_result = self.get_node_result(conn.from_node_id)
                print(f"       Risultato predecessore type: {type(predecessor_result)}")
                if isinstance(predecessor_result, dict):
                    print(f"       Risultato predecessore keys: {list(predecessor_result.keys())}")
                
                logger.info(f"      Risultato predecessore: {type(predecessor_result)} - {list(predecessor_result.keys()) if isinstance(predecessor_result, dict) else 'N/A'}")
                
                if predecessor_result is not None:
                    # Prendi il valore SPECIFICO dalla porta di output
                    if conn.from_port and isinstance(predecessor_result, dict):
                        value = predecessor_result.get(conn.from_port)
                        print(f"       Estratto valore da porta '{conn.from_port}': {type(value)}")
                        if isinstance(value, str):
                            print(f"       Lunghezza: {len(value)} chars")
                        logger.info(f"      Estratto valore da porta '{conn.from_port}': {type(value)} - {len(value) if isinstance(value, str) else 'N/A'}")
                    else:
                        # Se non c'è porta specifica o il risultato non è un dict, usa tutto
                        value = predecessor_result
                        print(f"       Uso tutto il risultato: {type(value)}")
                        logger.info(f"      Uso tutto il risultato: {type(value)}")
                    
                    # Mappa al nome della porta di input
                    port_name = conn.to_port if conn.to_port else f"input_from_{conn.from_node_id}"
                    input_data[port_name] = value
                    print(f"       ✅ Mappato a input_data['{port_name}']")
                    logger.info(f"      ✅ Mappato a '{port_name}'")
                else:
                    print(f"       ⚠️ Risultato predecessore è None!")
                    logger.warning(f"      ⚠️ Risultato predecessore è None!")
        
        print(f"\n   📊 Totale connessioni in ingresso: {incoming_connections}")
        print(f"   📦 Input finale keys: {list(input_data.keys())}")
        print(f"{'='*80}\n")
        
        logger.info(f"   📊 Totale connessioni in ingresso: {incoming_connections}")
        logger.info(f"   📦 Input finale keys: {list(input_data.keys())}")
        
        # Aggiungi dati condivisi
        input_data.update(self.shared_data)
        
        return input_data
        
    def has_errors(self) -> bool:
        """Verifica se ci sono stati errori nell'esecuzione."""
        return bool(self.node_errors)
        
    def get_execution_summary(self) -> Dict[str, Any]:
        """Ottieni un riepilogo dell'esecuzione."""
        return {
            "execution_id": self.execution_id,
            "workflow_name": self.workflow.name,
            "started_at": self.started_at.isoformat(),
            "completed_nodes": len(self.node_results),
            "failed_nodes": len(self.node_errors),
            "has_errors": self.has_errors(),
            "node_results": self.node_results,
            "node_errors": self.node_errors
        }
