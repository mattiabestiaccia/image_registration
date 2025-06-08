# Core - Algoritmi di Registrazione Principali

Questo modulo contiene gli algoritmi principali per la registrazione di immagini multispettrali e la gestione dei metadati geospaziali.

## Componenti

### `image_registration.py`
**Classe principale: `ImageRegistration`**

Implementa algoritmi avanzati per la registrazione automatica di immagini multispettrali a 5 bande:

#### Metodi di Registrazione Disponibili:
- **Hybrid** (raccomandato): Combina feature matching e SLIC
- **Features**: Solo feature matching con ORB
- **SLIC**: Solo segmentazione SLIC
- **Phase**: Solo correlazione di fase

#### Caratteristiche Principali:
- Supporto per immagini MicaSense RedEdge (5 bande)
- Trasformazioni affini robuste con RANSAC
- Pre-processing avanzato (CLAHE, filtri Gaussiani)
- Gestione automatica dei fallback tra algoritmi
- Preservazione metadati geospaziali

#### Uso:
```python
from image_registration.core import ImageRegistration

registrator = ImageRegistration(
    n_segments=1000,
    compactness=10.0,
    reference_band=1,
    registration_method='hybrid'
)

success = registrator.process_image_group(band_paths, output_path)
```

### `metadata_utils.py`
**Classe principale: `MetadataManager`**

Gestisce i metadati geospaziali durante la registrazione:

#### Funzionalità:
- Estrazione metadati da file GeoTIFF
- Preservazione CRS e geotrasformazioni
- Aggiornamento trasformazioni dopo registrazione
- Validazione consistenza spaziale
- Salvataggio con metadati preservati

#### Metadati Supportati:
- **CRS**: Sistemi di coordinate (EPSG, WKT, PROJ4)
- **Geotrasformazione**: Coordinate pixel-to-world
- **Tag TIFF**: Metadati personalizzati
- **Descrizioni bande**: Nomi e descrizioni
- **Parametri compressione**: LZW, tiling, dimensioni blocchi

#### Uso:
```python
from image_registration.core import MetadataManager

metadata_manager = MetadataManager()
image, metadata = metadata_manager.load_image_with_metadata(file_path)
metadata_manager.save_multiband_with_metadata(bands, output_path, metadata)
```

## Algoritmo di Registrazione

### Metodo Hybrid (Raccomandato)

1. **Caricamento**: Le 5 bande vengono caricate e validate
2. **Pre-processing avanzato**:
   - Normalizzazione e enhancement del contrasto con CLAHE
   - Filtro Gaussiano per riduzione rumore
   - Histogram matching verso banda di riferimento
3. **Feature matching**:
   - Rilevamento keypoint con ORB
   - Matching robusto dei descrittori
   - Stima trasformazione affine con RANSAC
4. **Fallback SLIC**: Se feature matching fallisce:
   - Segmentazione SLIC in superpixel
   - Matching basato su similarità intensità e area
   - Stima trasformazione da centroidi matched
5. **Fallback finale**: Correlazione di fase per shift semplici
6. **Allineamento**: Applicazione trasformazioni affini alle immagini originali
7. **Output**: Salvataggio file TIFF multibanda allineato

### Vantaggi del Metodo Hybrid
- **Robustezza**: Algoritmi multipli di fallback
- **Precisione**: Trasformazioni affini gestiscono rotazioni e scaling
- **Adattabilità**: Si adatta automaticamente al tipo di disallineamento

## Dipendenze

- `numpy`: Operazioni array numerici
- `opencv-python`: Elaborazione immagini e trasformazioni geometriche
- `scikit-image`: Algoritmi segmentazione e registrazione
- `rasterio`: I/O per file geospaziali
- `tifffile`: Supporto aggiuntivo per file TIFF

## Limitazioni

- Supporta solo gruppi completi di 5 bande
- Ottimizzato per shift traslazionali (non rotazioni o deformazioni complesse)
- Richiede immagini con dimensioni simili
- Metadati geospaziali richiedono rasterio installato
