# CLI - Interfacce a Riga di Comando

Questo modulo contiene le interfacce a riga di comando per l'utilizzo del sistema di registrazione immagini multispettrali.

## Componenti

### `main.py`
**Script principale per registrazione batch di immagini multispettrali**

Interfaccia completa per processare singoli gruppi di immagini o intere cartelle con funzionalità avanzate di resume e configurazione.

## Funzionalità Principali

### Modalità di Input
- **File singolo**: Processa un gruppo specifico di 5 bande
- **Cartella completa**: Processa tutti i gruppi trovati nella directory
- **Pattern automatico**: Riconoscimento automatico pattern `IMG_xxxx_N.tif`

### Algoritmi di Registrazione
- **Hybrid** (raccomandato): Combina feature matching e SLIC
- **Features**: Solo feature matching con ORB
- **SLIC**: Solo segmentazione SLIC  
- **Phase**: Solo correlazione di fase

### Gestione Metadati
- **Preservazione automatica**: Mantiene CRS, geotrasformazioni e tag
- **Aggiornamento trasformazioni**: Riflette le registrazioni applicate
- **Compatibilità GIS**: Output compatibile con QGIS, ArcGIS, GDAL

### Funzionalità Resume
- **Ripresa automatica**: Salta file già processati
- **Gestione interruzioni**: Riprende da dove interrotto
- **Report dettagliato**: Mostra progresso e file saltati

## Uso

### Esempi Base

```bash
# Processa un singolo gruppo di immagini
python main.py -i IMG_1234_1.tif -o ./output/

# Processa tutte le immagini in una cartella
python main.py -i ./input_folder/ -o ./output/

# Con parametri personalizzati
python main.py -i ./input/ -o ./output/ \
    --segments 2000 \
    --compactness 15 \
    --reference-band 3 \
    --method hybrid
```

### Metodi di Registrazione

```bash
# Metodo hybrid (raccomandato)
python main.py -i ./input/ -o ./output/ --method hybrid

# Solo feature matching
python main.py -i ./input/ -o ./output/ --method features

# Solo SLIC
python main.py -i ./input/ -o ./output/ --method slic

# Solo correlazione di fase
python main.py -i ./input/ -o ./output/ --method phase
```

### Gestione Metadati

```bash
# Preservazione metadati (comportamento default)
python main.py -i ./input/ -o ./output/

# Disabilita preservazione metadati
python main.py -i ./input/ -o ./output/ --no-metadata
```

### Funzionalità Resume

```bash
# Prima esecuzione - processa tutti i file
python main.py -i ./input/ -o ./output/

# Seconda esecuzione - salta file già completati
python main.py -i ./input/ -o ./output/
# Output: "Found 50 total groups: 30 already processed (skipped), 20 to process"

# Forza riprocessing completo
python main.py -i ./input/ -o ./output/ --no-resume
```

## Parametri Completi

### Parametri Obbligatori
- `-i, --input`: File singolo o cartella contenente immagini
- `-o, --output`: Directory di output per file registrati

### Parametri SLIC
- `--segments`: Numero superpixel per SLIC (default: 1000)
- `--compactness`: Parametro compattezza SLIC (default: 10.0)
- `--sigma`: Sigma per filtro Gaussiano (default: 1.0)

### Parametri Registrazione
- `--reference-band`: Banda di riferimento 1-5 (default: 1)
- `--method`: Metodo registrazione (default: hybrid)
  - `hybrid`: Feature matching + SLIC fallback
  - `features`: Solo feature matching ORB
  - `slic`: Solo segmentazione SLIC
  - `phase`: Solo correlazione di fase

### Parametri Metadati
- `--no-metadata`: Disabilita preservazione metadati geospaziali
- `--resume`: Abilita funzionalità resume (default: True)
- `--no-resume`: Forza riprocessing completo

### Parametri Output
- `--verbose, -v`: Output verboso con dettagli elaborazione

## Pattern File di Input

Il sistema riconosce automaticamente gruppi di file con pattern:

```
IMG_xxxx_1.tif  # Banda 1 - Blue (475 nm)
IMG_xxxx_2.tif  # Banda 2 - Green (560 nm)
IMG_xxxx_3.tif  # Banda 3 - Red (668 nm)
IMG_xxxx_4.tif  # Banda 4 - Red Edge (717 nm)
IMG_xxxx_5.tif  # Banda 5 - Near-IR (840 nm)
```

Dove `xxxx` è un identificatore numerico comune per tutte le bande dello stesso gruppo.

## Output

### File Prodotti
Per ogni gruppo di 5 bande input, viene prodotto:
- **File TIFF multibanda**: `IMG_xxxx_registered.tif`
- **5 layer allineati**: Corrispondenti alle bande registrate
- **Metadati preservati**: CRS, geotrasformazioni, tag personalizzati
- **Risoluzione originale**: Mantenuta profondità e dimensioni

