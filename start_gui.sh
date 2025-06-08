#!/bin/bash
# Script di avvio per Image Registration GUI
# Attiva automaticamente l'ambiente virtuale e avvia l'interfaccia

echo "🚀 Image Registration GUI - Avvio con ambiente virtuale"
echo "=" * 60

# Verifica che l'ambiente virtuale esista
if [ ! -d "venv_registration" ]; then
    echo "❌ Ambiente virtuale non trovato!"
    echo "🔧 Crea l'ambiente virtuale con:"
    echo "   python3 -m venv venv_registration"
    echo "   source venv_registration/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Attiva ambiente virtuale
echo "🔧 Attivazione ambiente virtuale..."
source venv_registration/bin/activate

# Verifica che le dipendenze siano installate
echo "🔍 Verifica dipendenze..."
python3 -c "import numpy, cv2, skimage, tifffile, matplotlib, tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Dipendenze mancanti!"
    echo "🔧 Installa le dipendenze con:"
    echo "   pip install -r requirements.txt"
    exit 1
fi

echo "✅ Ambiente pronto"
echo "🎯 Avvio interfaccia grafica..."

# Avvia GUI
python3 run_gui.py

echo "👋 Interfaccia chiusa"
