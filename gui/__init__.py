"""
GUI - Interfaccia Grafica per Image Registration

Questo modulo contiene l'interfaccia grafica tkinter per la gestione
di progetti di registrazione di immagini multispettrali.

Funzionalità principali:
- Selezione di immagini singole, multiple o cartelle
- Creazione automatica di cartelle di progetto
- Integrazione con tutti i visualizzatori esistenti
- Gestione metadata e path originali
- Pulizia automatica cartelle vuote

Uso:
    from image_registration.gui import launch_gui
    launch_gui()
"""

# Import principale
try:
    from .main_window import launch_gui
    __all__ = ['launch_gui']
except ImportError as e:
    # tkinter potrebbe non essere disponibile
    def launch_gui():
        raise ImportError(f"GUI non disponibile: {e}")
    __all__ = ['launch_gui']
