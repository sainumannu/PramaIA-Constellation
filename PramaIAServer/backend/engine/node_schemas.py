"""
Definizioni dei tipi di nodo per il workflow engine di PramaIA.
NOTA: Le definizioni PDF legacy sono state rimosse e migrate al PDK.
"""

from typing import Dict, Any, List, Optional
from enum import Enum


class DataType(Enum):
    """Tipi di dati supportati."""
    STRING = "string"
    NUMBER = "number" 
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    FILE = "file"


class NodeSchemaRegistry:
    """Registry dei nodi (senza i nodi PDF legacy)."""
    
    NODE_SCHEMAS = {
        # PDF NODES REMOVED - Now in PDK plugins
    }

    @classmethod
    def get_schema(cls, node_type: str) -> Optional[Dict[str, Any]]:
        return cls.NODE_SCHEMAS.get(node_type)


def get_node_schema(node_type: str) -> Optional[Dict[str, Any]]:
    return NodeSchemaRegistry.get_schema(node_type)


__all__ = [
    "DataType",
    "NodeSchemaRegistry", 
    "get_node_schema"
]
