"""
Modulo di utilità per la registrazione di immagini multibanda
"""

import os
import glob
import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import numpy as np
import tifffile
from PIL import Image
from metadata_utils import MetadataManager


def find_image_groups(input_path: str) -> Dict[str, List[str]]:
    """
    Trova e raggruppa le immagini per base name (IMG_xxxx_1.tif, IMG_xxxx_2.tif, etc.)
    
    Args:
        input_path: Percorso della cartella o lista di file
        
    Returns:
        Dizionario con base_name come chiave e lista di percorsi file come valore
    """
    if os.path.isfile(input_path):
        # Se è un singolo file, assumiamo che sia parte di un gruppo
        base_dir = os.path.dirname(input_path)
        filename = os.path.basename(input_path)
        base_name = extract_base_name(filename)
        if base_name:
            pattern = os.path.join(base_dir, f"{base_name}_*.tif")
            files = sorted(glob.glob(pattern))
            return {base_name: files}
        return {}
    
    elif os.path.isdir(input_path):
        # Cerca tutti i file .tif nella cartella
        pattern = os.path.join(input_path, "IMG_*_*.tif")
        all_files = glob.glob(pattern)
        
        groups = {}
        for file_path in all_files:
            filename = os.path.basename(file_path)
            base_name = extract_base_name(filename)
            if base_name:
                if base_name not in groups:
                    groups[base_name] = []
                groups[base_name].append(file_path)
        
        # Ordina i file in ogni gruppo
        for base_name in groups:
            groups[base_name] = sorted(groups[base_name])
            
        return groups
    
    return {}


def extract_base_name(filename: str) -> Optional[str]:
    """
    Estrae il nome base da un filename tipo IMG_xxxx_1.tif
    
    Args:
        filename: Nome del file
        
    Returns:
        Nome base (es. IMG_1234) o None se non corrisponde al pattern
    """
    pattern = r'(IMG_\d+)_\d+\.tif'
    match = re.match(pattern, filename)
    if match:
        return match.group(1)
    return None


def load_image_band(file_path: str) -> np.ndarray:
    """
    Carica una singola banda da file TIFF (versione legacy senza metadati)

    Args:
        file_path: Percorso del file

    Returns:
        Array numpy dell'immagine
    """
    try:
        # Prova prima con tifffile
        img = tifffile.imread(file_path)
        if img.ndim == 3 and img.shape[2] == 1:
            img = img.squeeze(axis=2)
        return img.astype(np.float32)
    except:
        # Fallback con PIL
        img = Image.open(file_path)
        img_array = np.array(img).astype(np.float32)
        if img_array.ndim == 3 and img_array.shape[2] == 1:
            img_array = img_array.squeeze(axis=2)
        return img_array


def load_image_band_with_metadata(file_path: str) -> Tuple[np.ndarray, Dict]:
    """
    Carica una singola banda da file TIFF preservando i metadati

    Args:
        file_path: Percorso del file

    Returns:
        Tuple (array numpy dell'immagine, metadati)
    """
    metadata_manager = MetadataManager()
    return metadata_manager.load_image_with_metadata(file_path)


def save_multiband_tiff(bands: List[np.ndarray], output_path: str) -> None:
    """
    Salva multiple bande in un singolo file TIFF (versione legacy senza metadati)

    Args:
        bands: Lista di array numpy rappresentanti le bande
        output_path: Percorso del file di output
    """
    # Stack delle bande lungo l'asse 0 (primo asse)
    multiband_image = np.stack(bands, axis=0)

    # Salva usando tifffile
    tifffile.imwrite(output_path, multiband_image, photometric='minisblack')


def save_multiband_tiff_with_metadata(bands: List[np.ndarray],
                                    output_path: str,
                                    reference_metadata: Dict,
                                    band_descriptions: List[str] = None,
                                    registration_matrices: List[np.ndarray] = None) -> None:
    """
    Salva multiple bande in un singolo file TIFF preservando i metadati

    Args:
        bands: Lista di array numpy rappresentanti le bande
        output_path: Percorso del file di output
        reference_metadata: Metadati della banda di riferimento
        band_descriptions: Descrizioni per ogni banda
        registration_matrices: Matrici di registrazione applicate
    """
    metadata_manager = MetadataManager()
    metadata_manager.save_multiband_with_metadata(
        bands, output_path, reference_metadata,
        band_descriptions, registration_matrices
    )


def validate_image_group(file_paths: List[str]) -> bool:
    """
    Valida che un gruppo di immagini sia completo (5 bande)
    
    Args:
        file_paths: Lista dei percorsi dei file
        
    Returns:
        True se il gruppo è valido
    """
    if len(file_paths) != 5:
        return False
    
    # Verifica che tutti i file esistano
    for path in file_paths:
        if not os.path.exists(path):
            return False
    
    # Verifica che i numeri delle bande siano 1,2,3,4,5
    band_numbers = []
    for path in file_paths:
        filename = os.path.basename(path)
        match = re.search(r'_(\d+)\.tif$', filename)
        if match:
            band_numbers.append(int(match.group(1)))
    
    expected_bands = {1, 2, 3, 4, 5}
    return set(band_numbers) == expected_bands


def create_output_filename(base_name: str, output_dir: str) -> str:
    """
    Crea il nome del file di output

    Args:
        base_name: Nome base (es. IMG_1234)
        output_dir: Cartella di output

    Returns:
        Percorso completo del file di output
    """
    output_filename = f"{base_name}_registered.tif"
    return os.path.join(output_dir, output_filename)


def check_already_processed(base_name: str, output_dir: str) -> bool:
    """
    Controlla se un gruppo di immagini è già stato processato

    Args:
        base_name: Nome base del gruppo (es. IMG_1234)
        output_dir: Cartella di output

    Returns:
        True se il file di output esiste già
    """
    output_path = create_output_filename(base_name, output_dir)
    return os.path.exists(output_path)


def find_processed_groups(output_dir: str) -> set:
    """
    Trova tutti i gruppi già processati nella cartella di output

    Args:
        output_dir: Cartella di output

    Returns:
        Set dei nomi base già processati
    """
    if not os.path.exists(output_dir):
        return set()

    processed = set()
    pattern = os.path.join(output_dir, "*_registered.tif")

    for file_path in glob.glob(pattern):
        filename = os.path.basename(file_path)
        # Estrai il nome base da "IMG_xxxx_registered.tif"
        match = re.match(r'(.+)_registered\.tif$', filename)
        if match:
            base_name = match.group(1)
            processed.add(base_name)

    return processed


def get_resume_info(input_groups: Dict[str, List[str]], output_dir: str) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """
    Separa i gruppi da processare da quelli già completati

    Args:
        input_groups: Dizionario dei gruppi di input
        output_dir: Cartella di output

    Returns:
        Tuple (gruppi_da_processare, gruppi_già_completati)
    """
    processed_groups = find_processed_groups(output_dir)

    to_process = {}
    already_done = {}

    for base_name, file_paths in input_groups.items():
        if base_name in processed_groups:
            already_done[base_name] = file_paths
        else:
            to_process[base_name] = file_paths

    return to_process, already_done
