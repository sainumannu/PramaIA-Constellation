"""
Modulo di inizializzazione e configurazione per PramaIALog nel backend.
Centralizza l'integrazione con il servizio di logging PramaIA.
"""
import os
import logging
from pathlib import Path
import sys

# Configura il logger di fallback (standard)
logger = logging.getLogger(__name__)

# Verifica se il modulo pramaialog è disponibile
try:
    # Prova a importare il modulo pramaialog dal path locale
    from backend.utils.pramaialog import PramaIALogger, LogLevel, LogProject
    
    # Flag per indicare che pramaialog è disponibile
    PRAMAIALOG_AVAILABLE = True
    logger.info("Modulo pramaialog importato con successo")
except ImportError:
    # Se il modulo non è disponibile, imposta un flag per usare un logger di fallback
    PRAMAIALOG_AVAILABLE = False
    logger.warning("Modulo pramaialog non disponibile, verrà usato il logger standard")

# Funzione per ottenere le variabili d'ambiente relative a LogService
def get_log_service_config():
    """
    Ottiene la configurazione per il LogService dalle variabili d'ambiente.
    
    Returns:
        tuple: (host, api_key, enabled) - configurazione per PramaIALog
    """
    host = os.environ.get("PRAMAIALOG_HOST", "http://localhost:8081")
    api_key = os.environ.get("PRAMAIALOG_API_KEY", "")
    
    # Il servizio è abilitato se l'API key è impostata e non è vuota
    enabled = bool(api_key and PRAMAIALOG_AVAILABLE)
    
    return host, api_key, enabled

# Inizializza il logger PramaIA globale
def init_pramaialog():
    """
    Inizializza il logger PramaIA con la configurazione dalle variabili d'ambiente.
    
    Returns:
        object: istanza del logger configurato (PramaIALogger o logger standard)
    """
    host, api_key, enabled = get_log_service_config()
    
    if enabled:
        try:
            # Crea un'istanza del logger PramaIA
            pramaialogger = PramaIALogger(
                api_key=api_key,
                project=LogProject.SERVER,  # Utilizza l'enum LogProject
                module="pramaiaserver",     # Nome del modulo (può essere personalizzato)
                host=host
            )
            
            logger.info(f"PramaIALogger inizializzato con successo. Host: {host}")
            return pramaialogger
        
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione di PramaIALogger: {e}", exc_info=True)
            return create_fallback_logger()
    else:
        logger.warning("PramaIALogger disabilitato. Verrà usato il logger standard.")
        return create_fallback_logger()

def create_fallback_logger():
    """
    Crea un logger di fallback compatibile con l'interfaccia di PramaIALogger.
    
    Returns:
        object: un wrapper del logger standard con l'interfaccia di PramaIALogger
    """
    # Classe wrapper per emulare l'interfaccia di PramaIALogger
    class FallbackLogger:
        def __init__(self):
            self.logger = logging.getLogger("PramaIAFallbackLogger")
        
        def debug(self, message, details=None, context=None):
            context_str = f" [Context: {context}]" if context else ""
            details_str = f" [Details: {details}]" if details else ""
            self.logger.debug(f"{message}{details_str}{context_str}")
        
        def info(self, message, details=None, context=None):
            context_str = f" [Context: {context}]" if context else ""
            details_str = f" [Details: {details}]" if details else ""
            self.logger.info(f"{message}{details_str}{context_str}")
        
        def warning(self, message, details=None, context=None):
            context_str = f" [Context: {context}]" if context else ""
            details_str = f" [Details: {details}]" if details else ""
            self.logger.warning(f"{message}{details_str}{context_str}")
        
        def error(self, message, details=None, context=None):
            context_str = f" [Context: {context}]" if context else ""
            details_str = f" [Details: {details}]" if details else ""
            self.logger.error(f"{message}{details_str}{context_str}")
        
        def critical(self, message, details=None, context=None):
            context_str = f" [Context: {context}]" if context else ""
            details_str = f" [Details: {details}]" if details else ""
            self.logger.critical(f"{message}{details_str}{context_str}")
        
        def lifecycle(self, message, details=None, context=None):
            context_str = f" [Context: {context}]" if context else ""
            details_str = f" [Details: {details}]" if details else ""
            self.logger.info(f"[LIFECYCLE] {message}{details_str}{context_str}")
    
    return FallbackLogger()

# Esporta un'istanza globale del logger PramaIA
# Questo è l'oggetto che altri moduli dovrebbero importare e utilizzare
pramaialogger = init_pramaialog()