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
import tifffile
from fractions import Fraction


class MetadataManager:
    """
    Class for managing geospatial metadata during registration
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def gps_fraction_to_decimal(self, gps_coord):
        """
        Converte coordinate GPS dal formato frazione (gradi, minuti, secondi) al formato decimale.
        
        Args:
            gps_coord: Tupla di 3 valori (gradi, minuti, secondi) come frazioni o interi
            
        Returns:
            float: Coordinata in formato decimale
        """
        def parse_value(val):
            if isinstance(val, (int, float)):
                return float(val)
            elif isinstance(val, tuple) and len(val) == 2:
                return Fraction(val[0], val[1])
            else:
                return float(val)
        
        degrees = parse_value(gps_coord[0]) / 10000000  # Diviso per 10^7
        minutes = parse_value(gps_coord[1]) / 10000000  # Diviso per 10^7
        seconds = parse_value(gps_coord[2]) / 10000000  # Diviso per 10^7
        
        return float(degrees + minutes/60 + seconds/3600)
    
    def extract_gps_from_jpg(self, jpg_path: str) -> Dict[str, Any]:
        """
        Estrae le coordinate GPS da un file JPG usando EXIF data.
        
        Args:
            jpg_path: Percorso al file JPG
            
        Returns:
            dict: Dizionario con latitudine, longitudine e altitudine
        """
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS, GPSTAGS
            
            with Image.open(jpg_path) as img:
                exif_data = img._getexif()
                
                if not exif_data:
                    return {}
                
                gps_data = {}
                
                # Cerca i dati GPS nell'EXIF
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    
                    if tag == 'GPSInfo':
                        for gps_tag_id, gps_value in value.items():
                            gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                            
                            if gps_tag == 'GPSLatitude':
                                gps_data['latitude_raw'] = gps_value
                            elif gps_tag == 'GPSLatitudeRef':
                                gps_data['latitude_ref'] = gps_value
                            elif gps_tag == 'GPSLongitude':
                                gps_data['longitude_raw'] = gps_value
                            elif gps_tag == 'GPSLongitudeRef':
                                gps_data['longitude_ref'] = gps_value
                            elif gps_tag == 'GPSAltitude':
                                gps_data['altitude_raw'] = gps_value
                            elif gps_tag == 'GPSAltitudeRef':
                                gps_data['altitude_ref'] = gps_value
                
                # Converti i dati GPS in formato decimale
                result = {}
                
                if 'latitude_raw' in gps_data and 'latitude_ref' in gps_data:
                    lat_decimal = self._convert_gps_coordinate(gps_data['latitude_raw'])
                    if gps_data['latitude_ref'] == 'S':
                        lat_decimal = -lat_decimal
                    result['latitude'] = lat_decimal
                    result['latitude_ref'] = gps_data['latitude_ref']
                
                if 'longitude_raw' in gps_data and 'longitude_ref' in gps_data:
                    lon_decimal = self._convert_gps_coordinate(gps_data['longitude_raw'])
                    if gps_data['longitude_ref'] == 'W':
                        lon_decimal = -lon_decimal
                    result['longitude'] = lon_decimal
                    result['longitude_ref'] = gps_data['longitude_ref']
                
                if 'altitude_raw' in gps_data:
                    altitude = float(gps_data['altitude_raw'])
                    if 'altitude_ref' in gps_data and gps_data['altitude_ref'] == 1:
                        altitude = -altitude
                    result['altitude'] = altitude
                
                if result:
                    self.logger.info(f"GPS coordinates extracted from JPG EXIF in {os.path.basename(jpg_path)}")
                    if 'latitude' in result and 'longitude' in result:
                        self.logger.info(f"  Lat: {result['latitude']:.8f}, Lon: {result['longitude']:.8f}")
                
                return result
                
        except Exception as e:
            self.logger.warning(f"Error extracting GPS from JPG {jpg_path}: {str(e)}")
            return {}
    
    def _convert_gps_coordinate(self, coord_tuple):
        """
        Converte coordinate GPS dal formato EXIF (gradi, minuti, secondi) al formato decimale.
        
        Args:
            coord_tuple: Tupla con (gradi, minuti, secondi) come frazioni
            
        Returns:
            float: Coordinata in formato decimale
        """
        degrees = float(coord_tuple[0])
        minutes = float(coord_tuple[1])
        seconds = float(coord_tuple[2])
        
        return degrees + minutes/60 + seconds/3600
    
    def extract_gps_coordinates(self, file_path: str) -> Dict[str, Any]:
        """
        Estrae le coordinate GPS da un file immagine (TIFF o JPG).
        Cerca prima nei tag rasterio, poi nei tag EXIF.
        
        Args:
            file_path: Percorso al file immagine
            
        Returns:
            dict: Dizionario con latitudine, longitudine e altitudine
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # For JPG files, use PIL/Pillow to extract EXIF data
        if file_ext in ['.jpg', '.jpeg']:
            return self.extract_gps_from_jpg(file_path)
        
        # Prima prova con rasterio (per file TIFF processati)
        try:
            with rasterio.open(file_path) as src:
                tags = src.tags()
                gps_data = {}
                
                # Cerca tag GPS nei metadati rasterio
                if 'GPS_LATITUDE' in tags:
                    gps_data['latitude'] = float(tags['GPS_LATITUDE'])
                    gps_data['latitude_ref'] = tags.get('GPS_LATITUDE_REF', 'N')
                
                if 'GPS_LONGITUDE' in tags:
                    gps_data['longitude'] = float(tags['GPS_LONGITUDE'])
                    gps_data['longitude_ref'] = tags.get('GPS_LONGITUDE_REF', 'E')
                
                if 'GPS_ALTITUDE' in tags:
                    gps_data['altitude'] = float(tags['GPS_ALTITUDE'])
                
                if 'GPS_DOP' in tags:
                    gps_data['dop'] = float(tags['GPS_DOP'])
                
                if gps_data:
                    self.logger.info(f"GPS coordinates extracted from rasterio tags in {os.path.basename(file_path)}")
                    if 'latitude' in gps_data and 'longitude' in gps_data:
                        self.logger.info(f"  Lat: {gps_data['latitude']:.8f}, Lon: {gps_data['longitude']:.8f}")
                    return gps_data
                    
        except Exception as e:
            self.logger.debug(f"Rasterio GPS extraction failed for {file_path}: {str(e)}")
        
        # Fallback: prova con tifffile (per file TIFF originali)
        try:
            with tifffile.TiffFile(file_path) as tif:
                page = tif.pages[0]
                
                # Cerca il tag GPS
                gps_tag = None
                for tag in page.tags:
                    if tag.name == 'GPSTag':
                        gps_tag = tag.value
                        break
                
                if not gps_tag:
                    return {}
                
                # Estrai i dati GPS
                gps_data = {}
                
                # Latitudine
                if 'GPSLatitude' in gps_tag and 'GPSLatitudeRef' in gps_tag:
                    lat_decimal = self.gps_fraction_to_decimal(gps_tag['GPSLatitude'])
                    if gps_tag['GPSLatitudeRef'] == 'S':
                        lat_decimal = -lat_decimal
                    gps_data['latitude'] = lat_decimal
                    gps_data['latitude_ref'] = gps_tag['GPSLatitudeRef']
                
                # Longitudine
                if 'GPSLongitude' in gps_tag and 'GPSLongitudeRef' in gps_tag:
                    lon_decimal = self.gps_fraction_to_decimal(gps_tag['GPSLongitude'])
                    if gps_tag['GPSLongitudeRef'] == 'W':
                        lon_decimal = -lon_decimal
                    gps_data['longitude'] = lon_decimal
                    gps_data['longitude_ref'] = gps_tag['GPSLongitudeRef']
                
                # Altitudine
                if 'GPSAltitude' in gps_tag:
                    alt_frac = gps_tag['GPSAltitude']
                    altitude = Fraction(alt_frac[0], alt_frac[1])
                    gps_data['altitude'] = float(altitude)
                    
                    # Riferimento altitudine (0 = sopra il livello del mare, 1 = sotto)
                    if 'GPSAltitudeRef' in gps_tag:
                        if gps_tag['GPSAltitudeRef'] == 1:
                            gps_data['altitude'] = -gps_data['altitude']
                
                # DOP (Dilution of Precision)
                if 'GPSDOP' in gps_tag:
                    dop = gps_tag['GPSDOP']
                    if dop[1] != 0:  # Evita divisione per zero
                        gps_data['dop'] = float(Fraction(dop[0], dop[1]))
                
                if gps_data:
                    self.logger.info(f"GPS coordinates extracted from EXIF tags in {os.path.basename(file_path)}")
                    if 'latitude' in gps_data and 'longitude' in gps_data:
                        self.logger.info(f"  Lat: {gps_data['latitude']:.8f}, Lon: {gps_data['longitude']:.8f}")
                
                return gps_data
                
        except Exception as e:
            self.logger.warning(f"Error extracting GPS from {file_path}: {str(e)}")
            return {}

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract all metadata from a geospatial image file (TIFF or JPG)

        Args:
            file_path: File path

        Returns:
            Dictionary with all metadata including GPS coordinates
        """
        metadata = {}
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # For JPG files, create minimal metadata structure
        if file_ext in ['.jpg', '.jpeg']:
            try:
                from PIL import Image
                with Image.open(file_path) as img:
                    width, height = img.size
                    metadata = {
                        'crs': None,
                        'transform': None,
                        'width': width,
                        'height': height,
                        'count': 1,
                        'dtype': 'uint8',
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
                        'profile': {
                            'driver': 'JPEG',
                            'width': width,
                            'height': height,
                            'count': 1,
                            'dtype': 'uint8'
                        }
                    }
                    self.logger.info(f"JPG metadata extracted from {os.path.basename(file_path)}")
                    self.logger.info(f"  Dimensions: {width}x{height}")
            except Exception as e:
                self.logger.warning(f"Unable to extract JPG metadata from {file_path}: {str(e)}")
                # Fallback minimal metadata
                metadata = {
                    'crs': None, 'transform': None, 'width': None, 'height': None,
                    'count': 1, 'dtype': 'uint8', 'nodata': None, 'compress': None,
                    'tiled': False, 'blockxsize': None, 'blockysize': None,
                    'tags': {}, 'descriptions': None, 'units': None,
                    'scales': None, 'offsets': None, 'colorinterp': None,
                    'profile': {'driver': 'JPEG', 'count': 1, 'dtype': 'uint8'}
                }
        else:
            # For TIFF files, use rasterio
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
        
        # Estrai coordinate GPS
        gps_data = self.extract_gps_coordinates(file_path)
        metadata['gps'] = gps_data
        
        return metadata
    
    def load_image_with_metadata(self, file_path: str) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Carica un'immagine preservando i metadati (supports TIFF and JPG)

        Args:
            file_path: File path

        Returns:
            Tuple (immagine, metadati)
        """
        metadata = self.extract_metadata(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()

        # For JPG files, use PIL/Pillow
        if file_ext in ['.jpg', '.jpeg']:
            try:
                from PIL import Image
                with Image.open(file_path) as img:
                    # Convert to grayscale if it's a color image (for consistency with multispectral workflow)
                    if img.mode in ['RGB', 'RGBA']:
                        img = img.convert('L')
                    image = np.array(img).astype(np.float32)
                    if image.ndim == 3 and image.shape[2] == 1:
                        image = image.squeeze(axis=2)
                return image, metadata
            except Exception as e:
                raise RuntimeError(f"Impossibile caricare JPG {file_path}: {e}")

        # For TIFF files, try rasterio first, then tifffile fallback
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
                
                # Preserva coordinate GPS se disponibili
                if 'gps' in reference_metadata and reference_metadata['gps']:
                    gps_data = reference_metadata['gps']
                    if 'latitude' in gps_data:
                        tags['GPS_LATITUDE'] = str(gps_data['latitude'])
                        tags['GPS_LATITUDE_REF'] = gps_data.get('latitude_ref', 'N')
                    if 'longitude' in gps_data:
                        tags['GPS_LONGITUDE'] = str(gps_data['longitude'])
                        tags['GPS_LONGITUDE_REF'] = gps_data.get('longitude_ref', 'E')
                    if 'altitude' in gps_data:
                        tags['GPS_ALTITUDE'] = str(gps_data['altitude'])
                    if 'dop' in gps_data:
                        tags['GPS_DOP'] = str(gps_data['dop'])
                
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
