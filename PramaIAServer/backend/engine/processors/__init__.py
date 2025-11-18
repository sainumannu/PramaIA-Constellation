"""
Processori per l'engine PramaIA.
Modulo di inizializzazione che esporta tutti i processori disponibili.

NOTA: I processori PDF sono stati migrati all'architettura PDK.
Le implementazioni PDF si trovano ora in PramaIA-PDK/plugins/
"""

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

__all__ = [
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
    
    # NOTA: I processori PDF sono stati migrati al PDK
    # Vedere PramaIA-PDK/plugins/ per le implementazioni PDF
] 
