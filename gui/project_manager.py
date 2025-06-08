#!/usr/bin/env python3
"""
Project Manager - Gestione progetti per Image Registration

Gestisce la creazione, organizzazione e pulizia delle cartelle di progetto
per l'elaborazione di immagini multispettrali.
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class ProjectManager:
    """Gestisce progetti di registrazione immagini con cartelle dedicate"""

    def __init__(self, base_projects_dir: str = None):
        """
        Inizializza il gestore progetti

        Args:
            base_projects_dir: Directory base per i progetti (default: ./projects/)
        """
        if base_projects_dir is None:
            base_projects_dir = os.path.join(os.getcwd(), "projects")

        self.base_projects_dir = Path(base_projects_dir)
        self.current_project = None
        self.project_metadata = {}

    def create_project(self, project_name: str = None,
                      source_paths: List[str] = None) -> str:
        """
        Crea una nuova cartella di progetto

        Args:
            project_name: Nome del progetto (auto-generato se None)
            source_paths: Lista di path sorgente (file o cartelle)

        Returns:
            Path della cartella di progetto creata
        """
        if project_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = f"project_{timestamp}"

        # Crea cartella progetto
        project_path = self.base_projects_dir / project_name
        project_path.mkdir(parents=True, exist_ok=True)

        # Crea sottocartelle
        (project_path / "registered").mkdir(exist_ok=True)
        (project_path / "visualizations").mkdir(exist_ok=True)
        (project_path / "exports").mkdir(exist_ok=True)

        # Salva metadata
        metadata = {
            "project_name": project_name,
            "created_at": datetime.now().isoformat(),
            "source_paths": source_paths or [],
            "source_type": self._detect_source_type(source_paths),
            "processed_files": [],
            "visualizations_saved": []
        }

        metadata_file = project_path / "project_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        self.current_project = str(project_path)
        self.project_metadata = metadata

        return str(project_path)

    def _detect_source_type(self, source_paths: List[str]) -> str:
        """Rileva il tipo di sorgente (file, files, folder)"""
        if not source_paths:
            return "unknown"

        if len(source_paths) == 1:
            if os.path.isdir(source_paths[0]):
                return "folder"
            else:
                return "single_file"
        else:
            return "multiple_files"

    def add_processed_file(self, original_path: str, processed_path: str):
        """Aggiunge un file processato ai metadata"""
        if not self.current_project:
            return

        self.project_metadata["processed_files"].append({
            "original_path": original_path,
            "processed_path": processed_path,
            "processed_at": datetime.now().isoformat()
        })

        self._save_metadata()

    def add_visualization(self, visualization_path: str, visualization_type: str):
        """Aggiunge una visualizzazione salvata ai metadata"""
        if not self.current_project:
            return

        self.project_metadata["visualizations_saved"].append({
            "path": visualization_path,
            "type": visualization_type,
            "saved_at": datetime.now().isoformat()
        })

        self._save_metadata()

    def _save_metadata(self):
        """Salva i metadata del progetto corrente"""
        if not self.current_project:
            return

        metadata_file = Path(self.current_project) / "project_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.project_metadata, f, indent=2, ensure_ascii=False)

    def get_project_paths(self) -> Dict[str, str]:
        """Restituisce i path delle cartelle del progetto corrente"""
        if not self.current_project:
            return {}

        project_path = Path(self.current_project)
        return {
            "project": str(project_path),
            "registered": str(project_path / "registered"),
            "visualizations": str(project_path / "visualizations"),
            "exports": str(project_path / "exports")
        }

    def has_saved_content(self) -> bool:
        """Verifica se il progetto ha contenuto salvato"""
        if not self.current_project:
            return False

        paths = self.get_project_paths()

        # Controlla se ci sono file nelle cartelle
        for folder_type in ["registered", "visualizations", "exports"]:
            folder_path = Path(paths[folder_type])
            if folder_path.exists() and any(folder_path.iterdir()):
                return True

        return False

    def cleanup_empty_project(self):
        """Rimuove il progetto se non contiene file salvati"""
        if not self.current_project:
            return

        if not self.has_saved_content():
            try:
                shutil.rmtree(self.current_project)
                print(f"🗑️  Progetto vuoto rimosso: {self.current_project}")
            except Exception as e:
                print(f"⚠️  Errore rimozione progetto: {e}")

        self.current_project = None
        self.project_metadata = {}

    def get_source_info(self) -> Dict:
        """Restituisce informazioni sui file sorgente"""
        if not self.project_metadata:
            return {}

        return {
            "paths": self.project_metadata.get("source_paths", []),
            "type": self.project_metadata.get("source_type", "unknown"),
            "count": len(self.project_metadata.get("source_paths", []))
        }
