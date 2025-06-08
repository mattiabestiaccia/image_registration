#!/usr/bin/env python3
"""
Script per installare automaticamente tutte le dipendenze necessarie
per il modulo image_registration, incluso imagecodecs per file TIFF compressi
"""

import subprocess
import sys
import os

def check_pip():
    """Verifica che pip sia disponibile"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        print("❌ pip non disponibile")
        return False

def install_package(package_name):
    """Installa un singolo pacchetto"""
    try:
        print(f"📦 Installazione {package_name}...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package_name
        ], check=True, capture_output=True, text=True)
        print(f"✅ {package_name} installato")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Errore installazione {package_name}:")
        print(f"   {e.stderr}")
        return False

def install_from_requirements():
    """Installa da requirements.txt"""
    requirements_file = "requirements.txt"
    
    if not os.path.exists(requirements_file):
        print(f"❌ File {requirements_file} non trovato")
        return False
    
    try:
        print(f"📋 Installazione da {requirements_file}...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", requirements_file
        ], check=True, capture_output=True, text=True)
        print("✅ Dipendenze installate da requirements.txt")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Errore installazione da requirements:")
        print(f"   {e.stderr}")
        return False

def test_critical_imports():
    """Test degli import critici"""
    print("\n🧪 Test import critici:")
    
    critical_packages = [
        ("numpy", "numpy"),
        ("tifffile", "tifffile"),
        ("imagecodecs", "imagecodecs"),
        ("scikit-image", "skimage"),
        ("matplotlib", "matplotlib"),
        ("opencv-python", "cv2"),
        ("rasterio", "rasterio")
    ]
    
    all_ok = True
    
    for package_name, import_name in critical_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} - mancante")
            all_ok = False
    
    return all_ok

def test_imagecodecs_functionality():
    """Test specifico per imagecodecs"""
    print("\n🔧 Test funzionalità imagecodecs:")
    
    try:
        import imagecodecs
        import numpy as np
        import tifffile
        
        # Test compressione LZW
        test_data = np.random.randint(0, 1000, (50, 50), dtype=np.uint16)
        test_file = "test_lzw.tif"
        
        # Salva con LZW
        tifffile.imwrite(test_file, test_data, compression='lzw')
        print("✅ File LZW creato")
        
        # Carica
        loaded = tifffile.imread(test_file)
        print("✅ File LZW caricato")
        
        # Verifica
        if np.array_equal(test_data, loaded):
            print("✅ Integrità LZW verificata")
        else:
            print("❌ Dati LZW corrotti")
            return False
        
        # Cleanup
        os.remove(test_file)
        print("🗑️ File test rimosso")
        
        return True
        
    except Exception as e:
        print(f"❌ Test imagecodecs fallito: {e}")
        return False

def main():
    """Installazione principale"""
    print("🚀 Installazione Dipendenze Image Registration")
    print("=" * 60)
    
    # Verifica pip
    if not check_pip():
        print("Installa pip prima di continuare")
        return False
    
    print("✅ pip disponibile")
    
    # Aggiorna pip
    print("\n📦 Aggiornamento pip...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        print("✅ pip aggiornato")
    except:
        print("⚠️ Aggiornamento pip fallito (continuo comunque)")
    
    # Installa dipendenze critiche singolarmente
    critical_packages = [
        "numpy",
        "tifffile", 
        "imagecodecs",  # Questo è il pacchetto chiave!
        "scikit-image",
        "matplotlib",
        "opencv-python",
        "rasterio",
        "packaging"
    ]
    
    print("\n📦 Installazione pacchetti critici:")
    failed_packages = []
    
    for package in critical_packages:
        if not install_package(package):
            failed_packages.append(package)
    
    # Installa da requirements se esiste
    print("\n📋 Installazione da requirements.txt:")
    install_from_requirements()
    
    # Test finale
    print("\n" + "=" * 60)
    print("🧪 TEST FINALE:")
    
    imports_ok = test_critical_imports()
    imagecodecs_ok = test_imagecodecs_functionality()
    
    print("\n" + "=" * 60)
    print("📊 RISULTATI INSTALLAZIONE:")
    
    if imports_ok and imagecodecs_ok:
        print("🎉 INSTALLAZIONE COMPLETATA CON SUCCESSO!")
        print("✅ Tutte le dipendenze sono disponibili")
        print("✅ imagecodecs funziona correttamente")
        print("💡 Il modulo può ora caricare file TIFF compressi")
        
        if failed_packages:
            print(f"\n⚠️ Pacchetti con problemi: {failed_packages}")
            print("   (potrebbero essere stati installati da requirements.txt)")
        
    else:
        print("❌ INSTALLAZIONE INCOMPLETA")
        if failed_packages:
            print(f"   Pacchetti falliti: {failed_packages}")
        
        print("\n🔧 RISOLUZIONE PROBLEMI:")
        print("1. Verifica connessione internet")
        print("2. Aggiorna pip: python -m pip install --upgrade pip")
        print("3. Installa manualmente: pip install imagecodecs")
        print("4. Su sistemi Linux, potrebbe servire: apt-get install libtiff-dev")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
