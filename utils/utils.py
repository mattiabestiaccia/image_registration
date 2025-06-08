"""
Utility module for multiband image registration
"""

import os
import glob
import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import numpy as np
import tifffile
from PIL import Image
try:
    from ..core.metadata_utils import MetadataManager
except ImportError:
    try:
        from core.metadata_utils import MetadataManager
    except ImportError:
        try:
            from metadata_utils import MetadataManager
        except ImportError:
            # Fallback: crea una classe dummy se MetadataManager non è disponibile
            class MetadataManager:
                def load_image_with_metadata(self, file_path):
                    img = tifffile.imread(file_path)
                    if img.ndim == 3 and img.shape[2] == 1:
                        img = img.squeeze(axis=2)
                    return img.astype(np.float32), {}

                def save_multiband_with_metadata(self, bands, output_path, reference_metadata,
                                               band_descriptions=None, registration_matrices=None):
                    multiband_image = np.stack(bands, axis=0)
                    tifffile.imwrite(output_path, multiband_image, photometric='minisblack')


def find_image_groups(input_path: str) -> Dict[str, List[str]]:
    """
    Find and group images by base name (IMG_xxxx_1.tif, IMG_xxxx_2.tif, etc.)

    Args:
        input_path: Path to folder or list of files

    Returns:
        Dictionary with base_name as key and list of file paths as value
    """
    if os.path.isfile(input_path):
        # If it's a single file, assume it's part of a group
        base_dir = os.path.dirname(input_path)
        filename = os.path.basename(input_path)
        base_name = extract_base_name(filename)
        if base_name:
            pattern = os.path.join(base_dir, f"{base_name}_*.tif")
            files = sorted(glob.glob(pattern))
            return {base_name: files}
        return {}

    elif os.path.isdir(input_path):
        # Search for all .tif files in the folder
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

        # Sort files in each group
        for base_name in groups:
            groups[base_name] = sorted(groups[base_name])

        return groups
    
    return {}


def extract_base_name(filename: str) -> Optional[str]:
    """
    Extract base name from filename like IMG_xxxx_1.tif

    Args:
        filename: File name

    Returns:
        Base name (e.g. IMG_1234) or None if doesn't match pattern
    """
    pattern = r'(IMG_\d+)_\d+\.tif'
    match = re.match(pattern, filename)
    if match:
        return match.group(1)
    return None


def load_image_band(file_path: str) -> np.ndarray:
    """
    Load a single band from TIFF file (legacy version without metadata)

    Args:
        file_path: File path

    Returns:
        Numpy array of the image
    """
    try:
        # Try with tifffile first
        img = tifffile.imread(file_path)
        if img.ndim == 3 and img.shape[2] == 1:
            img = img.squeeze(axis=2)
        return img.astype(np.float32)
    except Exception as e:
        # Check for specific compression errors
        if "imagecodecs" in str(e) or "COMPRESSION" in str(e):
            raise ImportError(
                f"Errore caricamento {file_path}: {e}\n"
                "Installa imagecodecs per supportare file TIFF compressi:\n"
                "pip install imagecodecs"
            )

        # Fallback with PIL for other errors
        try:
            img = Image.open(file_path)
            img_array = np.array(img).astype(np.float32)
            if img_array.ndim == 3 and img_array.shape[2] == 1:
                img_array = img_array.squeeze(axis=2)
            return img_array
        except Exception as e2:
            raise RuntimeError(
                f"Impossibile caricare {file_path}:\n"
                f"Errore tifffile: {e}\n"
                f"Errore PIL: {e2}"
            )


def load_image_band_with_metadata(file_path: str) -> Tuple[np.ndarray, Dict]:
    """
    Load a single band from TIFF file preserving metadata

    Args:
        file_path: File path

    Returns:
        Tuple (numpy array of image, metadata)
    """
    metadata_manager = MetadataManager()
    return metadata_manager.load_image_with_metadata(file_path)


def save_multiband_tiff(bands: List[np.ndarray], output_path: str) -> None:
    """
    Save multiple bands to a single TIFF file (legacy version without metadata)

    Args:
        bands: List of numpy arrays representing bands
        output_path: Output file path
    """
    # Stack bands along axis 0 (first axis)
    multiband_image = np.stack(bands, axis=0)

    # Save using tifffile
    tifffile.imwrite(output_path, multiband_image, photometric='minisblack')


def save_multiband_tiff_with_metadata(bands: List[np.ndarray],
                                    output_path: str,
                                    reference_metadata: Dict,
                                    band_descriptions: List[str] = None,
                                    registration_matrices: List[np.ndarray] = None) -> None:
    """
    Save multiple bands to a single TIFF file preserving metadata

    Args:
        bands: List of numpy arrays representing bands
        output_path: Output file path
        reference_metadata: Reference band metadata
        band_descriptions: Descriptions for each band
        registration_matrices: Applied registration matrices
    """
    metadata_manager = MetadataManager()
    metadata_manager.save_multiband_with_metadata(
        bands, output_path, reference_metadata,
        band_descriptions, registration_matrices
    )


def validate_image_group(file_paths: List[str]) -> bool:
    """
    Validate that an image group is complete (5 bands)

    Args:
        file_paths: List of file paths

    Returns:
        True if the group is valid
    """
    if len(file_paths) != 5:
        return False

    # Verify that all files exist
    for path in file_paths:
        if not os.path.exists(path):
            return False

    # Verify that band numbers are 1,2,3,4,5
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
    Create output file name

    Args:
        base_name: Base name (e.g. IMG_1234)
        output_dir: Output directory

    Returns:
        Complete output file path
    """
    output_filename = f"{base_name}_registered.tif"
    return os.path.join(output_dir, output_filename)


def check_already_processed(base_name: str, output_dir: str) -> bool:
    """
    Check if an image group has already been processed

    Args:
        base_name: Group base name (e.g. IMG_1234)
        output_dir: Output directory

    Returns:
        True if output file already exists
    """
    output_path = create_output_filename(base_name, output_dir)
    return os.path.exists(output_path)


def find_processed_groups(output_dir: str) -> set:
    """
    Find all groups already processed in the output directory

    Args:
        output_dir: Output directory

    Returns:
        Set of base names already processed
    """
    if not os.path.exists(output_dir):
        return set()

    processed = set()
    pattern = os.path.join(output_dir, "*_registered.tif")

    for file_path in glob.glob(pattern):
        filename = os.path.basename(file_path)
        # Extract base name from "IMG_xxxx_registered.tif"
        match = re.match(r'(.+)_registered\.tif$', filename)
        if match:
            base_name = match.group(1)
            processed.add(base_name)

    return processed


def get_resume_info(input_groups: Dict[str, List[str]], output_dir: str) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """
    Separate groups to process from those already completed

    Args:
        input_groups: Dictionary of input groups
        output_dir: Output directory

    Returns:
        Tuple (groups_to_process, groups_already_completed)
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
