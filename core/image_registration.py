"""
Main module for multiband image registration using advanced SLIC
"""

import numpy as np
import cv2
from skimage.segmentation import slic
from skimage.feature import match_template, corner_harris, corner_peaks, ORB
from skimage.registration import phase_cross_correlation
from skimage.measure import ransac
from skimage.transform import AffineTransform, warp
from skimage.filters import gaussian
from skimage.exposure import match_histograms
from typing import List, Tuple, Optional, Dict
import logging
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

try:
    from ..utils.utils import (load_image_band, save_multiband_tiff, validate_image_group,
                      create_output_filename, load_image_band_with_metadata,
                      save_multiband_tiff_with_metadata)
    from .metadata_utils import MetadataManager
except ImportError:
    try:
        from utils.utils import (load_image_band, save_multiband_tiff, validate_image_group,
                          create_output_filename, load_image_band_with_metadata,
                          save_multiband_tiff_with_metadata)
        from metadata_utils import MetadataManager
    except ImportError:
        # Fallback per esecuzione diretta
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        sys.path.insert(0, parent_dir)

        from utils.utils import (load_image_band, save_multiband_tiff, validate_image_group,
                          create_output_filename, load_image_band_with_metadata,
                          save_multiband_tiff_with_metadata)
        from core.metadata_utils import MetadataManager


