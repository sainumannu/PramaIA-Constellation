"""
Data Types System for Workflow Engine

Definisce i tipi di dati supportati tra nodi e le regole di validazione/conversione.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union, Type
from dataclasses import dataclass
import json
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class DataType(Enum):
    """Tipi di dati supportati nel workflow engine."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    FILE = "file"
    JSON = "json"
    ARRAY = "array"
    OBJECT = "object"
    DATE = "date"
    EMAIL = "email"
    URL = "url"
    ANY = "any"  # Accetta qualsiasi tipo


@dataclass
class DataSchema:
    """Schema per la validazione di un tipo di dato."""
    data_type: DataType
    required: bool = True
    description: str = ""
    constraints: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.constraints is None:
            self.constraints = {}


@dataclass
class PortSchema:
    """Schema per una porta di input/output di un nodo."""
    name: str
    schema: DataSchema
    display_name: str = ""
    
    def __post_init__(self):
        if not self.display_name:
            self.display_name = self.name.replace("_", " ").title()


class DataValidator(ABC):
    """Classe base per validatori di tipo di dato."""
    
    @abstractmethod
    def validate(self, value: Any, constraints: Dict[str, Any] = None) -> bool:
        """Valida un valore per questo tipo di dato."""
        pass
    
    @abstractmethod
    def convert(self, value: Any, constraints: Dict[str, Any] = None) -> Any:
        """Converte un valore a questo tipo di dato."""
        pass
    
    def get_error_message(self, value: Any, constraints: Dict[str, Any] = None) -> str:
        """Ottieni messaggio di errore per validazione fallita."""
        return f"Valore non valido per il tipo di dato: {value}"


class StringValidator(DataValidator):
    """Validatore per stringhe."""
    
    def validate(self, value: Any, constraints: Dict[str, Any] = None) -> bool:
        if not isinstance(value, str):
            return False
        
        if constraints:
            min_length = constraints.get("min_length", 0)
            max_length = constraints.get("max_length", float('inf'))
            pattern = constraints.get("pattern")
            
            if len(value) < min_length or len(value) > max_length:
                return False
            
            if pattern:
                import re
                if not re.match(pattern, value):
                    return False
        
        return True
    
    def convert(self, value: Any, constraints: Dict[str, Any] = None) -> str:
        if isinstance(value, str):
            return value
        return str(value)


class NumberValidator(DataValidator):
    """Validatore per numeri."""
    
    def validate(self, value: Any, constraints: Dict[str, Any] = None) -> bool:
        if not isinstance(value, (int, float)):
            try:
                float(value)
            except (ValueError, TypeError):
                return False
        
        if constraints:
            num_value = float(value)
            min_value = constraints.get("min_value", float('-inf'))
            max_value = constraints.get("max_value", float('inf'))
            
            if num_value < min_value or num_value > max_value:
                return False
        
        return True
    
    def convert(self, value: Any, constraints: Dict[str, Any] = None) -> Union[int, float]:
        if isinstance(value, (int, float)):
            return value
        
        if isinstance(value, str):
            try:
                # Prova prima int, poi float
                if '.' not in value:
                    return int(value)
                return float(value)
            except ValueError:
                raise ValueError(f"Cannot convert '{value}' to number")
        
        raise ValueError(f"Cannot convert {type(value)} to number")


class BooleanValidator(DataValidator):
    """Validatore per booleani."""
    
    def validate(self, value: Any, constraints: Dict[str, Any] = None) -> bool:
        if isinstance(value, bool):
            return True
        
        # Accetta anche stringhe che rappresentano booleani
        if isinstance(value, str):
            return value.lower() in ('true', 'false', 'yes', 'no', '1', '0')
        
        if isinstance(value, (int, float)):
            return value in (0, 1)
        
        return False
    
    def convert(self, value: Any, constraints: Dict[str, Any] = None) -> bool:
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', '1')
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        raise ValueError(f"Cannot convert {type(value)} to boolean")


class JsonValidator(DataValidator):
    """Validatore per JSON."""
    
    def validate(self, value: Any, constraints: Dict[str, Any] = None) -> bool:
        if isinstance(value, (dict, list)):
            return True
        
        if isinstance(value, str):
            try:
                json.loads(value)
                return True
            except json.JSONDecodeError:
                return False
        
        return False
    
    def convert(self, value: Any, constraints: Dict[str, Any] = None) -> Union[dict, list]:
        if isinstance(value, (dict, list)):
            return value
        
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON string: {value}")
        
        raise ValueError(f"Cannot convert {type(value)} to JSON")


class ArrayValidator(DataValidator):
    """Validatore per array."""
    
    def validate(self, value: Any, constraints: Dict[str, Any] = None) -> bool:
        if isinstance(value, list):
            if constraints:
                min_length = constraints.get("min_length", 0)
                max_length = constraints.get("max_length", float('inf'))
                item_type = constraints.get("item_type")
                
                if len(value) < min_length or len(value) > max_length:
                    return False
                
                if item_type:
                    item_validator = DataTypeRegistry.get_validator(DataType(item_type))
                    for item in value:
                        if not item_validator.validate(item):
                            return False
            
            return True
        
        # Accetta anche stringhe che rappresentano array JSON
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return isinstance(parsed, list)
            except json.JSONDecodeError:
                return False
        
        return False
    
    def convert(self, value: Any, constraints: Dict[str, Any] = None) -> list:
        if isinstance(value, list):
            return value
        
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            
            # Se non è JSON, tratta come lista di una stringa
            return [value]
        
        # Converte altri tipi in lista
        return [value]


