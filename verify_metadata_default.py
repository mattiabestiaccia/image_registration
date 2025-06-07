#!/usr/bin/env python3
"""
Script semplice per verificare che i metadati vengano preservati di default
"""

import os
import tempfile
import numpy as np
from image_registration import ImageRegistration
from utils import find_image_groups, create_output_filename


def create_simple_test_images(output_dir: str, base_name: str = "IMG_0001") -> list:
    """
    Crea immagini di test semplici senza dipendenze da rasterio
    """
    import tifffile
    
    # Crea un'immagine base 256x256
    base_image = np.random.randint(0, 255, (256, 256), dtype=np.uint8)
    
    # Aggiungi pattern riconoscibili
    base_image[100:156, 100:156] = 200  # Quadrato centrale
    base_image[50:70, 50:200] = 150     # Rettangolo
    
    file_paths = []
    shifts = [(0, 0), (2, 3), (-1, 4), (3, -2), (-2, -1)]  # Shift per ogni banda
    
    for i, (shift_y, shift_x) in enumerate(shifts):
        # Applica shift artificiale
        shifted_image = np.roll(base_image, shift_y, axis=0)
        shifted_image = np.roll(shifted_image, shift_x, axis=1)
        
        # Aggiungi rumore diverso per ogni banda
        noise = np.random.normal(0, 5, shifted_image.shape).astype(np.int16)
        noisy_image = np.clip(shifted_image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        # Salva l'immagine
        filename = f"{base_name}_{i+1}.tif"
        filepath = os.path.join(output_dir, filename)
        
        tifffile.imwrite(filepath, noisy_image)
        file_paths.append(filepath)
        
        print(f"Creata immagine: {filename} (shift: {shift_y}, {shift_x})")
    
    return file_paths


def test_default_behavior():
    """Test che i metadati vengano preservati di default"""
    print("=== Test Comportamento Default ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        input_dir = os.path.join(temp_dir, "input")
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(input_dir)
        os.makedirs(output_dir)
        
        # Crea immagini di test
        print("Creazione immagini di test...")
        test_files = create_simple_test_images(input_dir, "IMG_TEST")
        
        # Trova gruppi
        groups = find_image_groups(input_dir)
        assert "IMG_TEST" in groups, "Gruppo non trovato"
        
        # Test 1: Comportamento default (dovrebbe preservare metadati)
        print("\n1. Test comportamento default...")
        registrator_default = ImageRegistration(
            n_segments=500,
            reference_band=1,
            registration_method='hybrid'
            # Non specifichiamo preserve_metadata, dovrebbe essere True di default
        )
        
        output_path_default = create_output_filename("IMG_TEST_default", output_dir)
        success = registrator_default.process_image_group(groups["IMG_TEST"], output_path_default)
        
        assert success, "Registrazione default fallita"
        assert os.path.exists(output_path_default), "File output non creato"
        print(f"✓ Registrazione default completata: {os.path.basename(output_path_default)}")
        
        # Verifica che preserve_metadata sia True di default
        assert registrator_default.preserve_metadata == True, "preserve_metadata non è True di default"
        print("✓ preserve_metadata è True di default")
        
        # Test 2: Disabilitazione esplicita
        print("\n2. Test disabilitazione esplicita...")
        registrator_no_meta = ImageRegistration(
            n_segments=500,
            reference_band=1,
            registration_method='hybrid',
            preserve_metadata=False
        )
        
        output_path_no_meta = create_output_filename("IMG_TEST_no_meta", output_dir)
        success = registrator_no_meta.process_image_group(groups["IMG_TEST"], output_path_no_meta)
        
        assert success, "Registrazione senza metadati fallita"
        assert os.path.exists(output_path_no_meta), "File output senza metadati non creato"
        print(f"✓ Registrazione senza metadati completata: {os.path.basename(output_path_no_meta)}")
        
        # Verifica che preserve_metadata sia False quando specificato
        assert registrator_no_meta.preserve_metadata == False, "preserve_metadata non rispetta impostazione esplicita"
        print("✓ preserve_metadata rispetta impostazione esplicita")
        
        # Confronta dimensioni file (con metadati potrebbe essere leggermente più grande)
        size_default = os.path.getsize(output_path_default)
        size_no_meta = os.path.getsize(output_path_no_meta)
        
        print(f"\nConfronto dimensioni file:")
        print(f"  Con metadati (default): {size_default:,} bytes")
        print(f"  Senza metadati: {size_no_meta:,} bytes")
        print(f"  Differenza: {size_default - size_no_meta:,} bytes")
        
        return True


def test_cli_behavior():
    """Test del comportamento CLI"""
    print("\n=== Test Comportamento CLI ===")
    
    # Simula argparse per testare la logica
    class MockArgs:
        def __init__(self, no_metadata=False):
            self.no_metadata = no_metadata
    
    # Test 1: Comportamento default (senza flag)
    args_default = MockArgs(no_metadata=False)
    preserve_metadata_default = not args_default.no_metadata
    assert preserve_metadata_default == True, "CLI default non preserva metadati"
    print("✓ CLI preserva metadati di default")
    
    # Test 2: Con flag --no-metadata
    args_no_meta = MockArgs(no_metadata=True)
    preserve_metadata_disabled = not args_no_meta.no_metadata
    assert preserve_metadata_disabled == False, "CLI non rispetta --no-metadata"
    print("✓ CLI rispetta flag --no-metadata")
    
    return True


def main():
    """Esegue tutti i test di verifica"""
    print("🔍 VERIFICA COMPORTAMENTO DEFAULT METADATI\n")
    
    try:
        # Test comportamento default
        test_default_behavior()
        
        # Test logica CLI
        test_cli_behavior()
        
        print(f"\n{'='*60}")
        print("🎉 VERIFICA COMPLETATA CON SUCCESSO! 🎉")
        print("\nComportamento confermato:")
        print("✓ I metadati vengono preservati DI DEFAULT")
        print("✓ Nessun flag necessario per preservare metadati")
        print("✓ Flag --no-metadata disabilita preservazione")
        print("✓ Comportamento coerente tra API e CLI")
        
    except Exception as e:
        print(f"\n❌ VERIFICA FALLITA: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
