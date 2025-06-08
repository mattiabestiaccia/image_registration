"""
Advanced Multiband Image Registration Module

Questo modulo implementa un sistema avanzato per la registrazione automatica 
di immagini multispettrali a 5 bande disallineate utilizzando multiple tecniche:
SLIC, feature matching ORB, trasformazioni affini robuste e correlazione di fase.

Struttura del modulo:
- core/: Algoritmi di registrazione principali e gestione metadati
- utils/: Utilities e funzioni di supporto
- visualization/: Visualizzatori RGB e interattivi
- cli/: Interfacce a riga di comando
- docs/: Documentazione

Uso principale:
    from image_registration.core import ImageRegistration
    from image_registration.utils import find_image_groups
"""

__version__ = "1.0.0"
__author__ = "Advanced Image Registration Module"

# Import principali per compatibilità
from .core.image_registration import ImageRegistration
from .utils.utils import find_image_groups, create_output_filename

__all__ = [
    'ImageRegistration',
    'find_image_groups', 
    'create_output_filename'
]
