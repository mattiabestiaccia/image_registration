"""
Visualization - Visualizzatori per Immagini Multispettrali

Questo modulo contiene tutti i visualizzatori per immagini multispettrali
MicaSense RedEdge, inclusi visualizzatori RGB e interattivi.

Sottocartelle:
- rgb/: Visualizzatori per composizioni RGB e false color
- interactive/: Visualizzatori interattivi per navigazione bande

Uso rapido:
    # RGB veloce
    from image_registration.visualization.rgb import quick_rgb_view
    
    # Visualizzatore interattivo
    from image_registration.visualization.interactive import InteractiveBandViewer
"""

# Import per compatibilità (opzionali)
try:
    from .rgb.quick_rgb_view import quick_rgb_view
    from .interactive.interactive_band_viewer import InteractiveBandViewer
except ImportError:
    # I moduli di visualizzazione potrebbero avere dipendenze opzionali
    pass

__all__ = []
