"""
Processori per l'engine PramaIA.
Modulo di inizializzazione che esporta tutti i processori disponibili.

AGGIORNAMENTO: Aggiunti processori reali per sostituire gli stub.
NOTA: I processori PDF sono stati migrati all'architettura PDK.
Le implementazioni PDF si trovano ora in PramaIA-PDK/plugins/
"""

# Importa processori REALI COMPLETI - Con ChromaDB e dipendenze complete
try:
    # Real processors completi - IMPLEMENTAZIONI FUNZIONANTI CON CHROMADB
    from .real_processors_part2 import (
        VectorStoreOperationsProcessor as VectorStoreOperationsProcessor
    )
    
    # Real processors semplificati per gli altri - IMPLEMENTAZIONI FUNZIONANTI
    from .simple_real_processors import (
        SimpleEventInputProcessor as EventInputProcessor,
        SimpleFileParsingProcessor as FileParsingProcessor, 
        SimpleMetadataManagerProcessor as MetadataManagerProcessor,
        SimpleDocumentProcessorProcessor as DocumentProcessorProcessor,
        SimpleEventLoggerProcessor as EventLoggerProcessor
    )
    
    # Registro processori reali
    REAL_PROCESSORS = {
        'EventInputProcessor': EventInputProcessor,
        'FileParsingProcessor': FileParsingProcessor,
        'MetadataManagerProcessor': MetadataManagerProcessor,
        'DocumentProcessorProcessor': DocumentProcessorProcessor,
        'VectorStoreOperationsProcessor': VectorStoreOperationsProcessor,  # CHROMADB REALE
        'EventLoggerProcessor': EventLoggerProcessor
    }
    
except ImportError as e:
    import logging
    logging.warning(f"⚠️  Processori reali non disponibili, usando fallback semplificati: {e}")
    
    # Fallback ai processori semplificati se ChromaDB non è disponibile
    try:
        from .simple_real_processors import (
            SimpleEventInputProcessor as EventInputProcessor,
            SimpleFileParsingProcessor as FileParsingProcessor, 
            SimpleMetadataManagerProcessor as MetadataManagerProcessor,
            SimpleDocumentProcessorProcessor as DocumentProcessorProcessor,
            SimpleVectorStoreOperationsProcessor as VectorStoreOperationsProcessor,
            SimpleEventLoggerProcessor as EventLoggerProcessor
        )
        
        REAL_PROCESSORS = {
            'EventInputProcessor': EventInputProcessor,
            'FileParsingProcessor': FileParsingProcessor,
            'MetadataManagerProcessor': MetadataManagerProcessor,
            'DocumentProcessorProcessor': DocumentProcessorProcessor,
            'VectorStoreOperationsProcessor': VectorStoreOperationsProcessor,  # FALLBACK SIMPLE
            'EventLoggerProcessor': EventLoggerProcessor
        }
        
    except ImportError as e2:
        import logging
        logging.error(f"❌ Tutti i processori reali falliti: {e2}")
        REAL_PROCESSORS = {}

# Importa processori essenziali (NON PDF - quelli sono nel PDK)
try:
    # RAG processors - ESSENZIALI per la chat
    from .rag_processors import RAGQueryProcessor, RAGGenerationProcessor, DocumentIndexProcessor
    
    # LLM processors - ESSENZIALI per la chat  
    from .llm_processors import OpenAIProcessor, AnthropicProcessor, OllamaProcessor
    
    # Input/Output processors - ESSENZIALI per l'interfaccia
    from .input_processors import UserInputProcessor, FileInputProcessor
    from .output_processors import TextOutputProcessor, FileOutputProcessor
    
    # Data processors - UTILI per elaborazione dati
    from .data_processors import DataTransformProcessor, TextProcessor, JSONProcessor
    
    # API processors - UTILI per integrazioni
    from .api_processors import HTTPRequestProcessor, WebhookProcessor, APICallProcessor

except ImportError as e:
    # Log dell'errore ma continua comunque
    import logging
    logging.warning(f"⚠️  Alcuni processori non disponibili: {e}")
    # Definizioni stub per evitare errori
    RAGQueryProcessor = None
    RAGGenerationProcessor = None
    DocumentIndexProcessor = None

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
    
    Returns:
        dict: Stato delle dipendenze per ogni processore
    """
    status = {}
    
    # Test EventInputProcessor (sempre disponibile)
    status['EventInputProcessor'] = {'available': True, 'issues': []}
    
    # Test FileParsingProcessor
    try:
        import PyPDF2
        import pdfplumber
        status['FileParsingProcessor'] = {'available': True, 'issues': []}
    except ImportError as e:
        status['FileParsingProcessor'] = {
            'available': False, 
            'issues': ['PyPDF2 o pdfplumber non disponibili']
        }
    
    # Test MetadataManagerProcessor (sempre disponibile)
    status['MetadataManagerProcessor'] = {'available': True, 'issues': []}
    
    # Test DocumentProcessorProcessor (sempre disponibile)  
    status['DocumentProcessorProcessor'] = {'available': True, 'issues': []}
    
    # Test VectorStoreOperationsProcessor
    issues = []
    try:
        import chromadb
    except ImportError:
        issues.append('ChromaDB non disponibile')
        
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        issues.append('SentenceTransformers non disponibile')
    
    status['VectorStoreOperationsProcessor'] = {
        'available': len(issues) == 0,
        'issues': issues,
        'type': 'real_chromadb' if len(issues) == 0 else 'fallback_simple'
    }
    
    # Test EventLoggerProcessor (sempre disponibile)
    status['EventLoggerProcessor'] = {'available': True, 'issues': []}
    
    return status

__all__ = [
    # Processori REALI - NUOVI
    'EventInputProcessor',
    'FileParsingProcessor',
    'MetadataManagerProcessor', 
    'DocumentProcessorProcessor',
    'VectorStoreOperationsProcessor',
    'EventLoggerProcessor',
    'REAL_PROCESSORS',
    
    # Processori RAG - ESSENZIALI per chat
    'RAGQueryProcessor',
    'RAGGenerationProcessor', 
    'DocumentIndexProcessor',
    
    # Processori LLM - ESSENZIALI per chat
    'OpenAIProcessor',
    'AnthropicProcessor', 
    'OllamaProcessor',
    
    # Processori I/O - ESSENZIALI per interfaccia
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
    'validate_processor_dependencies',
    
    # NOTA: I processori PDF sono stati migrati al PDK
    # Vedere PramaIA-PDK/plugins/ per le implementazioni PDF
] 
