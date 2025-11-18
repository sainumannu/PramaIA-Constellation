"""
Utility per facilitare la migrazione dai logger standard a pramaialogger.
Fornisce una funzione di conversione automatica o semiautomatica.
"""

import inspect
import re
import logging

# Import pramaialogger
from backend.utils.logging_service import pramaialogger, PRAMAIALOG_AVAILABLE

def migrate_logger(module_name):
    """
    Restituisce un logger che utilizza pramaialogger se disponibile,
    altrimenti torna al logger standard di Python.
    
    Questo logger è compatibile con entrambi i sistemi e semplifica la migrazione.
    
    Args:
        module_name (str): Nome del modulo che sta richiedendo il logger
        
    Returns:
        object: Un logger compatibile con entrambi i sistemi
    """
    # Classe che implementa lo stesso API di un logger standard
    # ma invia tutto a pramaialogger
    class MigratedLogger:
        def __init__(self, name):
            self.name = name
            # Fallback logger in caso di problemi
            self.std_logger = logging.getLogger(name)
            
        def _format_context(self, *args, **kwargs):
            """Estrae informazioni contestuali da una chiamata a logger"""
            # Ottieni il contesto della chiamata
            current_frame = inspect.currentframe()
            if current_frame and current_frame.f_back and current_frame.f_back.f_back:
                caller_frame = current_frame.f_back.f_back
                caller_info = inspect.getframeinfo(caller_frame)
                
                # Prepara contesto con info sulla chiamata
                context = kwargs.pop("context", {}) or {}
                context.update({
                    "module": self.name,
                    "file": caller_info.filename,
                    "line": caller_info.lineno,
                    "function": caller_info.function
                })
            else:
                # Fallback se non possiamo ottenere il frame
                context = kwargs.pop("context", {}) or {}
                context.update({"module": self.name})
            return context
        
        def _extract_details(self, *args, **kwargs):
            """Estrae dettagli dai parametri della chiamata al logger"""
            details = kwargs.pop("details", {}) or {}
            
            # Se ci sono parametri aggiuntivi (logger.info("msg", "param1", "param2"))
            # li aggiungiamo ai dettagli
            if len(args) > 1:
                for i, arg in enumerate(args[1:]):
                    details[f"arg{i+1}"] = arg
                    
            return details
        
        def debug(self, message, *args, **kwargs):
            context = self._format_context(*args, **kwargs)
            details = self._extract_details(*args, **kwargs)
            
            if PRAMAIALOG_AVAILABLE:
                pramaialogger.debug(message, details=details, context=context)
            else:
                # Rimuovi parametri non supportati dal logger standard
                clean_kwargs = {k: v for k, v in kwargs.items() if k not in ['details', 'context']}
                self.std_logger.debug(message, *args, **clean_kwargs)
                
        def info(self, message, *args, **kwargs):
            context = self._format_context(*args, **kwargs)
            details = self._extract_details(*args, **kwargs)
            
            if PRAMAIALOG_AVAILABLE:
                pramaialogger.info(message, details=details, context=context)
            else:
                # Rimuovi parametri non supportati dal logger standard
                clean_kwargs = {k: v for k, v in kwargs.items() if k not in ['details', 'context']}
                self.std_logger.info(message, *args, **clean_kwargs)
                
        def warning(self, message, *args, **kwargs):
            context = self._format_context(*args, **kwargs)
            details = self._extract_details(*args, **kwargs)
            
            if PRAMAIALOG_AVAILABLE:
                pramaialogger.warning(message, details=details, context=context)
            else:
                # Rimuovi parametri non supportati dal logger standard
                clean_kwargs = {k: v for k, v in kwargs.items() if k not in ['details', 'context']}
                self.std_logger.warning(message, *args, **clean_kwargs)
                
        def error(self, message, *args, **kwargs):
            context = self._format_context(*args, **kwargs)
            details = self._extract_details(*args, **kwargs)
            
            if PRAMAIALOG_AVAILABLE:
                pramaialogger.error(message, details=details, context=context)
            else:
                # Rimuovi parametri non supportati dal logger standard
                clean_kwargs = {k: v for k, v in kwargs.items() if k not in ['details', 'context']}
                self.std_logger.error(message, *args, **clean_kwargs)
                
        def critical(self, message, *args, **kwargs):
            context = self._format_context(*args, **kwargs)
            details = self._extract_details(*args, **kwargs)
            
            if PRAMAIALOG_AVAILABLE:
                pramaialogger.critical(message, details=details, context=context)
            else:
                # Rimuovi parametri non supportati dal logger standard
                clean_kwargs = {k: v for k, v in kwargs.items() if k not in ['details', 'context']}
                self.std_logger.critical(message, *args, **clean_kwargs)
                
        def lifecycle(self, message, *args, **kwargs):
            context = self._format_context(*args, **kwargs)
            details = self._extract_details(*args, **kwargs)
            
            if PRAMAIALOG_AVAILABLE:
                pramaialogger.lifecycle(message, details=details, context=context)
            else:
                self.std_logger.info(f"[LIFECYCLE] {message}", *args, **kwargs)
                
        # Implementa altri metodi compatibili con il logging standard
        def setLevel(self, level):
            self.std_logger.setLevel(level)
        
        def exception(self, message, *args, **kwargs):
            context = self._format_context(*args, **kwargs)
            details = self._extract_details(*args, **kwargs)
            
            # Aggiungi informazioni sull'eccezione ai dettagli
            import traceback
            details["traceback"] = traceback.format_exc()
            
            if PRAMAIALOG_AVAILABLE:
                pramaialogger.error(message, details=details, context=context)
            else:
                self.std_logger.exception(message, *args, **kwargs)
    
    # Restituisci l'istanza del logger migrato
    return MigratedLogger(module_name)


def get_logger(module_name=None):
    """
    Funzione di utilità per ottenere un logger compatibile.
    Da usare in tutti i moduli in sostituzione di logging.getLogger().
    
    Args:
        module_name (str, optional): Nome del modulo. Se None, verrà rilevato automaticamente.
        
    Returns:
        object: Un logger compatibile
    """
    # Se il nome del modulo non è specificato, prova a ricavarlo automaticamente
    if module_name is None:
        # Ottieni il frame del chiamante
        current_frame = inspect.currentframe()
        if current_frame and current_frame.f_back:
            caller_frame = current_frame.f_back
            # Ottieni il modulo del chiamante
            module_name = caller_frame.f_globals.get('__name__', 'unknown')
        else:
            module_name = 'unknown'
    
    return migrate_logger(module_name)