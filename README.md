# 🛰️ Image Registration - Multispectral Image Registration

System for automatic registration of multispectral images with support for **MicaSense RedEdge** cameras (5 bands).

## ✨ Features

- **Automatic registration** with SLIC algorithms, feature matching, and phase correlation
- **Full graphical interface** with advanced visualization
- **MicaSense RedEdge support** (5 bands: Blue, Green, Red, Red Edge, Near-IR)
- **Multiple visualization modes**: RGB, NDVI, Red Edge Enhanced, single bands
- **Project management** with automatic file organization
- **Preservation of geospatial metadata**

## 🚀 Quick Start

### Automatic Installation (Recommended)
```bash
python3 install_dependencies.py
```

### Manual Installation
```bash
pip install -r requirements.txt
# or
pip install numpy opencv-python scikit-image tifffile matplotlib imagecodecs rasterio
```

### Start Interface
```bash
python3 run_gui.py
```

### Workflow
1. **Select** image files or folders
2. **Configure** registration method and reference band
3. **Process** images automatically
4. **View** results with multiple modes
5. **Save** visualizations and results

## 📁 Structure

```
image_registration/
├── core/                    # Registration algorithms
├── gui/                     # Graphical interface
├── utils/                   # Support utilities
├── projects/                # User projects
└── run_gui.py               # Start interface
```

## 🎨 Visualization Modes

- **Natural RGB (3,2,1)**: Familiar view
- **Red Edge Enhanced (4,3,2)**: Vegetation stress
- **NDVI-like (5,4,3)**: Vegetation analysis
- **NDVI**: Quantitative index with colorbar
- **Single Bands**: Individual band navigation

## 📷 MicaSense RedEdge Bands

| Band | Wavelength | Use |
|------|------------|-----|
| 1 | Blue (475 nm) | Water, atmosphere |
| 2 | Green (560 nm) | Vegetation, RGB |
| 3 | Red (668 nm) | Chlorophyll, RGB |
| 4 | Red Edge (717 nm) | Vegetation stress |
| 5 | Near-IR (840 nm) | Biomass, NDVI |

## 🔧 Configuration

### Registration Methods
- **`hybrid`**: Feature matching + SLIC (recommended)
- **`features`**: Feature matching only (fast)
- **`slic`**: SLIC superpixels only (robust)
- **`phase`**: Phase correlation (fallback)

### Supported Formats
- **Input**: Single-band TIFFs, structured names `IMG_xxxx_n.tif`
- **Output**: Registered multiband TIFF, visualizations PNG/JPEG/PDF

## 💡 Tips

- **Reference band**: Red (band 3) for most cases
- **Overlap**: > 60% between images for best results
- **Organization**: Files named `IMG_xxxx_1.tif`...`IMG_xxxx_5.tif` are grouped automatically

## 🎯 Use Cases

- **Agriculture**: Crop monitoring, NDVI calculation
- **Environment**: Vegetation analysis, ecosystem monitoring  
- **Research**: Pre-processing multispectral datasets

---

# 🛰️ Image Registration - Registrazione Immagini Multispettrali

Sistema per la registrazione automatica di immagini multispettrali con supporto per fotocamere **MicaSense RedEdge** (5 bande).

## ✨ Caratteristiche

- **Registrazione automatica** con algoritmi SLIC, feature matching e correlazione di fase
- **Interfaccia grafica completa** con visualizzazione avanzata
- **Supporto MicaSense RedEdge** (5 bande: Blue, Green, Red, Red Edge, Near-IR)
- **Modalità visualizzazione multiple**: RGB, NDVI, Red Edge Enhanced, bande singole
- **Gestione progetti** con organizzazione automatica file
- **Preservazione metadati** geospaziali

## 🚀 Avvio Rapido

### Installazione Automatica (Raccomandato)
```bash
python3 install_dependencies.py
```

### Installazione Manuale
```bash
pip install -r requirements.txt
# oppure
pip install numpy opencv-python scikit-image tifffile matplotlib imagecodecs rasterio
```

### Avvio Interfaccia
```bash
python3 run_gui.py
```

### Workflow
1. **Seleziona** file immagini o cartelle
2. **Configura** metodo registrazione e banda di riferimento
3. **Elabora** immagini automaticamente
4. **Visualizza** risultati con modalità multiple
5. **Salva** visualizzazioni e risultati

## 📁 Struttura

```
image_registration/
├── core/                    # Algoritmi registrazione
├── gui/                     # Interfaccia grafica
├── utils/                   # Utilità supporto
├── projects/                # Progetti utente
└── run_gui.py              # Avvio interfaccia
```

## 🎨 Modalità Visualizzazione

- **RGB Naturale (3,2,1)**: Vista familiare
- **Red Edge Enhanced (4,3,2)**: Stress vegetazione
- **NDVI-like (5,4,3)**: Analisi vegetazione
- **NDVI**: Indice quantitativo con colorbar
- **Bande Singole**: Navigazione individuale

## 📷 Bande MicaSense RedEdge

| Banda | Lunghezza d'onda | Uso |
|-------|------------------|-----|
| 1 | Blue (475 nm) | Acqua, atmosfera |
| 2 | Green (560 nm) | Vegetazione, RGB |
| 3 | Red (668 nm) | Clorofilla, RGB |
| 4 | Red Edge (717 nm) | Stress vegetazione |
| 5 | Near-IR (840 nm) | Biomassa, NDVI |

## 🔧 Configurazione

### Metodi Registrazione
- **`hybrid`**: Feature matching + SLIC (consigliato)
- **`features`**: Solo feature matching (veloce)
- **`slic`**: Solo superpixel SLIC (robusto)
- **`phase`**: Correlazione di fase (fallback)

### Formati Supportati
- **Input**: TIFF singole bande, nomi strutturati `IMG_xxxx_n.tif`
- **Output**: TIFF multibanda registrato, visualizzazioni PNG/JPEG/PDF

## 💡 Suggerimenti

- **Banda di riferimento**: Red (banda 3) per la maggior parte dei casi
- **Sovrapposizione**: > 60% tra immagini per migliori risultati
- **Organizzazione**: File con nomi `IMG_xxxx_1.tif`...`IMG_xxxx_5.tif` vengono raggruppati automaticamente

## 🎯 Casi d'Uso

- **Agricoltura**: Monitoraggio colture, calcolo NDVI
- **Ambiente**: Analisi vegetazione, monitoraggio ecosistemi  
- **Ricerca**: Pre-processing dataset multispettrali

---

