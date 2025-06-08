# Visualization

Questo modulo contiene visualizzatori interattivi per navigare attraverso le bande multispettrali con controlli da tastiera e mouse, ottimizzati per immagini MicaSense RedEdge.

## Componenti

### `quick_band_viewer.py`
**Visualizzatore semplice con controlli essenziali**

Strumento leggero per navigazione rapida tra bande con interfaccia minimalista.

#### Caratteristiche:
- **Navigazione fluida**: Slider e controlli tastiera
- **Visualizzazione grayscale**: Ogni banda in scala di grigi ottimizzata
- **Statistiche base**: Min, max, media per banda corrente
- **Performance ottimizzata**: Pre-normalizzazione per velocità
- **Interfaccia pulita**: Focus sulla visualizzazione

#### Controlli:
- **← →**: Banda precedente/successiva
- **1-5**: Salto diretto a banda specifica
- **Mouse**: Slider per navigazione
- **Q**: Esci

#### Uso:
```bash
python quick_band_viewer.py IMG_0001_registered.tif
```

### `interactive_band_viewer.py`
**Visualizzatore completo con statistiche dettagliate**

Strumento avanzato per analisi approfondita delle bande con statistiche complete e funzioni di export.

#### Caratteristiche Avanzate:
- **Statistiche dettagliate**: Min, max, media, std, valori unici
- **Percentili completi**: 1%, 5%, 25%, 50%, 75%, 95%, 99%
- **Bordi colorati**: Identificazione visiva banda per lunghezza d'onda
- **Export individuale**: Salvataggio PNG per ogni banda
- **Info real-time**: Aggiornamento automatico statistiche
- **Colorbar dinamica**: Scala intensità per ogni banda

#### Controlli Estesi:
- **← → ↑ ↓**: Navigazione bande
- **1-5**: Salto diretto a banda
- **Spazio**: Info dettagliate banda corrente (console)
- **S**: Salva banda corrente come PNG
- **Q**: Esci
- **Mouse**: Slider e bottoni

#### Uso:
```bash
python interactive_band_viewer.py -i IMG_0001_registered.tif
```

### `advanced_band_viewer.py`
**Visualizzatore multi-modalità con RGB e NDVI**

Strumento completo che combina navigazione bande singole con visualizzazioni composite avanzate.

#### Modalità Disponibili:

1. **Bande Singole**: Navigazione tradizionale grayscale
2. **RGB Naturale**: Composizione 3,2,1 per colori reali
3. **False Color IR**: Composizione 5,3,2 per vegetazione
4. **Red Edge Enhanced**: Composizione 4,3,2 per stress vegetazione
5. **NDVI-like**: Composizione 5,4,3 per salute vegetazione
6. **NDVI Calcolato**: Indice vegetazione (NIR-Red)/(NIR+Red)

#### Caratteristiche Uniche:
- **Switch modalità**: Cambio istantaneo tra visualizzazioni
- **NDVI real-time**: Calcolo e visualizzazione indice vegetazione
- **Interfaccia unificata**: Tutti i controlli in una finestra
- **Salvataggio multiplo**: Export di qualsiasi modalità
- **Statistiche contestuali**: Adattate alla modalità corrente

#### Controlli Completi:
- **B**: Modalità bande singole
- **R**: RGB naturale
- **F**: False color IR
- **E**: Red Edge enhanced
- **N**: NDVI-like composite
- **L**: NDVI calcolato
- **← →**: Navigazione (in modalità bande)
- **1-5**: Salto banda (in modalità bande)
- **S**: Salva modalità corrente
- **Q**: Esci

#### Uso:
```bash
python advanced_band_viewer.py -i IMG_0001_registered.tif
```

## Configurazione Bande MicaSense RedEdge

Tutti i visualizzatori utilizzano la configurazione standard:

```python
band_info = {
    0: {"name": "Banda 1 - Blue", "wavelength": "475 nm", "color": "blue"},
    1: {"name": "Banda 2 - Green", "wavelength": "560 nm", "color": "green"},
    2: {"name": "Banda 3 - Red", "wavelength": "668 nm", "color": "red"},
    3: {"name": "Banda 4 - Red Edge", "wavelength": "717 nm", "color": "darkred"},
    4: {"name": "Banda 5 - Near-IR", "wavelength": "840 nm", "color": "purple"}
}
```

## Algoritmi di Visualizzazione

### Normalizzazione Bande
```python
def normalize_band(band, percentile_range=(2, 98)):
    """Normalizza banda per visualizzazione ottimale"""
    p_min, p_max = np.percentile(band, percentile_range)
    return np.clip((band - p_min) / (p_max - p_min + 1e-8), 0, 1)
```

