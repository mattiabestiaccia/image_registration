# Modulo di Registrazione Immagini Multibanda Avanzato

Questo modulo implementa un sistema avanzato per la registrazione automatica di immagini multibanda a 5 bande disallineate utilizzando multiple tecniche: SLIC (Simple Linear Iterative Clustering), feature matching con ORB, trasformazioni affini robuste e phase cross-correlation.

## Caratteristiche Avanzate

- **Supporto immagini multibanda**: Gestisce gruppi di 5 immagini TIFF per banda
- **Algoritmi multipli**: SLIC, feature matching, phase correlation e metodo ibrido
- **Registrazione robusta**: Usa RANSAC per trasformazioni affini robuste
- **Enhancement automatico**: CLAHE e histogram matching per migliorare la coerenza
- **Preservazione metadati**: Mantiene CRS, geotrasformazioni e tag originali
- **Supporto GeoTIFF**: Compatibilità completa con file geospaziali
- **Funzionalità Resume**: Riprende automaticamente da dove interrotto
- **Flessibilità input**: Accetta singoli gruppi di immagini o cartelle multiple
- **Output unificato**: Produce file TIFF con 5 layer allineati
- **CLI intuitiva**: Interfaccia a riga di comando con parametri avanzati

## Installazione

1. Clona o scarica il progetto
2. Installa le dipendenze:

```bash
pip install -r requirements.txt
```

## Formato File di Input

Il modulo si aspetta file TIFF con il seguente pattern di naming:
- `IMG_xxxx_1.tif` - Banda 1
- `IMG_xxxx_2.tif` - Banda 2  
- `IMG_xxxx_3.tif` - Banda 3
- `IMG_xxxx_4.tif` - Banda 4
- `IMG_xxxx_5.tif` - Banda 5

Dove `xxxx` è un identificatore numerico comune per tutte le bande dello stesso gruppo.

## Utilizzo

### Interfaccia a Riga di Comando

#### Processare un singolo gruppo di immagini:
```bash
python main.py -i IMG_1234_1.tif -o ./output/
```

#### Processare tutte le immagini in una cartella:
```bash
python main.py -i ./input_folder/ -o ./output/
```

#### Con parametri personalizzati:
```bash
python main.py -i ./input/ -o ./output/ --segments 2000 --compactness 15 --reference-band 3 --method hybrid
```

#### Metodi di registrazione disponibili:
```bash
# Metodo ibrido (raccomandato) - combina feature matching e SLIC
python main.py -i ./input/ -o ./output/ --method hybrid

# Solo feature matching con ORB
python main.py -i ./input/ -o ./output/ --method features

# Solo registrazione basata su SLIC
python main.py -i ./input/ -o ./output/ --method slic

# Solo phase cross-correlation
python main.py -i ./input/ -o ./output/ --method phase

# Preservazione metadati (comportamento di default)
python main.py -i ./input/ -o ./output/

# Disabilita preservazione metadati (solo se necessario)
python main.py -i ./input/ -o ./output/ --no-metadata

# Forza riprocessamento completo (ignora file esistenti)
python main.py -i ./input/ -o ./output/ --no-resume
```

### Parametri Disponibili

- `-i, --input`: Percorso del file singolo o cartella (richiesto)
- `-o, --output`: Cartella di output (richiesto)
- `--segments`: Numero di superpixel per SLIC (default: 1000)
- `--compactness`: Parametro di compattezza per SLIC (default: 10.0)
- `--sigma`: Sigma per il filtro gaussiano (default: 1.0)
- `--reference-band`: Banda di riferimento 1-5 (default: 1)
- `--method`: Metodo di registrazione: hybrid, features, slic, phase (default: hybrid)
- `--no-metadata`: Disabilita preservazione metadati geospaziali (default: preserva sempre)
- `--resume`: Riprendi da dove interrotto, saltando file già processati (default: True)
- `--no-resume`: Forza riprocessamento di tutti i file, anche se già esistenti
- `--verbose, -v`: Output verboso

### Utilizzo Programmatico

```python
from image_registration import ImageRegistration
from utils import find_image_groups, create_output_filename

# Inizializza il registratore
registrator = ImageRegistration(
    n_segments=1000,
    compactness=10.0,
    reference_band=1
)

# Trova gruppi di immagini
groups = find_image_groups("./input_folder/")

# Processa ogni gruppo
for base_name, band_paths in groups.items():
    output_path = create_output_filename(base_name, "./output/")
    success = registrator.process_image_group(band_paths, output_path)
    print(f"Gruppo {base_name}: {'OK' if success else 'ERRORE'}")
```

## Algoritmo Avanzato

