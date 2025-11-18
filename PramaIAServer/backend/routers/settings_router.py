from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import os
import importlib
import sys
import json

from backend.auth.dependencies import get_current_user, get_current_admin_user

# Configurazione del logger
logger = logging.getLogger(__name__)

# Router per le impostazioni di configurazione
router = APIRouter(
    prefix="/api/settings",
    tags=["settings"],
    dependencies=[Depends(get_current_user)],
)

class ConfigSettingUpdate(BaseModel):
    """Modello per l'aggiornamento di un'impostazione di configurazione"""
    key: str
    value: Any
    description: Optional[str] = None

class ConfigSetting(BaseModel):
    """Modello per la rappresentazione di un'impostazione di configurazione"""
    key: str
    value: Any
    description: Optional[str] = None
    is_editable: bool = True
    type: str = "string"  # string, integer, boolean, etc.

# Mappatura delle impostazioni disponibili
CONFIG_SETTINGS_MAP = {
    "PDF_EVENTS_MAX_AGE_HOURS": {
        "description": "Età massima (in ore) degli eventi PDF da mantenere",
        "is_editable": True,
        "type": "integer"
    },
    "PDF_EVENTS_MAX_COUNT": {
        "description": "Numero massimo di eventi PDF da mantenere",
        "is_editable": True,
        "type": "integer"
    },
    "PDF_EVENTS_AUTO_CLEANUP": {
        "description": "Abilita la pulizia automatica degli eventi PDF",
        "is_editable": True,
        "type": "boolean"
    }
}

def get_config_module():
    """Ottiene il modulo di configurazione"""
    try:
        return importlib.import_module("backend.core.config")
    except ImportError as e:
        logger.error(f"Impossibile importare il modulo di configurazione: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Impossibile accedere alle configurazioni del sistema"
        )

def get_config_file_path():
    """Ottiene il percorso del file di configurazione"""
    try:
        config_module = get_config_module()
        return config_module.__file__
    except Exception as e:
        logger.error(f"Impossibile ottenere il percorso del file di configurazione: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Impossibile determinare il percorso del file di configurazione"
        )

@router.get("/config", response_model=Dict[str, ConfigSetting])
async def get_config_settings(current_user: Dict = Depends(get_current_admin_user)):
    """
    Recupera tutte le impostazioni di configurazione disponibili
    Solo gli amministratori possono accedere a questa funzione
    """
    config_module = get_config_module()
    
    # Raccoglie le impostazioni dal modulo config
    settings = {}
    for key, info in CONFIG_SETTINGS_MAP.items():
        if hasattr(config_module, key):
            value = getattr(config_module, key)
            settings[key] = ConfigSetting(
                key=key,
                value=value,
                description=info.get("description", ""),
                is_editable=info.get("is_editable", True),
                type=info.get("type", "string")
            )
    
    return settings

@router.put("/config/{key}", response_model=ConfigSetting)
async def update_config_setting(
    key: str,
    setting: ConfigSettingUpdate = Body(...),
    current_user: Dict = Depends(get_current_admin_user)
):
    """
    Aggiorna un'impostazione di configurazione
    Solo gli amministratori possono accedere a questa funzione
    """
    # Verifica che la chiave sia valida
    if key not in CONFIG_SETTINGS_MAP:
        raise HTTPException(
            status_code=404,
            detail=f"Impostazione di configurazione '{key}' non trovata"
        )
    
    # Verifica che la chiave sia modificabile
    if not CONFIG_SETTINGS_MAP[key].get("is_editable", True):
        raise HTTPException(
            status_code=403,
            detail=f"L'impostazione di configurazione '{key}' non è modificabile"
        )
    
    # Verifica che la chiave nella path corrisponda alla chiave nel body
    if key != setting.key:
        raise HTTPException(
            status_code=400,
            detail="La chiave nel percorso non corrisponde alla chiave nel corpo della richiesta"
        )
    
    # Ottieni il tipo atteso per questo parametro
    expected_type = CONFIG_SETTINGS_MAP[key].get("type", "string")
    
    # Valida il tipo del valore
    if expected_type == "integer":
        try:
            setting.value = int(setting.value)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400,
                detail=f"Il valore per '{key}' deve essere un numero intero"
            )
    elif expected_type == "boolean":
        if isinstance(setting.value, str):
            setting.value = setting.value.lower() in ("true", "1", "yes", "y")
        elif not isinstance(setting.value, bool):
            raise HTTPException(
                status_code=400,
                detail=f"Il valore per '{key}' deve essere un booleano"
            )
    
    # Ottieni il percorso del file di configurazione
    config_file = get_config_file_path()
    if not config_file:
        raise HTTPException(
            status_code=500,
            detail="Impossibile determinare il percorso del file di configurazione"
        )
    
    # Leggi il contenuto del file
    with open(config_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Crea un backup del file di configurazione
    backup_file = f"{config_file}.bak"
    with open(backup_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    # Prepara il nuovo valore da scrivere nel file
    if expected_type == "string":
        new_value_str = f'"{setting.value}"'
    elif expected_type == "boolean":
        new_value_str = str(setting.value).lower()
    else:
        new_value_str = str(setting.value)
    
    # Pattern per trovare la definizione della variabile
    # Cerca pattern come: KEY = value  oppure  KEY = value  # commento
    import re
    pattern = fr"({key}\s*=\s*)[^\n#]+"
    
    # Sostituisci il valore
    new_content = re.sub(pattern, fr"\1{new_value_str}", content)
    
    # Scrivi il nuovo contenuto nel file
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception as e:
        # Ripristina il backup in caso di errore
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(content)
        logger.error(f"Errore durante l'aggiornamento del file di configurazione: {e}")
        raise HTTPException(
            status_code=500,
            detail="Errore durante l'aggiornamento del file di configurazione"
        )
    
    # Ricarica il modulo di configurazione
    try:
        config_module = get_config_module()
        importlib.reload(config_module)
    except Exception as e:
        logger.error(f"Errore durante il ricaricamento del modulo di configurazione: {e}")
        raise HTTPException(
            status_code=500,
            detail="Errore durante il ricaricamento della configurazione"
        )
    
    # Restituisci la nuova impostazione
    return ConfigSetting(
        key=key,
        value=setting.value,
        description=CONFIG_SETTINGS_MAP[key].get("description", ""),
        is_editable=CONFIG_SETTINGS_MAP[key].get("is_editable", True),
        type=CONFIG_SETTINGS_MAP[key].get("type", "string")
    )
