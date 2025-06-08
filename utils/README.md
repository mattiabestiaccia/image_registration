# Utils - Utilities e Funzioni di Supporto

Questo modulo contiene funzioni di utilità per la gestione di file, gruppi di immagini e operazioni di supporto per il sistema di registrazione.

## Componenti

### `utils.py`
Funzioni di utilità per gestione file e operazioni di supporto.

#### Gestione Gruppi di Immagini

**`find_image_groups(input_path)`**
- Trova gruppi di 5 immagini con pattern `IMG_xxxx_N.tif`
- Supporta file singoli o cartelle
- Restituisce dizionario `{base_name: [file_paths]}`

```python
groups = find_image_groups("./input_folder/")
# Risultato: {'IMG_0001': ['IMG_0001_1.tif', 'IMG_0001_2.tif', ...]}
```

**`validate_image_group(file_paths)`**
- Valida che un gruppo contenga esattamente 5 bande
- Verifica esistenza e accessibilità file
- Controlla pattern naming corretto

#### Caricamento e Salvataggio

**`load_image_band(file_path)`**
- Carica singola banda da file TIFF
- Conversione automatica a float32
- Gestione errori robusta

**`load_image_band_with_metadata(file_path)`**
- Carica banda preservando metadati geospaziali
- Utilizza MetadataManager per estrazione metadati
- Restituisce tupla (immagine, metadati)

**`save_multiband_tiff(bands, output_path)`**
- Salva multiple bande in singolo file TIFF
- Versione legacy senza metadati
- Stack automatico lungo asse 0

**`save_multiband_tiff_with_metadata(...)`**
- Salva con preservazione metadati geospaziali
- Supporta descrizioni bande e matrici registrazione
- Utilizza MetadataManager per gestione completa

#### Gestione Output e Resume

**`create_output_filename(base_name, output_dir)`**
- Crea nome file output standardizzato
- Pattern: `{base_name}_registered.tif`
- Gestione path automatica

**`check_already_processed(base_name, output_dir)`**
- Verifica se gruppo già processato
- Controlla esistenza file output
- Supporta funzionalità resume

**`get_resume_info(input_groups, output_dir)`**
- Separa gruppi da processare da quelli completati
- Supporta ripresa elaborazione interrotta
- Restituisce tupla (da_processare, già_completati)

**`find_processed_groups(output_dir)`**
- Trova tutti i gruppi già processati in directory
- Estrae base_name da file `*_registered.tif`
- Supporta validazione stato elaborazione

## Pattern di Naming File

Il modulo gestisce file con pattern specifico per MicaSense RedEdge:

```
IMG_xxxx_1.tif  # Banda 1 - Blue (475 nm)
IMG_xxxx_2.tif  # Banda 2 - Green (560 nm)  
IMG_xxxx_3.tif  # Banda 3 - Red (668 nm)
IMG_xxxx_4.tif  # Banda 4 - Red Edge (717 nm)
IMG_xxxx_5.tif  # Banda 5 - Near-IR (840 nm)
```

Dove `xxxx` è identificatore numerico comune per tutte le bande dello stesso gruppo.

## Funzionalità Resume

Il sistema supporta ripresa automatica dell'elaborazione:

### Comportamento Automatico
- **Scansione cartella output**: Identifica file già processati
- **Skip gruppi completati**: Evita riprocessing non necessario
- **Continua da interruzione**: Riprende con gruppi rimanenti
- **Report dettagliato**: Mostra progresso e file saltati

### Vantaggi
- **Risparmio tempo**: Non riprocessa file già completati
- **Robustezza**: Gestisce interruzioni (Ctrl+C, crash, etc.)
- **Flessibilità**: Permette elaborazione incrementale
- **Sicurezza**: Preserva lavoro già svolto

## Esempi d'Uso

### Elaborazione Base
```python
from image_registration.utils import find_image_groups, create_output_filename

# Trova gruppi
groups = find_image_groups("./input/")

# Processa ogni gruppo
for base_name, file_paths in groups.items():
    output_path = create_output_filename(base_name, "./output/")
    # ... elaborazione ...
```

### Con Funzionalità Resume
```python
from image_registration.utils import get_resume_info

# Separa gruppi da processare
to_process, already_done = get_resume_info(all_groups, output_dir)

print(f"Già completati: {len(already_done)}")
print(f"Da processare: {len(to_process)}")

# Processa solo quelli rimanenti
for base_name, file_paths in to_process.items():
    # ... elaborazione ...
```

## Gestione Errori

- **File non trovati**: Gestione robusta con messaggi informativi
- **Gruppi incompleti**: Warning per gruppi con meno di 5 bande
- **Permessi file**: Controllo accessibilità lettura/scrittura
- **Spazio disco**: Verifica disponibilità prima del salvataggio

## Dipendenze

- `numpy`: Operazioni array
- `tifffile`: I/O file TIFF
- `os`, `pathlib`: Gestione filesystem
- `glob`: Pattern matching file