class FileValidator(DataValidator):
    """Validatore per file."""
    
    def validate(self, value: Any, constraints: Dict[str, Any] = None) -> bool:
        # Per ora, accetta path di file come stringa o oggetti file
        if isinstance(value, str):
            # Verifica estensioni se specificate
            if constraints and "allowed_extensions" in constraints:
                import os
                ext = os.path.splitext(value)[1].lower()
                return ext in constraints["allowed_extensions"]
            return True
        
        # Accetta anche oggetti file-like
        if hasattr(value, 'read') or hasattr(value, 'filename'):
            return True
        
        return False
    
    def convert(self, value: Any, constraints: Dict[str, Any] = None) -> Any:
        # Per ora, restituisce il valore così com'è
        return value


class EmailValidator(DataValidator):
    """Validatore per email."""
    
    def validate(self, value: Any, constraints: Dict[str, Any] = None) -> bool:
        if not isinstance(value, str):
            return False
        
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, value) is not None
    
    def convert(self, value: Any, constraints: Dict[str, Any] = None) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        
        raise ValueError(f"Cannot convert {type(value)} to email")


class UrlValidator(DataValidator):
    """Validatore per URL."""
    
    def validate(self, value: Any, constraints: Dict[str, Any] = None) -> bool:
        if not isinstance(value, str):
            return False
        
        import re
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return re.match(url_pattern, value) is not None
    
    def convert(self, value: Any, constraints: Dict[str, Any] = None) -> str:
        if isinstance(value, str):
            return value.strip()
        
        raise ValueError(f"Cannot convert {type(value)} to URL")


class AnyValidator(DataValidator):
    """Validatore che accetta qualsiasi tipo."""
    
    def validate(self, value: Any, constraints: Dict[str, Any] = None) -> bool:
        return True
    
    def convert(self, value: Any, constraints: Dict[str, Any] = None) -> Any:
        return value


class DataTypeRegistry:
    """Registry per i validatori di tipo di dato."""
    
    _validators = {
        DataType.STRING: StringValidator(),
        DataType.NUMBER: NumberValidator(),
        DataType.BOOLEAN: BooleanValidator(),
        DataType.JSON: JsonValidator(),
        DataType.ARRAY: ArrayValidator(),
        DataType.FILE: FileValidator(),
        DataType.EMAIL: EmailValidator(),
        DataType.URL: UrlValidator(),
        DataType.ANY: AnyValidator(),
    }
    
    @classmethod
    def get_validator(cls, data_type: DataType) -> DataValidator:
        """Ottieni il validatore per un tipo di dato."""
        return cls._validators.get(data_type, cls._validators[DataType.ANY])
    
    @classmethod
    def validate_value(cls, value: Any, schema: DataSchema) -> bool:
        """Valida un valore contro uno schema."""
        validator = cls.get_validator(schema.data_type)
        return validator.validate(value, schema.constraints)
    
    @classmethod
    def convert_value(cls, value: Any, schema: DataSchema) -> Any:
        """Converte un valore al tipo specificato nello schema."""
        validator = cls.get_validator(schema.data_type)
        return validator.convert(value, schema.constraints)
    
    @classmethod
    def get_conversion_error(cls, value: Any, schema: DataSchema) -> str:
        """Ottieni messaggio di errore per conversione fallita."""
        validator = cls.get_validator(schema.data_type)
        return validator.get_error_message(value, schema.constraints)


class DataCompatibilityChecker:
    """Verifica la compatibilità tra tipi di dati."""
    
    # Matrice di compatibilità tra tipi
    _compatibility_matrix = {
        DataType.STRING: [DataType.STRING, DataType.EMAIL, DataType.URL, DataType.ANY],
        DataType.NUMBER: [DataType.NUMBER, DataType.STRING, DataType.ANY],
        DataType.BOOLEAN: [DataType.BOOLEAN, DataType.STRING, DataType.NUMBER, DataType.ANY],
        DataType.JSON: [DataType.JSON, DataType.STRING, DataType.ANY],
        DataType.ARRAY: [DataType.ARRAY, DataType.JSON, DataType.STRING, DataType.ANY],
        DataType.FILE: [DataType.FILE, DataType.STRING, DataType.ANY],
        DataType.EMAIL: [DataType.EMAIL, DataType.STRING, DataType.ANY],
        DataType.URL: [DataType.URL, DataType.STRING, DataType.ANY],
        DataType.ANY: list(DataType),  # ANY è compatibile con tutto
    }
    
    @classmethod
    def are_compatible(cls, from_type: DataType, to_type: DataType) -> bool:
        """Verifica se due tipi sono compatibili."""
        compatible_types = cls._compatibility_matrix.get(from_type, [])
        return to_type in compatible_types
    
    @classmethod
    def can_convert(cls, from_type: DataType, to_type: DataType) -> bool:
        """Verifica se è possibile convertire da un tipo all'altro."""
        # Per ora, usa la stessa logica di compatibilità
        # In futuro potrebbe essere più sofisticata
        return cls.are_compatible(from_type, to_type)
    
    @classmethod
    def get_conversion_warning(cls, from_type: DataType, to_type: DataType) -> Optional[str]:
        """Ottieni un avviso per conversioni potenzialmente problematiche."""
        if from_type == to_type:
            return None
        
        # Conversioni che potrebbero perdere informazioni
        if from_type == DataType.NUMBER and to_type == DataType.STRING:
            return "Conversione da numero a stringa: la formattazione potrebbe cambiare"
        
        if from_type == DataType.JSON and to_type == DataType.STRING:
            return "Conversione da JSON a stringa: la struttura verrà serializzata"
        
        if from_type == DataType.ARRAY and to_type == DataType.STRING:
            return "Conversione da array a stringa: gli elementi verranno concatenati"
        
        return None
