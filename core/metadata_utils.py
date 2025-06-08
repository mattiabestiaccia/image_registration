"""
Module for managing geospatial metadata during registration
"""

import numpy as np
import rasterio
from rasterio.transform import Affine
from rasterio.crs import CRS
from typing import Dict, List, Optional, Tuple, Any
import logging
import os
from pathlib import Path


class MetadataManager:
    """
    Class for managing geospatial metadata during registration
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract all metadata from a geospatial TIFF file

        Args:
            file_path: File path

        Returns:
            Dictionary with all metadata
        """
        metadata = {}
        
        try:
            with rasterio.open(file_path) as src:
                metadata = {
                    'crs': src.crs,
                    'transform': src.transform,
                    'width': src.width,
                    'height': src.height,
                    'count': src.count,
                    'dtype': src.dtypes[0] if src.dtypes else 'float32',
                    'nodata': src.nodata,
                    'compress': src.compression.value if src.compression else None,
                    'tiled': src.is_tiled,
                    'blockxsize': src.block_shapes[0][1] if src.block_shapes else None,
                    'blockysize': src.block_shapes[0][0] if src.block_shapes else None,
                    'tags': src.tags(),
                    'descriptions': src.descriptions,
                    'units': src.units,
                    'scales': src.scales,
                    'offsets': src.offsets,
                    'colorinterp': [ci.name for ci in src.colorinterp] if src.colorinterp else None,
                    'profile': src.profile.copy()
                }
                
                self.logger.info(f"Metadata estratti da {os.path.basename(file_path)}")
                self.logger.info(f"  CRS: {metadata['crs']}")
                self.logger.info(f"  Transform: {metadata['transform']}")
                self.logger.info(f"  Dimensioni: {metadata['width']}x{metadata['height']}")
                
        except Exception as e:
            self.logger.warning(f"Unable to extract metadata from {file_path}: {str(e)}")
            # Fallback: metadati minimi
            metadata = {
                'crs': None,
                'transform': None,
                'width': None,
                'height': None,
                'count': 1,
                'dtype': 'float32',
                'nodata': None,
                'compress': None,
                'tiled': False,
                'blockxsize': None,
                'blockysize': None,
                'tags': {},
                'descriptions': None,
                'units': None,
                'scales': None,
                'offsets': None,
                'colorinterp': None,
                'profile': {}
            }
        
        return metadata
    
    def load_image_with_metadata(self, file_path: str) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Carica un'immagine preservando i metadati

        Args:
            file_path: File path

        Returns:
            Tuple (immagine, metadati)
        """
        metadata = self.extract_metadata(file_path)

        try:
            with rasterio.open(file_path) as src:
                # Leggi la prima banda (assumiamo immagini single-band)
                image = src.read(1).astype(np.float32)
        except Exception as e:
            # Fallback con tifffile
            try:
                import tifffile
                image = tifffile.imread(file_path).astype(np.float32)
                if image.ndim == 3 and image.shape[2] == 1:
                    image = image.squeeze(axis=2)
            except Exception as e2:
                # Check for compression errors
                if "imagecodecs" in str(e2) or "COMPRESSION" in str(e2):
                    raise ImportError(
                        f"Errore caricamento {file_path}: {e2}\n"
                        "Installa imagecodecs per supportare file TIFF compressi:\n"
                        "pip install imagecodecs"
                    )
                else:
                    raise RuntimeError(
                        f"Impossibile caricare {file_path}:\n"
                        f"Errore rasterio: {e}\n"
                        f"Errore tifffile: {e2}"
                    )

        return image, metadata
    
    def update_transform_for_registration(self, original_transform: Affine, 
                                        registration_matrix: np.ndarray) -> Affine:
        """
        Aggiorna la geotrasformazione considerando la registrazione applicata
        
        Args:
            original_transform: Transformation originale
            registration_matrix: Matrice di registrazione 2x3
            
        Returns:
            Nuova trasformazione aggiornata
        """
        if original_transform is None or registration_matrix is None:
            return original_transform
        
        try:
            # Converti la matrice di registrazione in formato affine
            # registration_matrix è 2x3: [[a, b, tx], [c, d, ty]]
            a, b, tx = registration_matrix[0]
            c, d, ty = registration_matrix[1]
            
            # Crea trasformazione affine dalla registrazione
            reg_transform = Affine(a, b, tx, c, d, ty)
            
            # Combina con la trasformazione originale
            # La nuova trasformazione è: original * inverse(registration)
            # Perché la registrazione sposta i pixel, quindi dobbiamo compensare
            combined_transform = original_transform * ~reg_transform
            
            self.logger.debug(f"Transformation aggiornata: {combined_transform}")
            
            return combined_transform
            
        except Exception as e:
            self.logger.warning(f"Error nell'aggiornamento della trasformazione: {str(e)}")
            return original_transform
    
    def create_output_profile(self, reference_metadata: Dict[str, Any], 
                            num_bands: int, output_dtype: str = None) -> Dict[str, Any]:
        """
        Crea il profilo per il output file multibanda
        
        Args:
            reference_metadata: Metadata della banda di riferimento
            num_bands: Numero di bande nel output file
            output_dtype: Tipo di dato per l'output
            
        Returns:
            Profilo per rasterio
        """
        profile = reference_metadata['profile'].copy()
        
        # Aggiorna per multibanda
        profile.update({
            'count': num_bands,
            'dtype': output_dtype or reference_metadata['dtype'],
            'compress': 'lzw',  # Compressione efficiente
            'tiled': True,
            'blockxsize': 512,
            'blockysize': 512,
            'interleave': 'band'
        })
        
        # Mantieni metadati importanti
        if reference_metadata['crs']:
            profile['crs'] = reference_metadata['crs']
        if reference_metadata['transform']:
            profile['transform'] = reference_metadata['transform']
        if reference_metadata['nodata'] is not None:
            profile['nodata'] = reference_metadata['nodata']
        
        return profile
    
    def save_multiband_with_metadata(self, bands: List[np.ndarray], 
                                   output_path: str,
                                   reference_metadata: Dict[str, Any],
                                   band_descriptions: List[str] = None,
                                   registration_matrices: List[np.ndarray] = None) -> None:
        """
        Salva immagine multibanda preservando i metadati
        
        Args:
            bands: Lista delle bande registrate
            output_path: Percorso del output file
            reference_metadata: Metadata della banda di riferimento
            band_descriptions: Descrizioni per ogni banda
            registration_matrices: Matrici di registrazione applicate
        """
        try:
            # Crea profilo per l'output
            profile = self.create_output_profile(reference_metadata, len(bands))
            
            # Aggiorna trasformazione se necessario
            if registration_matrices and reference_metadata['transform']:
                # Usa la trasformazione della banda di riferimento (prima banda)
                if len(registration_matrices) > 0 and registration_matrices[0] is not None:
                    updated_transform = self.update_transform_for_registration(
                        reference_metadata['transform'], 
                        registration_matrices[0]
                    )
                    profile['transform'] = updated_transform
            
            # Salva il file
            with rasterio.open(output_path, 'w', **profile) as dst:
                # Scrivi ogni banda
                for i, band in enumerate(bands):
                    dst.write(band.astype(profile['dtype']), i + 1)
                
                # Aggiungi descrizioni delle bande
                if band_descriptions:
                    dst.descriptions = band_descriptions[:len(bands)]
                else:
                    dst.descriptions = [f"Band {i+1}" for i in range(len(bands))]
                
                # Copia tag originali e aggiungi informazioni sulla registrazione
                tags = reference_metadata['tags'].copy()
                tags.update({
                    'PROCESSING': 'Image Registration',
                    'SOFTWARE': 'Advanced Image Registration Module',
                    'BANDS_COUNT': str(len(bands)),
                    'REFERENCE_BAND': '1'
                })
                
                if registration_matrices:
                    for i, matrix in enumerate(registration_matrices):
                        if matrix is not None:
                            tags[f'REGISTRATION_MATRIX_BAND_{i+1}'] = str(matrix.tolist())
                
                dst.update_tags(**tags)
                
            self.logger.info(f"Multiband file saved with metadata: {output_path}")
            self.logger.info(f"  Bands: {len(bands)}")
            self.logger.info(f"  CRS preserved: {profile.get('crs', 'None')}")
            
        except Exception as e:
            self.logger.error(f"Error nel salvataggio con metadati: {str(e)}")
            # Fallback: salva senza metadati usando tifffile
            import tifffile
            multiband_image = np.stack(bands, axis=0)
            tifffile.imwrite(output_path, multiband_image, photometric='minisblack')
            self.logger.warning(f"Saved without geospatial metadata: {output_path}")
    
    def validate_spatial_consistency(self, metadata_list: List[Dict[str, Any]]) -> bool:
        """
        Valida che tutte le bande abbiano metadati spaziali consistenti
        
        Args:
            metadata_list: Lista dei metadati di tutte le bande
            
        Returns:
            True se i metadati sono consistenti
        """
        if not metadata_list:
            return False
        
        reference = metadata_list[0]
        
        for i, metadata in enumerate(metadata_list[1:], 1):
            # Controlla CRS
            if metadata['crs'] != reference['crs']:
                self.logger.warning(f"CRS diverso nella banda {i+1}: {metadata['crs']} vs {reference['crs']}")
                return False
            
            # Controlla dimensioni
            if (metadata['width'] != reference['width'] or 
                metadata['height'] != reference['height']):
                self.logger.warning(f"Dimensioni diverse nella banda {i+1}")
                return False
            
            # Controlla trasformazione (con tolleranza per piccole differenze)
            if metadata['transform'] and reference['transform']:
                for j in range(6):
                    if abs(metadata['transform'][j] - reference['transform'][j]) > 1e-10:
                        self.logger.warning(f"Transformation diversa nella banda {i+1}")
                        return False
        
        self.logger.info(f"Metadata spaziali consistenti tra tutte le bande")
        return True
