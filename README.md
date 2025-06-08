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

### ⚠️ Problema File TIFF Compressi
Se vedi l'errore `COMPRESSION.LZW requires the 'imagecodecs' package`:
```bash
pip install imagecodecs
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

**Licenza**: MIT | **Supporto**: Apri issue per domande o problemi
