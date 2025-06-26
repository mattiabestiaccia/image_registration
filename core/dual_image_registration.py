"""
Dual Image Registration - Registrazione tra due immagini singole di dimensioni diverse

Modulo specializzato per registrare due immagini singole con dimensioni e risoluzioni diverse,
tipicamente un'immagine termica più piccola e un'immagine RGB più grande.
"""

import numpy as np
import cv2
from skimage.feature import ORB, match_descriptors
from skimage.transform import AffineTransform, warp, resize
from skimage.measure import ransac
from skimage.registration import phase_cross_correlation
from skimage.filters import gaussian
from skimage.exposure import match_histograms, equalize_adapthist
from typing import Tuple, Optional, Dict, Any
import logging
import os
from PIL import Image
import matplotlib.pyplot as plt


class DualImageRegistration:
    """
    Classe per registrazione di due immagini singole di dimensioni diverse
    """
    
    def __init__(self, registration_method: str = 'hybrid', 
                 scale_factor_estimation: bool = True,
                 enhance_contrast: bool = True):
        """
        Inizializza il registratore per immagini duali
        
        Args:
            registration_method: 'features', 'phase', 'hybrid'
            scale_factor_estimation: Se stimare automaticamente il fattore di scala
            enhance_contrast: Se migliorare il contrasto prima della registrazione
        """
        self.registration_method = registration_method
        self.scale_factor_estimation = scale_factor_estimation
        self.enhance_contrast = enhance_contrast
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Parametri per feature detection
        self.orb = cv2.ORB_create(nfeatures=2000, scaleFactor=1.2, nlevels=8)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    
    def load_and_preprocess_image(self, file_path: str) -> np.ndarray:
        """
        Carica e preprocessa un'immagine
        
        Args:
            file_path: Percorso del file immagine
            
        Returns:
            Immagine preprocessata come array numpy
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext in ['.jpg', '.jpeg']:
                # Carica JPG con PIL
                with Image.open(file_path) as img:
                    if img.mode in ['RGB', 'RGBA']:
                        img = img.convert('L')  # Converti in grayscale
                    image = np.array(img).astype(np.float32)
            else:
                # Carica TIFF con OpenCV
                image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
                if image is None:
                    raise ValueError(f"Impossibile caricare {file_path}")
                image = image.astype(np.float32)
            
            # Normalizza
            image = (image - image.min()) / (image.max() - image.min() + 1e-8)
            
            # Migliora contrasto se richiesto
            if self.enhance_contrast:
                image = self._enhance_contrast(image)
            
            self.logger.info(f"Immagine caricata: {os.path.basename(file_path)} - Dimensioni: {image.shape}")
            return image
            
        except Exception as e:
            self.logger.error(f"Errore nel caricamento di {file_path}: {e}")
            raise
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Migliora il contrasto dell'immagine
        
        Args:
            image: Immagine di input normalizzata (0-1)
            
        Returns:
            Immagine con contrasto migliorato
        """
        try:
            # CLAHE (Contrast Limited Adaptive Histogram Equalization)
            img_uint8 = (image * 255).astype(np.uint8)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            enhanced = clahe.apply(img_uint8)
            return enhanced.astype(np.float32) / 255.0
        except:
            # Fallback: equalizzazione adattiva con scikit-image
            return equalize_adapthist(image, clip_limit=0.03)
    
    def estimate_scale_factor(self, small_image: np.ndarray, 
                            large_image: np.ndarray) -> float:
        """
        Stima il fattore di scala tra due immagini
        
        Args:
            small_image: Immagine più piccola
            large_image: Immagine più grande
            
        Returns:
            Fattore di scala stimato
        """
        # Calcola rapporti delle dimensioni
        height_ratio = large_image.shape[0] / small_image.shape[0]
        width_ratio = large_image.shape[1] / small_image.shape[1]
        
        # Usa il rapporto medio come stima iniziale
        initial_scale = (height_ratio + width_ratio) / 2
        
        if not self.scale_factor_estimation:
            return initial_scale
        
        # Prova diversi fattori di scala vicini alla stima iniziale
        scale_candidates = np.linspace(initial_scale * 0.7, initial_scale * 1.3, 10)
        best_scale = initial_scale
        best_score = 0
        
        for scale in scale_candidates:
            # Ridimensiona l'immagine piccola
            new_height = int(small_image.shape[0] * scale)
            new_width = int(small_image.shape[1] * scale)
            
            if new_height > large_image.shape[0] or new_width > large_image.shape[1]:
                continue
                
            resized_small = resize(small_image, (new_height, new_width), 
                                 anti_aliasing=True, preserve_range=True)
            
            # Calcola cross-correlation per valutare la qualità
            try:
                # Prendi una regione centrale dell'immagine grande
                center_y = large_image.shape[0] // 2
                center_x = large_image.shape[1] // 2
                half_h = new_height // 2
                half_w = new_width // 2
                
                roi = large_image[center_y-half_h:center_y+half_h,
                                center_x-half_w:center_x+half_w]
                
                if roi.shape == resized_small.shape:
                    correlation = np.corrcoef(roi.flatten(), resized_small.flatten())[0,1]
                    if not np.isnan(correlation) and correlation > best_score:
                        best_score = correlation
                        best_scale = scale
            except:
                continue
        
        self.logger.info(f"Fattore di scala stimato: {best_scale:.3f} (score: {best_score:.3f})")
        return best_scale
    
    def detect_and_match_features(self, ref_img: np.ndarray, 
                                target_img: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Rileva e matcha features tra due immagini
        
        Args:
            ref_img: Immagine di riferimento
            target_img: Immagine target
            
        Returns:
            Tuple di punti matched (ref_points, target_points)
        """
        # Converti a uint8 per ORB
        ref_uint8 = (ref_img * 255).astype(np.uint8)
        target_uint8 = (target_img * 255).astype(np.uint8)
        
        # Rileva keypoints e descriptors
        kp1, des1 = self.orb.detectAndCompute(ref_uint8, None)
        kp2, des2 = self.orb.detectAndCompute(target_uint8, None)
        
        if des1 is None or des2 is None or len(des1) < 10 or len(des2) < 10:
            self.logger.warning("Insufficienti features rilevate")
            return np.array([]), np.array([])
        
        # Match features
        matches = self.matcher.match(des1, des2)
        matches = sorted(matches, key=lambda x: x.distance)
        
        if len(matches) < 10:
            self.logger.warning("Insufficienti matches trovati")
            return np.array([]), np.array([])
        
        # Prendi i migliori matches
        good_matches = matches[:min(len(matches), 100)]
        
        ref_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches])
        target_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches])
        
        self.logger.info(f"Trovati {len(good_matches)} feature matches")
        return ref_pts, target_pts
    
    def estimate_transform_robust(self, ref_points: np.ndarray, 
                                target_points: np.ndarray) -> Optional[np.ndarray]:
        """
        Stima trasformazione robusta usando RANSAC
        
        Args:
            ref_points: Punti di riferimento
            target_points: Punti target
            
        Returns:
            Matrice di trasformazione o None
        """
        if len(ref_points) < 6 or len(target_points) < 6:
            return None
        
        try:
            # Usa RANSAC per stimare trasformazione robusta
            # Permetti scaling e rotation oltre a translation
            M, mask = cv2.estimateAffinePartial2D(
                target_points.reshape(-1, 1, 2),
                ref_points.reshape(-1, 1, 2),
                method=cv2.RANSAC,
                ransacReprojThreshold=5.0,  # Più permissivo per immagini diverse
                maxIters=3000,
                confidence=0.95
            )
            
            if mask is not None and np.sum(mask) >= 6:
                inlier_ratio = np.sum(mask) / len(mask)
                self.logger.info(f"Trasformazione stimata - Inliers: {np.sum(mask)}/{len(mask)} ({inlier_ratio:.2%})")
                return M
            else:
                self.logger.warning("Trasformazione non affidabile")
                return None
                
        except Exception as e:
            self.logger.error(f"Errore nella stima della trasformazione: {e}")
            return None
    
    def register_images(self, reference_path: str, 
                       target_path: str) -> Dict[str, Any]:
        """
        Registra due immagini singole
        
        Args:
            reference_path: Percorso immagine di riferimento (più grande)
            target_path: Percorso immagine target (più piccola)
            
        Returns:
            Dizionario con risultati della registrazione
        """
        try:
            # Carica immagini
            self.logger.info("Caricamento immagini...")
            ref_image = self.load_and_preprocess_image(reference_path)
            target_image = self.load_and_preprocess_image(target_path)
            
            # Determina quale è più piccola
            if (ref_image.shape[0] * ref_image.shape[1]) < (target_image.shape[0] * target_image.shape[1]):
                # Scambia se reference è più piccola
                ref_image, target_image = target_image, ref_image
                reference_path, target_path = target_path, reference_path
                self.logger.info("Scambiate immagini: reference ora è la più grande")
            
            # Stima fattore di scala
            scale_factor = self.estimate_scale_factor(target_image, ref_image)
            
            # Ridimensiona l'immagine target per matchare approssimativamente la reference
            new_height = int(target_image.shape[0] * scale_factor)
            new_width = int(target_image.shape[1] * scale_factor)
            
            # Limita le dimensioni alla reference image
            new_height = min(new_height, ref_image.shape[0])
            new_width = min(new_width, ref_image.shape[1])
            
            target_resized = resize(target_image, (new_height, new_width), 
                                  anti_aliasing=True, preserve_range=True)
            
            self.logger.info(f"Target ridimensionata da {target_image.shape} a {target_resized.shape}")
            
            # Registrazione
            transform_matrix = None
            method_used = "none"
            
            if self.registration_method in ['features', 'hybrid']:
                # Prova registrazione basata su features
                ref_pts, target_pts = self.detect_and_match_features(ref_image, target_resized)
                if len(ref_pts) > 0:
                    transform_matrix = self.estimate_transform_robust(ref_pts, target_pts)
                    if transform_matrix is not None:
                        method_used = "features"
            
            if transform_matrix is None and self.registration_method in ['phase', 'hybrid']:
                # Fallback: phase correlation
                try:
                    # Usa una regione centrale per phase correlation
                    center_y = ref_image.shape[0] // 2
                    center_x = ref_image.shape[1] // 2
                    half_h = min(target_resized.shape[0] // 2, ref_image.shape[0] // 4)
                    half_w = min(target_resized.shape[1] // 2, ref_image.shape[1] // 4)
                    
                    ref_roi = ref_image[center_y-half_h:center_y+half_h,
                                      center_x-half_w:center_x+half_w]
                    target_roi = target_resized[:2*half_h, :2*half_w]
                    
                    if ref_roi.shape == target_roi.shape:
                        shift, _, _ = phase_cross_correlation(ref_roi, target_roi)
                        transform_matrix = np.array([[1, 0, shift[1]], [0, 1, shift[0]]], dtype=np.float32)
                        method_used = f"phase_correlation(shift:{shift[0]:.1f},{shift[1]:.1f})"
                        self.logger.info(f"Phase correlation shift: {shift}")
                except Exception as e:
                    self.logger.warning(f"Phase correlation fallita: {e}")
            
            if transform_matrix is None:
                # Ultimo fallback: posiziona al centro
                offset_y = (ref_image.shape[0] - target_resized.shape[0]) // 2
                offset_x = (ref_image.shape[1] - target_resized.shape[1]) // 2
                transform_matrix = np.array([[1, 0, offset_x], [0, 1, offset_y]], dtype=np.float32)
                method_used = "center_placement"
                self.logger.info("Usato posizionamento centrale come fallback")
            
            # Applica trasformazione
            registered_target = cv2.warpAffine(
                target_resized, transform_matrix,
                (ref_image.shape[1], ref_image.shape[0]),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=0
            )
            
            # Crea maschera per la regione valida
            mask = np.ones_like(target_resized)
            mask_transformed = cv2.warpAffine(
                mask, transform_matrix,
                (ref_image.shape[1], ref_image.shape[0]),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=0
            )
            
            result = {
                'reference_image': ref_image,
                'target_image': target_image,
                'target_resized': target_resized,
                'registered_target': registered_target,
                'transform_matrix': transform_matrix,
                'scale_factor': scale_factor,
                'method_used': method_used,
                'mask': mask_transformed > 0.5,
                'reference_path': reference_path,
                'target_path': target_path
            }
            
            self.logger.info(f"Registrazione completata usando: {method_used}")
            return result
            
        except Exception as e:
            self.logger.error(f"Errore nella registrazione: {e}")
            raise
    
    def create_overlay_visualization(self, registration_result: Dict[str, Any], 
                                   overlay_mode: str = 'blend') -> np.ndarray:
        """
        Crea visualizzazione sovrapposta delle immagini registrate
        
        Args:
            registration_result: Risultato della registrazione
            overlay_mode: 'blend', 'checkerboard', 'side_by_side', 'thermal_overlay'
            
        Returns:
            Immagine di visualizzazione
        """
        ref_img = registration_result['reference_image']
        reg_target = registration_result['registered_target']
        mask = registration_result['mask']
        
        if overlay_mode == 'blend':
            # Blend semplice 50/50 nella regione di overlap
            alpha = 0.5
            result = ref_img.copy()
            result[mask] = alpha * ref_img[mask] + (1 - alpha) * reg_target[mask]
            
        elif overlay_mode == 'checkerboard':
            # Pattern a scacchiera
            result = ref_img.copy()
            h, w = result.shape
            checker = np.zeros((h, w), dtype=bool)
            checker[::20, ::20] = True
            checker[10::20, 10::20] = True
            
            checker_mask = checker & mask
            result[checker_mask] = reg_target[checker_mask]
            
        elif overlay_mode == 'thermal_overlay':
            # Overlay termico: converti a RGB e sovrapponi con colormap
            result_rgb = np.stack([ref_img, ref_img, ref_img], axis=2)
            
            # Applica colormap alla target (termica)
            thermal_colored = plt.cm.hot(reg_target)[:, :, :3]  # Solo RGB, no alpha
            
            # Overlay con trasparenza
            alpha = 0.6
            for i in range(3):
                result_rgb[:, :, i][mask] = (1 - alpha) * result_rgb[:, :, i][mask] + \
                                           alpha * thermal_colored[:, :, i][mask]
            
            return result_rgb
            
        elif overlay_mode == 'side_by_side':
            # Affianca le immagini
            result = np.hstack([ref_img, np.zeros_like(ref_img)])
            result[:, ref_img.shape[1]:] = reg_target
            
        else:
            result = ref_img.copy()
        
        return result