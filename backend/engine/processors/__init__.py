"""
Processori per l'engine PramaIA.
Modulo di inizializzazione che esporta tutti i processori disponibili.

NOTA: I processori PDF sono stati migrati all'architettura PDK.
Le implementazioni PDF si trovano ora in PramaIA-PDK/plugins/
"""

# Importa processori REALI - Solo implementazioni complete
from .real_processors_part2 import (
    DocumentProcessorProcessor,
    VectorStoreOperationsProcessor,
    EventLoggerProcessor
)

from .simple_real_processors import (
    SimpleEventInputProcessor as EventInputProcessor,
    SimpleFileParsingProcessor as FileParsingProcessor, 
    SimpleMetadataManagerProcessor as MetadataManagerProcessor
)

# Registro processori reali
REAL_PROCESSORS = {
    'EventInputProcessor': EventInputProcessor,
    'FileParsingProcessor': FileParsingProcessor,
    'MetadataManagerProcessor': MetadataManagerProcessor,
    'DocumentProcessorProcessor': DocumentProcessorProcessor,
    'VectorStoreOperationsProcessor': VectorStoreOperationsProcessor,
    'EventLoggerProcessor': EventLoggerProcessor
}

# Importa processori essenziali
# RAG processors - TEMPORANEAMENTE COMMENTATI per dependency issues
# from .rag_processors import RAGQueryProcessor, RAGGenerationProcessor, DocumentIndexProcessor

# LLM processors - ESSENZIALI per la chat  
from .llm_processors import OpenAIProcessor, AnthropicProcessor, OllamaProcessor

# Input/Output processors - ESSENZIALI per l'interfaccia
from .input_processors import UserInputProcessor, FileInputProcessor
from .output_processors import TextOutputProcessor, FileOutputProcessor

# Data processors - UTILI per elaborazione dati
from .data_processors import DataTransformProcessor, TextProcessor, JSONProcessor

# API processors - UTILI per integrazioni
from .api_processors import HTTPRequestProcessor, WebhookProcessor, APICallProcessor

# Funzioni di utilità per gestione processori
def get_real_processor(processor_name: str):
    """
    Ottiene il processore reale dato il nome.
    
    Args:
        processor_name: Nome del processore (può essere stub o reale)
        
    Returns:
        Classe del processore reale
        
    Raises:
        KeyError: Se il processore non è trovato
    """
    if processor_name in REAL_PROCESSORS:
        return REAL_PROCESSORS[processor_name]
    else:
        raise KeyError(f"Processore reale non trovato: {processor_name}")

def list_available_processors():
    """Elenca tutti i processori reali disponibili."""
    return list(REAL_PROCESSORS.keys())

def validate_processor_dependencies():
    """
    Valida che tutte le dipendenze dei processori siano disponibili.
    Se manca qualcosa, il sistema deve fallire chiaramente.
    
    Returns:
        dict: Stato delle dipendenze per ogni processore
    """
    status = {}
    
    # Test EventInputProcessor
    status['EventInputProcessor'] = {'available': True, 'issues': []}
    
    # Test FileParsingProcessor - DEVE avere PyPDF2 o fallisce
    import PyPDF2
    import pdfplumber
    status['FileParsingProcessor'] = {'available': True, 'issues': []}
    
    # Test MetadataManagerProcessor
    status['MetadataManagerProcessor'] = {'available': True, 'issues': []}
    
    # Test DocumentProcessorProcessor
    status['DocumentProcessorProcessor'] = {'available': True, 'issues': []}
    
    # Test VectorStoreOperationsProcessor - DEVE avere ChromaDB o fallisce
    import chromadb
    from sentence_transformers import SentenceTransformer
    status['VectorStoreOperationsProcessor'] = {
        'available': True,
        'issues': [],
        'type': 'real_chromadb'
    }
    
    # Test EventLoggerProcessor
    status['EventLoggerProcessor'] = {'available': True, 'issues': []}
    
    return status

__all__ = [
    # Processori REALI
    'EventInputProcessor',
    'FileParsingProcessor',
    'MetadataManagerProcessor', 
    'DocumentProcessorProcessor',
    'VectorStoreOperationsProcessor',
    'EventLoggerProcessor',
    'REAL_PROCESSORS',
    
    # Processori RAG - TEMPORANEAMENTE COMMENTATI
    # 'RAGQueryProcessor',
    # 'RAGGenerationProcessor', 
    # 'DocumentIndexProcessor',
    
    # Processori LLM
    'OpenAIProcessor',
    'AnthropicProcessor', 
    'OllamaProcessor',
    
    # Processori I/O
    'UserInputProcessor',
    'FileInputProcessor',
    'TextOutputProcessor',
    'FileOutputProcessor',
    
    # Processori dati e API
    'DataTransformProcessor',
    'TextProcessor',
    'JSONProcessor',
    'HTTPRequestProcessor',
    'WebhookProcessor', 
    'APICallProcessor',
    
    # Funzioni utilità
    'get_real_processor',
    'list_available_processors',
    'validate_processor_dependencies'
]