class ImageRegistration:
    """
    Advanced class for multiband image registration using SLIC,
    feature matching and robust affine transformations
    """

    def __init__(self, n_segments: int = 1000, compactness: float = 10.0,
                 sigma: float = 1.0, reference_band: int = 1,
                 registration_method: str = 'hybrid', preserve_metadata: bool = True):
        """
        Initialize advanced image registration

        Args:
            n_segments: Number of superpixels for SLIC
            compactness: Compactness parameter for SLIC
            sigma: Sigma for Gaussian filter pre-processing
            reference_band: Reference band (1-5)
            registration_method: 'slic', 'features', 'hybrid', 'phase'
            preserve_metadata: Whether to preserve geospatial metadata
        """
        self.n_segments = n_segments
        self.compactness = compactness
        self.sigma = sigma
        self.reference_band = reference_band - 1  # Convert to 0-based indexing
        self.registration_method = registration_method
        self.preserve_metadata = preserve_metadata

        # Parameters for feature detection
        self.orb = cv2.ORB_create(nfeatures=1000)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

        # Metadata manager
        self.metadata_manager = MetadataManager() if preserve_metadata else None

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def preprocess_image(self, image: np.ndarray, enhance_contrast: bool = True) -> np.ndarray:
        """
        Advanced image pre-processing

        Args:
            image: Input image
            enhance_contrast: Whether to apply contrast enhancement

        Returns:
            Pre-processed image
        """
        # Normalize to 0-1
        img_norm = (image - image.min()) / (image.max() - image.min() + 1e-8)

        # Contrast enhancement using CLAHE
        if enhance_contrast:
            img_uint8 = (img_norm * 255).astype(np.uint8)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            img_enhanced = clahe.apply(img_uint8)
            img_norm = img_enhanced.astype(np.float32) / 255.0

        # Apply Gaussian filter to reduce noise
        if self.sigma > 0:
            img_smooth = gaussian(img_norm, sigma=self.sigma, preserve_range=True)
        else:
            img_smooth = img_norm

        return img_smooth
    
    def compute_slic_segments(self, image: np.ndarray) -> np.ndarray:
        """
        Calcola i superpixel usando SLIC

        Args:
            image: Image di input

        Returns:
            Mappa dei segmenti
        """
        # Convert to uint8 for SLIC if necessary
        if image.dtype != np.uint8:
            img_uint8 = (image * 255).astype(np.uint8)
        else:
            img_uint8 = image

        # Apply SLIC
        segments = slic(img_uint8, n_segments=self.n_segments,
                       compactness=self.compactness, sigma=self.sigma,
                       start_label=1)

        return segments

    def extract_slic_features(self, image: np.ndarray, segments: np.ndarray) -> Dict:
        """
        Estrae features dai superpixel SLIC

        Args:
            image: Image di input
            segments: Mappa dei segmenti SLIC

        Returns:
            Dizionario con features per ogni segmento
        """
        features = {}
        unique_segments = np.unique(segments)

        for seg_id in unique_segments:
            mask = segments == seg_id
            if np.sum(mask) < 10:  # Ignora segmenti troppo piccoli
                continue

            # Calculate centroid
            y_coords, x_coords = np.where(mask)
            centroid = (np.mean(y_coords), np.mean(x_coords))

            # Calculate intensity statistics
            intensities = image[mask]
            mean_intensity = np.mean(intensities)
            std_intensity = np.std(intensities)

            # Calculate area and perimeter
            area = np.sum(mask)

            features[seg_id] = {
                'centroid': centroid,
                'mean_intensity': mean_intensity,
                'std_intensity': std_intensity,
                'area': area,
                'mask': mask
            }

        return features
    
    def detect_and_match_features(self, ref_img: np.ndarray, target_img: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Rileva e matcha features usando ORB

        Args:
            ref_img: Image di riferimento
            target_img: Image target

        Returns:
            Tuple di punti matched (ref_points, target_points)
        """
        # Converti a uint8
        ref_uint8 = (ref_img * 255).astype(np.uint8)
        target_uint8 = (target_img * 255).astype(np.uint8)

        # Rileva keypoints e descriptors
        kp1, des1 = self.orb.detectAndCompute(ref_uint8, None)
        kp2, des2 = self.orb.detectAndCompute(target_uint8, None)

        if des1 is None or des2 is None or len(des1) < 10 or len(des2) < 10:
            return np.array([]), np.array([])

        # Match features
        matches = self.matcher.match(des1, des2)
        matches = sorted(matches, key=lambda x: x.distance)

        # Estrai punti matched
        if len(matches) < 10:
            return np.array([]), np.array([])

        ref_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        target_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

        return ref_pts, target_pts

    def estimate_affine_transform(self, ref_points: np.ndarray, target_points: np.ndarray) -> Optional[np.ndarray]:
        """
        Stima trasformazione affine robusta usando RANSAC

        Args:
            ref_points: Punti di riferimento
            target_points: Punti target

        Returns:
            Matrice di trasformazione affine 2x3 o None
        """
        if len(ref_points) < 6 or len(target_points) < 6:
            return None

        try:
            # Usa RANSAC per stimare trasformazione robusta
            M, mask = cv2.estimateAffinePartial2D(
                target_points, ref_points,
                method=cv2.RANSAC,
                ransacReprojThreshold=3.0,
                maxIters=2000,
                confidence=0.99
            )

            # Verifica che ci siano abbastanza inliers
            if mask is not None and np.sum(mask) >= 6:
                return M
            else:
                return None

        except:
            return None
    
    def register_slic_based(self, ref_img: np.ndarray, target_img: np.ndarray) -> Optional[np.ndarray]:
        """
        Registration basata su matching di superpixel SLIC

        Args:
            ref_img: Image di riferimento
            target_img: Image target

        Returns:
            Matrice di trasformazione o None
        """
        # Calcola segmenti SLIC per entrambe le immagini
        ref_segments = self.compute_slic_segments(ref_img)
        target_segments = self.compute_slic_segments(target_img)

        # Estrai features dai segmenti
        ref_features = self.extract_slic_features(ref_img, ref_segments)
        target_features = self.extract_slic_features(target_img, target_segments)

        # Match segmenti basato su similarità
        matches = []
        for ref_id, ref_feat in ref_features.items():
            best_match = None
            best_score = float('inf')

            for target_id, target_feat in target_features.items():
                # Calcola distanza basata su intensità e area
                intensity_diff = abs(ref_feat['mean_intensity'] - target_feat['mean_intensity'])
                area_ratio = min(ref_feat['area'], target_feat['area']) / max(ref_feat['area'], target_feat['area'])

                score = intensity_diff + (1 - area_ratio)

                if score < best_score and score < 0.3:  # Soglia di similarità
                    best_score = score
                    best_match = target_id

            if best_match is not None:
                matches.append((ref_feat['centroid'], target_features[best_match]['centroid']))

        if len(matches) < 6:
            return None

        # Converti in formato per estimateAffinePartial2D
        ref_points = np.array([m[0] for m in matches], dtype=np.float32).reshape(-1, 1, 2)
        target_points = np.array([m[1] for m in matches], dtype=np.float32).reshape(-1, 1, 2)

        return self.estimate_affine_transform(ref_points, target_points)

    def estimate_phase_correlation_shift(self, reference: np.ndarray, target: np.ndarray) -> Tuple[float, float]:
        """
        Stima shift usando phase cross-correlation migliorata

        Args:
            reference: Image di riferimento
            target: Image da allineare

        Returns:
            Tuple (shift_y, shift_x)
        """
        try:
            # Usa phase cross-correlation con upsampling
            shift, _, _ = phase_cross_correlation(reference, target, upsample_factor=20)
            return shift[0], shift[1]
        except:
            # Fallback: cross-correlation con FFT
            ref_fft = np.fft.fft2(reference)
            target_fft = np.fft.fft2(target)

            cross_corr = np.fft.ifft2(ref_fft * np.conj(target_fft))
            cross_corr = np.fft.fftshift(cross_corr)

            # Trova il picco
            peak = np.unravel_index(np.argmax(np.abs(cross_corr)), cross_corr.shape)
            shift_y = peak[0] - reference.shape[0] // 2
            shift_x = peak[1] - reference.shape[1] // 2

            return float(shift_y), float(shift_x)

    def apply_transformation(self, image: np.ndarray, transform_matrix: np.ndarray) -> np.ndarray:
        """
        Applica trasformazione affine a un'immagine

        Args:
            image: Image di input
            transform_matrix: Matrice di trasformazione 2x3

        Returns:
            Image trasformata
        """
        if transform_matrix is None:
            return image

        transformed = cv2.warpAffine(
            image, transform_matrix,
            (image.shape[1], image.shape[0]),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT
        )

        return transformed
    
    def register_single_band(self, ref_img: np.ndarray, target_img: np.ndarray,
                           original_target: np.ndarray) -> Tuple[np.ndarray, str]:
        """
        Registra una singola banda usando il metodo specificato

        Args:
            ref_img: Image di riferimento pre-processata
            target_img: Image target pre-processata
            original_target: Image target originale

        Returns:
            Tuple (immagine registrata, metodo utilizzato)
        """
        transform_matrix = None
        method_used = "none"

        if self.registration_method in ['features', 'hybrid']:
            # Prova registrazione basata su features
            ref_pts, target_pts = self.detect_and_match_features(ref_img, target_img)
            if len(ref_pts) > 0:
                transform_matrix = self.estimate_affine_transform(ref_pts, target_pts)
                if transform_matrix is not None:
                    method_used = "features"

        if transform_matrix is None and self.registration_method in ['slic', 'hybrid']:
            # Prova registrazione basata su SLIC
            transform_matrix = self.register_slic_based(ref_img, target_img)
            if transform_matrix is not None:
                method_used = "slic"

        if transform_matrix is None:
            # Fallback: phase correlation per shift semplice
            shift_y, shift_x = self.estimate_phase_correlation_shift(ref_img, target_img)
            transform_matrix = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
            method_used = f"phase_shift({shift_y:.1f},{shift_x:.1f})"

        # Applica trasformazione all'immagine originale
        registered = self.apply_transformation(original_target, transform_matrix)

        return registered, method_used

    def register_bands(self, band_paths: List[str]) -> Tuple[List[np.ndarray], List[Dict], List[np.ndarray]]:
        """
        Registra un gruppo di 5 bande usando metodi avanzati

        Args:
            band_paths: Lista dei percorsi delle 5 bande

        Returns:
            Tuple (bande registrate, metadati, matrici di registrazione)
        """
        if not validate_image_group(band_paths):
            raise ValueError(f"Image group non valido: {band_paths}")

        self.logger.info(f"Loading di {len(band_paths)} bande...")

        # Load all bands con o senza metadati
        bands = []
        metadata_list = []

        if self.preserve_metadata:
            for path in band_paths:
                band, metadata = load_image_band_with_metadata(path)
                bands.append(band)
                metadata_list.append(metadata)

            # Valida consistenza metadati
            if self.metadata_manager:
                self.metadata_manager.validate_spatial_consistency(metadata_list)
        else:
            for path in band_paths:
                band = load_image_band(path)
                bands.append(band)
                metadata_list.append({})

        # Pre-processing con histogram matching per migliorare la coerenza
        processed_bands = []
        reference_band = self.preprocess_image(bands[self.reference_band], enhance_contrast=True)

        for i, band in enumerate(bands):
            if i == self.reference_band:
                processed = reference_band
            else:
                processed = self.preprocess_image(band, enhance_contrast=True)
                # Histogram matching verso la banda di riferimento
                try:
                    # Per immagini 2D (scala di grigi), verifica la versione di scikit-image
                    # e usa il parametro corretto
                    import skimage
                    from packaging import version

                    if version.parse(skimage.__version__) >= version.parse("0.19.0"):
                        # Versioni più recenti: usa channel_axis=None per immagini 2D
                        processed = match_histograms(processed, reference_band, channel_axis=None)
                    else:
                        # Versioni più vecchie: usa multichannel=False
                        processed = match_histograms(processed, reference_band, multichannel=False)
                except Exception as e:
                    # Se fallisce, usa l'immagine processata normale
                    self.logger.warning(f"Histogram matching fallito per banda {i+1}: {e}")
                    pass

            processed_bands.append(processed)
            self.logger.info(f"Pre-processing band {i+1} completed")

        self.logger.info(f"Using band {self.reference_band + 1} as reference")
        self.logger.info(f"Method di registrazione: {self.registration_method}")

        # Register each band to reference
        registered_bands = []
        registration_matrices = []

        for i, processed_band in enumerate(processed_bands):
            if i == self.reference_band:
                # Reference band remains unchanged
                registered_bands.append(bands[i])
                registration_matrices.append(None)  # Nessuna trasformazione
                self.logger.info(f"Band {i+1}: reference (no transformation)")
            else:
                # Registra la banda
                registered, method = self.register_single_band(
                    reference_band, processed_band, bands[i]
                )
                registered_bands.append(registered)

                # Estrai la matrice di registrazione per i metadati
                # Questo è un placeholder - dovresti modificare register_single_band
                # per restituire anche la matrice di trasformazione
                registration_matrices.append(None)  # TODO: implementare estrazione matrice

                self.logger.info(f"Band {i+1}: registered using {method}")

        return registered_bands, metadata_list, registration_matrices
    
    def process_image_group(self, band_paths: List[str], output_path: str) -> bool:
        """
        Processa un singolo image group

        Args:
            band_paths: Lista dei percorsi delle bande
            output_path: Percorso del output file

        Returns:
            True se il processing è successful
        """
        try:
            # Register bands
            registered_bands, metadata_list, registration_matrices = self.register_bands(band_paths)

            # Save result con o senza metadati
            if self.preserve_metadata and metadata_list and metadata_list[self.reference_band]:
                # Salva con metadati preservati
                band_descriptions = [f"Band {i+1} registrata" for i in range(len(registered_bands))]
                band_descriptions[self.reference_band] = f"Band {self.reference_band+1} (riferimento)"

                save_multiband_tiff_with_metadata(
                    registered_bands,
                    output_path,
                    metadata_list[self.reference_band],  # Usa metadati della banda di riferimento
                    band_descriptions,
                    registration_matrices
                )
                self.logger.info(f"Salvato con metadati preservati: {output_path}")
            else:
                # Salva senza metadati (fallback)
                save_multiband_tiff(registered_bands, output_path)
                self.logger.info(f"Salvato senza metadati: {output_path}")

            return True

        except Exception as e:
            self.logger.error(f"Error nel processing di {band_paths}: {str(e)}")
            return False
