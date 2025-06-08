#!/usr/bin/env python3
"""
Image Registration GUI - Avvio Interfaccia Grafica

Interfaccia grafica per la registrazione di immagini multispettrali
con supporto per fotocamere MicaSense RedEdge (5 bande).

Uso:
    python3 run_gui.py

Requisiti:
    - Python 3.8+
    - tkinter (incluso in Python)
    - numpy
    - opencv-python
    - scikit-image
    - tifffile
    - matplotlib

Installazione dipendenze:
    pip install numpy opencv-python scikit-image tifffile matplotlib
"""

import sys
import os

def check_dependencies():
    """Verifica che tutte le dipendenze siano installate"""
    missing_deps = []
    warnings = []

    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")

    try:
        import cv2
    except ImportError:
        missing_deps.append("opencv-python")

    try:
        import skimage
    except ImportError:
        missing_deps.append("scikit-image")

    try:
        import tifffile
    except ImportError:
        missing_deps.append("tifffile")

    try:
        import matplotlib
    except ImportError:
        missing_deps.append("matplotlib")

    try:
        import tkinter
    except ImportError:
        missing_deps.append("python3-tk")

    # Verifica imagecodecs (critico per file TIFF compressi)
    try:
        import imagecodecs
    except ImportError:
        warnings.append("imagecodecs - necessario per file TIFF compressi (LZW, DEFLATE)")

    # Verifica rasterio (per metadati geospaziali)
    try:
        import rasterio
    except ImportError:
        warnings.append("rasterio - necessario per metadati geospaziali")

    # Verifica packaging (per controllo versioni)
    try:
        import packaging
    except ImportError:
        warnings.append("packaging - necessario per controllo versioni")

    return missing_deps, warnings

def main():
    """Avvia l'interfaccia grafica"""
    print("🚀 Image Registration GUI")
    print("=" * 40)

    # Verifica dipendenze
    missing, warnings = check_dependencies()

    if missing:
        print("❌ Dipendenze mancanti:")
        for dep in missing:
            print(f"   • {dep}")
        print("\n🔧 Installa le dipendenze:")
        print("   pip install -r requirements.txt")
        print("   # oppure:")
        print("   python3 install_dependencies.py")
        if "python3-tk" in missing:
            print("   sudo apt-get install python3-tk  # Linux")
            print("   brew install python-tk          # macOS")
        sys.exit(1)

    print("✅ Tutte le dipendenze sono installate")

    # Mostra avvisi per dipendenze opzionali
    if warnings:
        print("\n⚠️ Dipendenze opzionali mancanti:")
        for warning in warnings:
            print(f"   • {warning}")
        print("\n💡 Per funzionalità complete installa:")
        print("   pip install imagecodecs rasterio packaging")
        print("   # oppure:")
        print("   python3 install_dependencies.py")
    
    # Aggiungi path corrente
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    try:
        # Importa e avvia GUI
        from image_registration.gui.main_window import launch_gui
        print("🎯 Avvio interfaccia grafica...")
        launch_gui()
        
    except ImportError as e:
        print(f"❌ Errore import: {e}")
        print("🔧 Verifica che il modulo image_registration sia nel path corretto")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Errore avvio: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