### Calcolo NDVI
```python
def calculate_ndvi(nir_band, red_band):
    """Calcola NDVI: (NIR - Red) / (NIR + Red)"""
    nir = nir_band.astype(float)
    red = red_band.astype(float)
    
    # Evita divisione per zero
    denominator = nir + red
    denominator[denominator == 0] = 1e-8
    
    ndvi = (nir - red) / denominator
    return np.clip(ndvi, -1, 1)
```

### Composizioni RGB
```python
def create_rgb_composite(bands, r_idx, g_idx, b_idx):
    """Crea composizione RGB da indici bande"""
    red = normalize_band(bands[r_idx])
    green = normalize_band(bands[g_idx])
    blue = normalize_band(bands[b_idx])
    
    return np.stack([red, green, blue], axis=2)
```

## Uso Programmatico

### Quick Band Viewer
```python
from image_registration.visualization.interactive import QuickBandViewer
import tifffile

# Carica dati
with tifffile.TiffFile("image.tif") as tif:
    data = tif.asarray()

# Crea e mostra visualizzatore
viewer = QuickBandViewer(data, "image.tif")
viewer.show()
```

### Interactive Band Viewer
```python
from image_registration.visualization.interactive import InteractiveBandViewer

# Carica e visualizza
bands_data = load_multiband_image("image.tif")
viewer = InteractiveBandViewer(bands_data, "image.tif")
viewer.show()
```

### Advanced Band Viewer
```python
from image_registration.visualization.interactive import AdvancedBandViewer

# Visualizzatore completo
viewer = AdvancedBandViewer(bands_data, "image.tif")
viewer.show()
```

## Statistiche Calcolate

### Statistiche Base (tutti i viewer):
- **Min/Max**: Valori estremi
- **Media**: Valore medio
- **Std**: Deviazione standard
- **Unici**: Numero valori distinti

### Statistiche Avanzate (Interactive/Advanced):
- **Percentili**: 1%, 5%, 25%, 50%, 75%, 95%, 99%
- **Dimensioni**: Larghezza × Altezza pixel
- **Range dinamico**: Differenza max-min
- **Distribuzione**: Istogramma valori

### Statistiche NDVI (Advanced):
- **Range NDVI**: -1 a +1
- **Media NDVI**: Salute vegetazione media
- **Percentili NDVI**: Distribuzione indice
- **Aree vegetate**: Pixel con NDVI > 0.3

## Performance e Ottimizzazioni

### Pre-processing:
- **Normalizzazione anticipata**: Tutte le bande pre-normalizzate all'avvio
- **Caching**: Immagini elaborate mantenute in memoria
- **Rendering ottimizzato**: Aggiornamento solo elementi modificati

### Gestione Memoria:
- **Lazy loading**: Caricamento on-demand per file grandi
- **Downsampling**: Riduzione risoluzione per preview veloci
- **Garbage collection**: Pulizia automatica memoria

### Responsività:
- **Threading**: Calcoli pesanti in background
- **Interrupt handling**: Gestione Ctrl+C pulita
- **Progress feedback**: Indicatori caricamento

## Esempi Avanzati

### Analisi Batch
```python
import glob
from image_registration.visualization.interactive import InteractiveBandViewer

# Analizza tutti i file registrati
for file_path in glob.glob("*_registered.tif"):
    print(f"\nAnalizzando: {file_path}")
    bands_data = load_multiband_image(file_path)
    
    # Calcola statistiche per tutte le bande
    for i in range(bands_data.shape[0]):
        stats = calculate_band_stats(bands_data[i])
        print(f"  Banda {i+1}: μ={stats['mean']:.1f}, σ={stats['std']:.1f}")
```

### Export Automatico
```python
# Salva tutte le bande come PNG
viewer = InteractiveBandViewer(bands_data, file_path)
for i in range(viewer.num_bands):
    viewer.current_band = i
    viewer.save_current_band()
```

## Troubleshooting

### Problemi Comuni:

1. **Visualizzazione lenta**:
   - Riduci risoluzione immagine
   - Chiudi altre applicazioni
   - Usa Quick Viewer per file grandi

2. **Controlli non responsivi**:
   - Verifica focus finestra matplotlib
   - Riavvia visualizzatore
   - Controlla versione matplotlib

3. **Errori caricamento**:
   - Verifica formato file (TIFF multibanda)
   - Controlla numero bande (minimo 3, ottimale 5)
   - Verifica permessi file

4. **Statistiche errate**:
   - Controlla range valori input
   - Verifica tipo dati (float vs int)
   - Controlla presenza valori NaN/inf

## Dipendenze

### Essenziali:
- `numpy`: Calcoli numerici
- `matplotlib`: Visualizzazione e interfaccia
- `matplotlib.widgets`: Controlli interattivi
- `tifffile`: Caricamento file TIFF

### Opzionali:
- `scikit-image`: Algoritmi elaborazione avanzati
- `PIL`: Supporto formati aggiuntivi
