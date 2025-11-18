"""
Package utils per PramaIAServer.
Contiene utility e helper functions per la manutenzione e pulizia del sistema.
"""

# Esporta il modulo di logging_service per facile accesso
try:
    from backend.utils.logging_service import pramaialogger
except ImportError:
    # Fallback se il modulo non può essere importato
    import logging
    pramaialogger = logging.getLogger("PramaIAFallbackLogger")

# Esporta la funzione unificata per ottenere logger
# Da usare in tutto il codice per standardizzare il logging
from backend.utils.logger_migration import get_logger