### Metodo Ibrido (Raccomandato)
1. **Caricamento**: Le 5 bande vengono caricate e validate
2. **Pre-processing avanzato**:
   - Normalizzazione e enhancement del contrasto con CLAHE
   - Filtro gaussiano per riduzione rumore
   - Histogram matching verso la banda di riferimento
3. **Feature matching**:
   - Rilevamento keypoints con ORB
   - Matching robusto dei descriptors
   - Stima trasformazione affine con RANSAC
4. **Fallback SLIC**: Se feature matching fallisce:
   - Segmentazione SLIC in superpixel
   - Matching basato su similarità di intensità e area
   - Stima trasformazione dai centroidi matched
5. **Fallback finale**: Phase cross-correlation per shift semplice
6. **Allineamento**: Applicazione trasformazioni affini alle immagini originali
7. **Output**: Salvataggio del file TIFF multibanda allineato

### Vantaggi del Metodo Ibrido
- **Robustezza**: Multipli algoritmi di fallback
- **Precisione**: Trasformazioni affini gestiscono rotazioni e scaling
- **Adattabilità**: Si adatta automaticamente al tipo di disallineamento

## Output

Per ogni gruppo di 5 bande di input, viene prodotto un file TIFF con:
- 5 layer corrispondenti alle bande allineate
- Nome formato: `IMG_xxxx_registered.tif`
- Mantenimento della risoluzione e profondità originali
- **Metadati preservati** (se abilitato):
  - Sistema di coordinate (CRS)
  - Geotrasformazione
  - Tag personalizzati
  - Descrizioni delle bande
  - Informazioni di compressione

## Gestione Metadati Geospaziali

Il modulo **preserva automaticamente tutti i metadati geospaziali** di default:

### Metadati Supportati
- **CRS (Coordinate Reference System)**: EPSG, WKT, PROJ4
- **Geotrasformazione**: Coordinate geografiche pixel-to-world
- **Tag TIFF**: Metadati personalizzati (sensore, data, processing level)
- **Descrizioni bande**: Nomi e descrizioni per ogni banda
- **Parametri di compressione**: LZW, tiling, block size

### Validazione Automatica
- Verifica consistenza CRS tra tutte le bande
- Controllo dimensioni e trasformazioni
- Warning per metadati inconsistenti

### Aggiornamento Trasformazioni
- Le geotrasformazioni vengono aggiornate per riflettere la registrazione
- Mantenimento della precisione geografica
- Compatibilità con software GIS (QGIS, ArcGIS, GDAL)

## Funzionalità Resume

Il modulo supporta la **ripresa automatica** del processing:

### Comportamento Automatico
- **Scansiona cartella output**: Identifica file già processati
- **Salta gruppi completati**: Evita riprocessamento inutile
- **Continua da dove interrotto**: Riprende con i gruppi rimanenti
- **Report dettagliato**: Mostra progresso e file saltati

### Vantaggi
- **Risparmio tempo**: Non riprocessa file già completati
- **Robustezza**: Gestisce interruzioni (Ctrl+C, crash, etc.)
- **Flessibilità**: Permette processing incrementale
- **Sicurezza**: Preserva lavoro già fatto

### Esempi d'Uso

#### Processing Normale (con Resume)
```bash
# Prima esecuzione - processa tutti i file
python main.py -i ./input/ -o ./output/

# Seconda esecuzione - salta file già fatti
python main.py -i ./input/ -o ./output/
# Output: "Trovati 50 gruppi totali: 30 già processati (saltati), 20 da processare"
```

#### Forzare Riprocessamento
```bash
# Riprocessa tutto, ignorando file esistenti
python main.py -i ./input/ -o ./output/ --no-resume
```

## Dipendenze

- numpy: Operazioni su array numerici
- opencv-python: Processing immagini e trasformazioni geometriche
- scikit-image: Algoritmi di segmentazione e registrazione
- tifffile: I/O per file TIFF
- Pillow: Supporto aggiuntivo per formati immagine
- tqdm: Barre di progresso

## Limitazioni

- Supporta solo gruppi completi di 5 bande
- Ottimizzato per shift traslazionali (non rotazioni o deformazioni complesse)
- Richiede che le immagini abbiano dimensioni simili

## Troubleshooting

### Errore "Gruppo di immagini non valido"
- Verifica che ci siano esattamente 5 file per gruppo
- Controlla che i nomi seguano il pattern `IMG_xxxx_N.tif`
- Assicurati che tutti i file esistano e siano accessibili

### Risultati di registrazione scarsi
- Prova ad aumentare il numero di segmenti SLIC (`--segments`)
- Modifica il parametro di compattezza (`--compactness`)
- Cambia la banda di riferimento (`--reference-band`)

### Errori di memoria
- Riduci il numero di segmenti SLIC
- Processa le immagini in batch più piccoli
