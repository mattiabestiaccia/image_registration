"""
Core - Algoritmi di Registrazione Principali

Questo modulo contiene gli algoritmi principali per la registrazione di immagini
multispettrali e la gestione dei metadati geospaziali.

Componenti:
- ImageRegistration: Classe principale per la registrazione
- MetadataManager: Gestione metadati geospaziali
"""

from .image_registration import ImageRegistration
from .metadata_utils import MetadataManager

__all__ = [
    'ImageRegistration',
    'MetadataManager'
]
