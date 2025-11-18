"""
Servizio per gestire filtri configurabili che gli agent possono interrogare
per evitare di trasferire file non processabili (es. video, film, etc.)
"""

import os
import json
import logging
from typing import Dict, List, Optional, Set, Any
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class FilterAction(Enum):
    """Azione da intraprendere per un file"""
    PROCESS_FULL = "process_full"      # Elabora completamente il file
    METADATA_ONLY = "metadata_only"    # Solo metadati (nome, dimensione, data)
    SKIP = "skip"                       # Ignora completamente

@dataclass
class FileFilter:
    """Definizione di un filtro per file"""
    name: str
    description: str
    extensions: List[str]              # Estensioni file (.mp4, .pdf, etc.)
    max_size_mb: Optional[int]         # Dimensione massima in MB
    min_size_mb: Optional[int]         # Dimensione minima in MB
    action: FilterAction               # Azione da intraprendere
    extract_metadata: List[str]        # Metadati da estrarre per METADATA_ONLY
    priority: int = 100                # Priorità del filtro (più basso = maggiore priorità)
    
class AgentFilterService:
    """
    Servizio per gestire filtri configurabili per gli agent
    """
    
    def __init__(self, config_file: str = "agent_filters_config.json"):
        self.config_file = config_file
        self.filters: List[FileFilter] = []
        self.load_default_filters()
        self.load_custom_filters()
        
    def load_default_filters(self):
        """Carica filtri predefiniti ottimizzati per RAG"""
        default_filters = [
            # FILE PROCESSABILI COMPLETAMENTE
            FileFilter(
                name="documents_text",
                description="Documenti di testo processabili per RAG",
                extensions=[".pdf", ".txt", ".md", ".docx", ".doc", ".rtf"],
                max_size_mb=100,  # Limite ragionevole per documenti
                min_size_mb=None,
                action=FilterAction.PROCESS_FULL,
                extract_metadata=["filename", "size", "modified_date", "path"],
                priority=10
            ),
            
            FileFilter(
                name="spreadsheets_data", 
                description="Fogli di calcolo e dati strutturati",
                extensions=[".xlsx", ".xls", ".csv", ".json", ".xml"],
                max_size_mb=50,
                min_size_mb=None,
                action=FilterAction.PROCESS_FULL,
                extract_metadata=["filename", "size", "modified_date", "path", "sheet_names"],
                priority=20
            ),
            
            FileFilter(
                name="presentations",
                description="Presentazioni processabili",
                extensions=[".pptx", ".ppt"],
                max_size_mb=100,
                min_size_mb=None,
                action=FilterAction.PROCESS_FULL,
                extract_metadata=["filename", "size", "modified_date", "path", "slide_count"],
                priority=30
            ),
            
            # CODE FILES
            FileFilter(
                name="source_code",
                description="File di codice sorgente",
                extensions=[".py", ".js", ".ts", ".html", ".css", ".sql", ".java", ".cpp", ".c", ".h"],
                max_size_mb=10,
                min_size_mb=None,
                action=FilterAction.PROCESS_FULL,
                extract_metadata=["filename", "size", "modified_date", "path", "language"],
                priority=40
            ),
            
            # SOLO METADATI (troppo grandi o non text-based)
            FileFilter(
                name="images_metadata_only",
                description="Immagini - solo metadati",
                extensions=[".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"],
                max_size_mb=None,
                min_size_mb=None,
                action=FilterAction.METADATA_ONLY,
                extract_metadata=["filename", "size", "modified_date", "path", "dimensions", "format"],
                priority=50
            ),
            
            FileFilter(
                name="audio_metadata_only",
                description="File audio - solo metadati",
                extensions=[".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma"],
                max_size_mb=None,
                min_size_mb=None,
                action=FilterAction.METADATA_ONLY,
                extract_metadata=["filename", "size", "modified_date", "path", "duration", "bitrate", "artist", "title"],
                priority=60
            ),
            
            # SKIP COMPLETAMENTE (troppo grandi, non utili per RAG)
            FileFilter(
                name="video_skip",
                description="File video - troppo grandi per RAG",
                extensions=[".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
                max_size_mb=None,
                min_size_mb=None,
                action=FilterAction.SKIP,
                extract_metadata=[],
                priority=70
            ),
            
            FileFilter(
                name="archives_skip",
                description="Archivi compressi - skip per evitare processing ricorsivo",
                extensions=[".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
                max_size_mb=None,
                min_size_mb=None,
                action=FilterAction.SKIP,
                extract_metadata=[],
                priority=80
            ),
            
            FileFilter(
                name="executables_skip",
                description="File eseguibili - non processabili",
                extensions=[".exe", ".msi", ".dmg", ".deb", ".rpm", ".app"],
                max_size_mb=None,
                min_size_mb=None,
                action=FilterAction.SKIP,
                extract_metadata=[],
                priority=90
            ),
            
            # FALLBACK GENERICO per file piccoli sconosciuti
            FileFilter(
                name="small_files_metadata",
                description="File piccoli sconosciuti - solo metadati",
                extensions=["*"],  # Wildcard per qualsiasi estensione
                max_size_mb=1,     # Solo file molto piccoli
                min_size_mb=None,
                action=FilterAction.METADATA_ONLY,
                extract_metadata=["filename", "size", "modified_date", "path"],
                priority=999       # Bassa priorità (ultimo fallback)
            )
        ]
        
        self.filters = default_filters
        logger.info(f"Caricati {len(default_filters)} filtri predefiniti")
        
    def load_custom_filters(self):
        """Carica filtri personalizzati da file di configurazione"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    custom_data = json.load(f)
                    
                custom_filters = []
                for filter_data in custom_data.get("custom_filters", []):
                    try:
                        custom_filter = FileFilter(
                            name=filter_data["name"],
                            description=filter_data["description"],
                            extensions=filter_data["extensions"],
                            max_size_mb=filter_data.get("max_size_mb"),
                            min_size_mb=filter_data.get("min_size_mb"),
                            action=FilterAction(filter_data["action"]),
                            extract_metadata=filter_data.get("extract_metadata", []),
                            priority=filter_data.get("priority", 100)
                        )
                        custom_filters.append(custom_filter)
                    except Exception as e:
                        logger.warning(f"Errore caricamento filtro personalizzato: {e}")
                        
                # Aggiungi filtri custom (sostituiscono quelli con stesso nome)
                for custom_filter in custom_filters:
                    # Rimuovi filtro esistente con stesso nome
                    self.filters = [f for f in self.filters if f.name != custom_filter.name]
                    self.filters.append(custom_filter)
                    
                logger.info(f"Caricati {len(custom_filters)} filtri personalizzati")
                
        except Exception as e:
            logger.warning(f"Errore caricamento filtri personalizzati: {e}")
            
    def save_custom_filters(self):
        """Salva filtri personalizzati su file"""
        try:
            # Separa filtri default da custom (quelli con priorità custom)
            custom_filters = [f for f in self.filters if f.priority >= 1000 or f.name.startswith("custom_")]
            
            config_data = {
                "custom_filters": [asdict(f) for f in custom_filters],
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Salvati {len(custom_filters)} filtri personalizzati")
            
        except Exception as e:
            logger.error(f"Errore salvataggio filtri personalizzati: {e}")
            
    def evaluate_file(self, file_path: str, file_size_bytes: Optional[int] = None) -> Dict[str, Any]:
        """
        Valuta un file contro i filtri configurati e restituisce azione da intraprendere
        
        Args:
            file_path: Percorso del file
            file_size_bytes: Dimensione del file in bytes (opzionale, viene calcolata se None)
            
        Returns:
            Dict con azione, metadati da estrarre, e dettagli del filtro applicato
        """
        try:
            path = Path(file_path)
            extension = path.suffix.lower()
            
            # Calcola dimensione se non fornita
            if file_size_bytes is None:
                try:
                    file_size_bytes = path.stat().st_size if path.exists() else 0
                except:
                    file_size_bytes = 0
                    
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            # Ordina filtri per priorità
            sorted_filters = sorted(self.filters, key=lambda f: f.priority)
            
            # Trova primo filtro che matcha
            for filter_rule in sorted_filters:
                if self._matches_filter(extension, file_size_mb, filter_rule):
                    return {
                        "action": filter_rule.action.value,
                        "filter_name": filter_rule.name,
                        "filter_description": filter_rule.description,
                        "extract_metadata": filter_rule.extract_metadata,
                        "file_size_mb": round(file_size_mb, 2),
                        "should_process": filter_rule.action == FilterAction.PROCESS_FULL,
                        "should_upload": filter_rule.action in [FilterAction.PROCESS_FULL, FilterAction.METADATA_ONLY]
                    }
                    
            # Nessun filtro matchato - azione di default
            return {
                "action": FilterAction.METADATA_ONLY.value,
                "filter_name": "default_fallback",
                "filter_description": "Nessun filtro specifico - solo metadati",
                "extract_metadata": ["filename", "size", "modified_date", "path"],
                "file_size_mb": round(file_size_mb, 2),
                "should_process": False,
                "should_upload": True
            }
            
        except Exception as e:
            logger.error(f"Errore valutazione file {file_path}: {e}")
            return {
                "action": FilterAction.SKIP.value,
                "filter_name": "error_fallback",
                "filter_description": f"Errore valutazione: {str(e)}",
                "extract_metadata": [],
                "file_size_mb": 0,
                "should_process": False,
                "should_upload": False
            }
            
    def _matches_filter(self, extension: str, file_size_mb: float, filter_rule: FileFilter) -> bool:
        """Verifica se un file matcha un filtro specifico"""
        
        # Check estensione
        if "*" not in filter_rule.extensions and extension not in filter_rule.extensions:
            return False
            
        # Check dimensione massima
        if filter_rule.max_size_mb is not None and file_size_mb > filter_rule.max_size_mb:
            return False
            
        # Check dimensione minima
        if filter_rule.min_size_mb is not None and file_size_mb < filter_rule.min_size_mb:
            return False
            
        return True
        
    def get_filters_summary(self) -> Dict[str, Any]:
        """Restituisce riassunto dei filtri configurati"""
        summary = {
            "total_filters": len(self.filters),
            "filters_by_action": {},
            "supported_extensions": set(),
            "filters": []
        }
        
        for filter_rule in self.filters:
            action = filter_rule.action.value
            summary["filters_by_action"][action] = summary["filters_by_action"].get(action, 0) + 1
            
            summary["supported_extensions"].update(filter_rule.extensions)
            
            summary["filters"].append({
                "name": filter_rule.name,
                "description": filter_rule.description,
                "extensions": filter_rule.extensions,
                "action": filter_rule.action.value,
                "priority": filter_rule.priority,
                "max_size_mb": filter_rule.max_size_mb
            })
            
        summary["supported_extensions"] = sorted(list(summary["supported_extensions"]))
        summary["filters"] = sorted(summary["filters"], key=lambda f: f["priority"])
        
        return summary
        
    def add_custom_filter(self, filter_data: Dict[str, Any]) -> bool:
        """Aggiunge un filtro personalizzato"""
        try:
            custom_filter = FileFilter(
                name=f"custom_{filter_data['name']}",
                description=filter_data["description"],
                extensions=filter_data["extensions"],
                max_size_mb=filter_data.get("max_size_mb"),
                min_size_mb=filter_data.get("min_size_mb"),
                action=FilterAction(filter_data["action"]),
                extract_metadata=filter_data.get("extract_metadata", []),
                priority=filter_data.get("priority", 1000)  # Priorità custom
            )
            
            # Rimuovi filtro esistente con stesso nome
            self.filters = [f for f in self.filters if f.name != custom_filter.name]
            self.filters.append(custom_filter)
            
            self.save_custom_filters()
            logger.info(f"Aggiunto filtro personalizzato: {custom_filter.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Errore aggiunta filtro personalizzato: {e}")
            return False
            
    def remove_custom_filter(self, filter_name: str) -> bool:
        """Rimuove un filtro personalizzato"""
        try:
            initial_count = len(self.filters)
            self.filters = [f for f in self.filters if f.name != filter_name and f.name != f"custom_{filter_name}"]
            
            if len(self.filters) < initial_count:
                self.save_custom_filters()
                logger.info(f"Rimosso filtro personalizzato: {filter_name}")
                return True
            else:
                logger.warning(f"Filtro personalizzato non trovato: {filter_name}")
                return False
                
        except Exception as e:
            logger.error(f"Errore rimozione filtro personalizzato: {e}")
            return False

# Istanza globale del servizio
agent_filter_service = AgentFilterService()
