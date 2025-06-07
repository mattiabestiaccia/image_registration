#!/usr/bin/env python3
"""
Script CLI per la registrazione di immagini multibanda
"""

import argparse
import os
import sys
from pathlib import Path
from tqdm import tqdm

from image_registration import ImageRegistration
from utils import find_image_groups, create_output_filename, get_resume_info, check_already_processed


def main():
    parser = argparse.ArgumentParser(
        description="Registrazione di immagini multibanda a 5 bande usando SLIC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi d'uso:

1. Processare una singola serie di immagini:
   python main.py -i IMG_1234_1.tif -o ./output/

2. Processare tutte le immagini in una cartella:
   python main.py -i ./input_folder/ -o ./output/

3. Con parametri personalizzati:
   python main.py -i ./input/ -o ./output/ --segments 2000 --compactness 15 --reference-band 3

4. Disabilita preservazione metadati (solo se necessario):
   python main.py -i ./input/ -o ./output/ --no-metadata

5. Forza riprocessamento completo (ignora file esistenti):
   python main.py -i ./input/ -o ./output/ --no-resume
        """
    )
    
    parser.add_argument('-i', '--input', required=True,
                       help='Percorso del file singolo o cartella contenente le immagini')
    
    parser.add_argument('-o', '--output', required=True,
                       help='Cartella di output per i file registrati')
    
    parser.add_argument('--segments', type=int, default=1000,
                       help='Numero di superpixel per SLIC (default: 1000)')
    
    parser.add_argument('--compactness', type=float, default=10.0,
                       help='Parametro di compattezza per SLIC (default: 10.0)')
    
    parser.add_argument('--sigma', type=float, default=1.0,
                       help='Sigma per il filtro gaussiano (default: 1.0)')
    
    parser.add_argument('--reference-band', type=int, default=1, choices=[1,2,3,4,5],
                       help='Banda di riferimento (1-5, default: 1)')

    parser.add_argument('--method', type=str, default='hybrid',
                       choices=['slic', 'features', 'hybrid', 'phase'],
                       help='Metodo di registrazione (default: hybrid)')

    parser.add_argument('--no-metadata', action='store_true',
                       help='Disabilita preservazione metadati geospaziali (default: preserva sempre)')

    parser.add_argument('--resume', action='store_true', default=True,
                       help='Riprendi da dove interrotto, saltando file già processati (default: True)')

    parser.add_argument('--no-resume', action='store_true',
                       help='Forza riprocessamento di tutti i file, anche se già esistenti')

    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Output verboso')
    
    args = parser.parse_args()
    
    # Verifica input
    if not os.path.exists(args.input):
        print(f"Errore: Il percorso di input '{args.input}' non esiste")
        sys.exit(1)
    
    # Crea cartella di output se non esiste
    os.makedirs(args.output, exist_ok=True)
    
    # Trova i gruppi di immagini
    print("Ricerca gruppi di immagini...")
    all_image_groups = find_image_groups(args.input)

    if not all_image_groups:
        print("Nessun gruppo di immagini trovato!")
        print("Assicurati che i file seguano il pattern: IMG_xxxx_1.tif, IMG_xxxx_2.tif, etc.")
        sys.exit(1)

    # Determina se usare la funzionalità di resume
    use_resume = args.resume and not args.no_resume

    if use_resume:
        # Separa gruppi da processare da quelli già completati
        image_groups, already_processed = get_resume_info(all_image_groups, args.output)

        print(f"Trovati {len(all_image_groups)} gruppi totali:")
        print(f"  {len(already_processed)} già processati (saltati)")
        print(f"  {len(image_groups)} da processare")

        if already_processed:
            print("\nGruppi già completati:")
            for base_name in sorted(already_processed.keys()):
                output_file = create_output_filename(base_name, args.output)
                print(f"  ✓ {base_name} -> {os.path.basename(output_file)}")

        if not image_groups:
            print("\n🎉 Tutti i gruppi sono già stati processati!")
            print(f"File di output in: {args.output}")
            sys.exit(0)

        print(f"\nContinuando con {len(image_groups)} gruppi rimanenti...")

    else:
        image_groups = all_image_groups
        print(f"Trovati {len(image_groups)} gruppi di immagini (modalità completa):")

    # Mostra dettagli gruppi da processare
    for base_name, files in image_groups.items():
        print(f"  {base_name}: {len(files)} bande")
        if len(files) != 5:
            print(f"    ATTENZIONE: Gruppo incompleto (trovate {len(files)} bande invece di 5)")
    
    # Preserva metadati di default, disabilita solo se richiesto esplicitamente
    preserve_metadata = not args.no_metadata

    # Inizializza il registratore
    registrator = ImageRegistration(
        n_segments=args.segments,
        compactness=args.compactness,
        sigma=args.sigma,
        reference_band=args.reference_band,
        registration_method=args.method,
        preserve_metadata=preserve_metadata
    )
    
    # Processa ogni gruppo
    successful = 0
    failed = 0
    
    print(f"\nInizio processing con banda di riferimento: {args.reference_band}")
    print(f"Metodo di registrazione: {args.method}")
    print(f"Preservazione metadati: {'Sì (default)' if preserve_metadata else 'No (disabilitata)'}")
    print(f"Modalità resume: {'Sì (default)' if use_resume else 'No (riprocessa tutto)'}")
    print(f"Parametri SLIC: segments={args.segments}, compactness={args.compactness}")
    
    for base_name, band_paths in tqdm(image_groups.items(), desc="Processing gruppi"):
        if len(band_paths) != 5:
            print(f"Saltando {base_name}: gruppo incompleto ({len(band_paths)} bande)")
            failed += 1
            continue
        
        # Crea nome file di output
        output_path = create_output_filename(base_name, args.output)

        # Controllo aggiuntivo per sicurezza (nel caso use_resume sia False)
        if not use_resume and os.path.exists(output_path):
            print(f"\nProcessing {base_name}...")
            print(f"  ⚠️  File di output già esistente: {os.path.basename(output_path)}")
            print(f"  🔄 Sovrascrivendo (modalità no-resume)...")
        else:
            print(f"\nProcessing {base_name}...")

        if args.verbose:
            print(f"  Input: {[os.path.basename(p) for p in band_paths]}")
            print(f"  Output: {os.path.basename(output_path)}")

        # Processa il gruppo
        success = registrator.process_image_group(band_paths, output_path)
        
        if success:
            successful += 1
            print(f"  ✓ Completato: {os.path.basename(output_path)}")
        else:
            failed += 1
            print(f"  ✗ Fallito: {base_name}")
    
    # Riepilogo finale
    print(f"\n{'='*50}")
    print(f"RIEPILOGO:")
    if use_resume and already_processed:
        print(f"  Gruppi già completati (saltati): {len(already_processed)}")
    print(f"  Gruppi processati con successo: {successful}")
    print(f"  Gruppi falliti: {failed}")
    if use_resume:
        total_completed = len(already_processed) + successful
        print(f"  Totale completati: {total_completed}/{len(all_image_groups)}")
    else:
        print(f"  Totale processati: {successful + failed}")

    if successful > 0 or (use_resume and already_processed):
        print(f"\nFile di output salvati in: {args.output}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