### Struttura Metadati
```
Metadati preservati:
├── CRS (Coordinate Reference System)
├── Geotrasformazione (pixel-to-world)
├── Tag TIFF personalizzati
├── Descrizioni bande
├── Parametri compressione
└── Informazioni registrazione
```

## Esempi Avanzati

### Elaborazione con Parametri Ottimizzati
```bash
# Per immagini ad alta risoluzione
python main.py -i ./input/ -o ./output/ \
    --segments 3000 \
    --compactness 20 \
    --sigma 1.5 \
    --method hybrid \
    --verbose

# Per immagini con disallineamento complesso
python main.py -i ./input/ -o ./output/ \
    --method features \
    --reference-band 3 \
    --verbose

# Per elaborazione veloce
python main.py -i ./input/ -o ./output/ \
    --segments 500 \
    --method phase \
    --no-metadata
```

### Batch Processing con Resume
```bash
#!/bin/bash
# Script per elaborazione batch con gestione errori

INPUT_DIR="./raw_images"
OUTPUT_DIR="./registered_images"

# Prima esecuzione
echo "Avvio elaborazione batch..."
python main.py -i "$INPUT_DIR" -o "$OUTPUT_DIR" --verbose

# Verifica e riprendi se necessario
if [ $? -ne 0 ]; then
    echo "Errore rilevato, riprovo con parametri conservativi..."
    python main.py -i "$INPUT_DIR" -o "$OUTPUT_DIR" \
        --method slic \
        --segments 800 \
        --verbose
fi

echo "Elaborazione completata!"
```

### Monitoraggio Progresso
```bash
# Con output dettagliato
python main.py -i ./input/ -o ./output/ --verbose 2>&1 | tee processing.log

# Conta file processati
find ./output/ -name "*_registered.tif" | wc -l
```

## Gestione Errori

### Errori Comuni e Soluzioni

1. **"No image groups found"**
   ```bash
   # Verifica pattern naming
   ls ./input/IMG_*_*.tif
   
   # Controlla che ci siano esattamente 5 bande per gruppo
   ```

2. **"Invalid image group"**
   ```bash
   # Verifica completezza gruppi
   python -c "
   from image_registration.utils import find_image_groups
   groups = find_image_groups('./input/')
   for name, files in groups.items():
       print(f'{name}: {len(files)} files')
   "
   ```

3. **Errori di memoria**
   ```bash
   # Riduci parametri SLIC
   python main.py -i ./input/ -o ./output/ --segments 500
   
   # Processa in batch più piccoli
   ```

4. **Risultati di registrazione scarsi**
   ```bash
   # Prova metodo diverso
   python main.py -i ./input/ -o ./output/ --method features
   
   # Cambia banda di riferimento
   python main.py -i ./input/ -o ./output/ --reference-band 3
   
   # Aumenta segmenti SLIC
   python main.py -i ./input/ -o ./output/ --segments 2000
   ```

## Integrazione con Altri Strumenti

### Con Visualizzatori
```bash
# Registra e visualizza
python main.py -i ./input/ -o ./output/
python ../visualization/rgb/quick_rgb_view.py ./output/IMG_0001_registered.tif

# Registra e analizza interattivamente
python main.py -i ./input/ -o ./output/
python ../visualization/interactive/advanced_band_viewer.py -i ./output/IMG_0001_registered.tif
```

### Con Script Personalizzati
```python
import subprocess
import sys

# Registrazione automatica
result = subprocess.run([
    sys.executable, "main.py",
    "-i", "./input/",
    "-o", "./output/",
    "--method", "hybrid",
    "--verbose"
], capture_output=True, text=True)

if result.returncode == 0:
    print("Registrazione completata con successo!")
    print(result.stdout)
else:
    print("Errore durante registrazione:")
    print(result.stderr)
```

## Performance e Ottimizzazione

### Parametri per Velocità
```bash
# Elaborazione veloce (qualità ridotta)
python main.py -i ./input/ -o ./output/ \
    --segments 300 \
    --method phase \
    --no-metadata
```

### Parametri per Qualità
```bash
# Elaborazione di qualità (più lenta)
python main.py -i ./input/ -o ./output/ \
    --segments 2000 \
    --compactness 15 \
    --method hybrid \
    --sigma 1.5
```

### Monitoraggio Risorse
```bash
# Con monitoraggio memoria
/usr/bin/time -v python main.py -i ./input/ -o ./output/

# Con profiling
python -m cProfile -o profile.stats main.py -i ./input/ -o ./output/
```

## Dipendenze

- `argparse`: Parsing argomenti CLI
- `os`, `sys`: Operazioni sistema
- `pathlib`: Gestione path
- `tqdm`: Progress bar
- Moduli core del package per funzionalità registrazione
