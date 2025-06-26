#!/usr/bin/env python3
"""
Project Logger - Sistema di logging su file per progetti Image Registration

Sistema di logging che salva i log e i traceback dell'ultima esecuzione 
in un file nella cartella del progetto corrente.
"""

import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO
import threading


class ProjectLogger:
    """Logger per progetti che scrive su file con rotazione automatica"""
    
    def __init__(self, log_file_path: Optional[str] = None):
        """
        Inizializza il logger del progetto
        
        Args:
            log_file_path: Percorso del file di log (se None, non scrive su file)
        """
        self.log_file_path = log_file_path
        self.log_file: Optional[TextIO] = None
        self.lock = threading.Lock()
        
        # Setup logger
        self.logger = logging.getLogger('ProjectLogger')
        self.logger.setLevel(logging.DEBUG)
        
        # Rimuovi handler esistenti per evitare duplicati
        self.logger.handlers.clear()
        
        # Setup formatter
        self.formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Setup file handler se specificato
        if self.log_file_path:
            self._setup_file_logging()
        
        # Log informazioni di sistema all'avvio
        self._log_system_info()
    
    def _setup_file_logging(self):
        """Configura il logging su file"""
        try:
            # Assicurati che la directory esista
            log_dir = os.path.dirname(self.log_file_path)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            # Rimuovi file di log precedenti per mantenere solo l'ultimo
            self._cleanup_old_logs()
            
            # Apri file di log
            self.log_file = open(self.log_file_path, 'w', encoding='utf-8')
            
            # Crea file handler
            file_handler = logging.FileHandler(self.log_file_path, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(self.formatter)
            
            self.logger.addHandler(file_handler)
            
            self.info(f"Logger inizializzato - File: {self.log_file_path}")
            
        except Exception as e:
            print(f"Errore inizializzazione logger: {e}")
    
    def _cleanup_old_logs(self):
        """Rimuove i file di log precedenti mantenendo solo l'ultimo"""
        try:
            log_dir = Path(self.log_file_path).parent
            if log_dir.exists():
                # Trova tutti i file di log della sessione
                log_files = list(log_dir.glob("session_*.log"))
                
                # Ordina per data di modifica e rimuovi tutti tranne i più recenti
                if len(log_files) > 0:
                    log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    
                    # Mantieni solo gli ultimi 3 file di log
                    for old_log in log_files[3:]:
                        try:
                            old_log.unlink()
                        except:
                            pass  # Ignora errori nella rimozione
        except Exception:
            pass  # Ignora errori nella pulizia
    
    def _log_system_info(self):
        """Logga informazioni di sistema all'avvio"""
        self.info("=" * 60)
        self.info("NUOVA SESSIONE IMAGE REGISTRATION")
        self.info("=" * 60)
        self.info(f"Timestamp avvio: {datetime.now().isoformat()}")
        self.info(f"Python: {sys.version}")
        self.info(f"Piattaforma: {sys.platform}")
        self.info(f"Working directory: {os.getcwd()}")
        
        # Informazioni sui moduli critici (versione veloce)
        modules_info = []
        try:
            import numpy
            modules_info.append(f"NumPy: {numpy.__version__}")
        except:
            modules_info.append("NumPy: non disponibile")
        
        try:
            import cv2
            modules_info.append(f"OpenCV: {cv2.__version__}")
        except:
            modules_info.append("OpenCV: non disponibile")
        
        try:
            import matplotlib
            modules_info.append(f"Matplotlib: {matplotlib.__version__}")
        except:
            modules_info.append("Matplotlib: non disponibile")
        
        self.info("Moduli: " + ", ".join(modules_info))
        
        self.info("-" * 60)
    
    def debug(self, message: str):
        """Log a livello DEBUG"""
        with self.lock:
            self.logger.debug(message)
    
    def info(self, message: str):
        """Log a livello INFO"""
        with self.lock:
            self.logger.info(message)
    
    def warning(self, message: str):
        """Log a livello WARNING"""
        with self.lock:
            self.logger.warning(message)
    
    def error(self, message: str):
        """Log a livello ERROR"""
        with self.lock:
            self.logger.error(message)
    
    def critical(self, message: str):
        """Log a livello CRITICAL"""
        with self.lock:
            self.logger.critical(message)
    
    def exception(self, message: str):
        """Log un'eccezione con traceback completo"""
        with self.lock:
            self.logger.error(message)
            self.logger.error("Traceback completo:")
            self.logger.error(traceback.format_exc())
    
    def log_operation_start(self, operation: str, details: dict = None):
        """Logga l'inizio di un'operazione"""
        self.info(f"INIZIO OPERAZIONE: {operation}")
        if details:
            for key, value in details.items():
                self.info(f"  {key}: {value}")
    
    def log_operation_end(self, operation: str, success: bool, details: dict = None):
        """Logga la fine di un'operazione"""
        status = "SUCCESSO" if success else "FALLIMENTO"
        self.info(f"FINE OPERAZIONE: {operation} - {status}")
        if details:
            for key, value in details.items():
                self.info(f"  {key}: {value}")
    
    def log_file_operation(self, operation: str, file_path: str, success: bool = True):
        """Logga operazioni su file"""
        status = "OK" if success else "ERRORE"
        self.info(f"FILE {operation.upper()}: {file_path} - {status}")
    
    def close(self):
        """Chiude il logger e il file"""
        with self.lock:
            self.info("Chiusura logger...")
            self.info("=" * 60)
            
            # Rimuovi tutti gli handler
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)
            
            # Chiudi file se aperto
            if self.log_file:
                try:
                    self.log_file.close()
                except:
                    pass
                self.log_file = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type is not None:
            self.exception(f"Eccezione non gestita: {exc_type.__name__}: {exc_val}")
        self.close()


def create_logger_for_project(project_manager) -> Optional[ProjectLogger]:
    """
    Crea un logger per il progetto corrente
    
    Args:
        project_manager: Istanza del ProjectManager
        
    Returns:
        ProjectLogger o None se nessun progetto attivo
    """
    log_file_path = project_manager.get_current_log_file_path()
    if log_file_path:
        return ProjectLogger(log_file_path)
    return None