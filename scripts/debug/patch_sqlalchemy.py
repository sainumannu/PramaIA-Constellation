# SQLAlchemy patch per Python 3.13
# Da eseguire prima di importare SQLAlchemy

import typing

# Salva l'implementazione originale
original_generic_init_subclass = typing._generic_init_subclass

# Monkey patch della funzione che causa il problema
def patched_generic_init_subclass(cls, *args, **kwargs):
    try:
        return original_generic_init_subclass(cls, *args, **kwargs)
    except AssertionError as e:
        # Se l'errore riguarda SQLCoreOperations e TypingOnly, ignoriamo l'errore
        if "SQLCoreOperations" in str(e) and "TypingOnly" in str(e):
            return None
        # Altrimenti, riproponiamo l'errore originale
        raise

# Applica la patch
typing._generic_init_subclass = patched_generic_init_subclass

print("✓ SQLAlchemy patch per Python 3.13 applicata con successo")