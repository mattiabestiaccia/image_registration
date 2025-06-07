# !/usr/bin/env python3
"""
CLI script for multiband image registration
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
        description="5-band multiband image registration using SLIC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:

1. Process a single image series:
   python main.py -i IMG_1234_1.tif -o ./output/

2. Process all images in a folder:
   python main.py -i ./input_folder/ -o ./output/

3. With custom parameters:
   python main.py -i ./input/ -o ./output/ --segments 2000 --compactness 15 --reference-band 3

4. Disable metadata preservation (only if necessary):
   python main.py -i ./input/ -o ./output/ --no-metadata

5. Force complete reprocessing (ignore existing files):
   python main.py -i ./input/ -o ./output/ --no-resume
        """
    )
    
    parser.add_argument('-i', '--input', required=True,
                       help='Path to single file or folder containing images')

    parser.add_argument('-o', '--output', required=True,
                       help='Output directory for registered files')

    parser.add_argument('--segments', type=int, default=1000,
                       help='Number of superpixels for SLIC (default: 1000)')

    parser.add_argument('--compactness', type=float, default=10.0,
                       help='Compactness parameter for SLIC (default: 10.0)')

    parser.add_argument('--sigma', type=float, default=1.0,
                       help='Sigma for Gaussian filter (default: 1.0)')

    parser.add_argument('--reference-band', type=int, default=1, choices=[1,2,3,4,5],
                       help='Reference band (1-5, default: 1)')

    parser.add_argument('--method', type=str, default='hybrid',
                       choices=['slic', 'features', 'hybrid', 'phase'],
                       help='Registration method (default: hybrid)')

    parser.add_argument('--no-metadata', action='store_true',
                       help='Disable geospatial metadata preservation (default: always preserve)')

    parser.add_argument('--resume', action='store_true', default=True,
                       help='Resume from where interrupted, skipping already processed files (default: True)')

    parser.add_argument('--no-resume', action='store_true',
                       help='Force reprocessing of all files, even if already existing')

    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Verify input
    if not os.path.exists(args.input):
        print(f"Error: Input path '{args.input}' does not exist")
        sys.exit(1)

    # Create output folder if it doesn't exist
    os.makedirs(args.output, exist_ok=True)

    # Find image groups
    print(f"Searching for image groups...")
    all_image_groups = find_image_groups(args.input)

    if not all_image_groups:
        print(f"No image groups found!")
        print(f"Make sure files follow the pattern: IMG_xxxx_1.tif, IMG_xxxx_2.tif, etc.")
        sys.exit(1)

    # Determine whether to use resume functionality
    use_resume = args.resume and not args.no_resume

    if use_resume:
        # Separate groups to process from those already completed
        image_groups, already_processed = get_resume_info(all_image_groups, args.output)

        print(f"Found {len(all_image_groups)} total groups:")
        print(f"  {len(already_processed)} already processed (skipped)")
        print(f"  {len(image_groups)} to process")

        if already_processed:
            print(f"\nGroups already completed:")
            for base_name in sorted(already_processed.keys()):
                output_file = create_output_filename(base_name, args.output)
                print(f"  ✓ {base_name} -> {os.path.basename(output_file)}")

        if not image_groups:
            print(f"\n🎉 All groups have already been processed!")
            print(f"Output files in: {args.output}")
            sys.exit(0)

        print(f"\nContinuing with {len(image_groups)} remaining groups...")

    else:
        image_groups = all_image_groups
        print(f"Found {len(image_groups)} image groups (complete mode):")

    # Show details of groups to process
    for base_name, files in image_groups.items():
        print(f"  {base_name}: {len(files)} bands")
        if len(files) != 5:
            print(f"    WARNING: Incomplete group (found {len(files)} bands instead of 5)")
    
    # Preserve metadata by default, disable only if explicitly requested
    preserve_metadata = not args.no_metadata

    # Initialize registrator
    registrator = ImageRegistration(
        n_segments=args.segments,
        compactness=args.compactness,
        sigma=args.sigma,
        reference_band=args.reference_band,
        registration_method=args.method,
        preserve_metadata=preserve_metadata
    )

    # Process each group
    successful = 0
    failed = 0

    print(f"\nStarting processing with reference band: {args.reference_band}")
    print(f"Registration method: {args.method}")
    print(f"Metadata preservation: {'Yes (default)' if preserve_metadata else 'No (disabled)'}")
    print(f"Resume mode: {'Yes (default)' if use_resume else 'No (reprocess all)'}")
    print(f"SLIC parameters: segments={args.segments}, compactness={args.compactness}")
    
    for base_name, band_paths in tqdm(image_groups.items(), desc="Processing groups"):
        if len(band_paths) != 5:
            print(f"Skipping {base_name}: incomplete group ({len(band_paths)} bands)")
            failed += 1
            continue

        # Create output file name
        output_path = create_output_filename(base_name, args.output)

        # Additional safety check (in case use_resume is False)
        if not use_resume and os.path.exists(output_path):
            print(f"\nProcessing {base_name}...")
            print(f"  ⚠️  Output file already exists: {os.path.basename(output_path)}")
            print(f"  🔄 Overwriting (no-resume mode)...")
        else:
            print(f"\nProcessing {base_name}...")

        if args.verbose:
            print(f"  Input: {[os.path.basename(p) for p in band_paths]}")
            print(f"  Output: {os.path.basename(output_path)}")

        # Process group
        success = registrator.process_image_group(band_paths, output_path)

        if success:
            successful += 1
            print(f"  ✓ Completed: {os.path.basename(output_path)}")
        else:
            failed += 1
            print(f"  ✗ Failed: {base_name}")
    
    # Final summary
    print(f"\n{'='*50}")
    print(f"SUMMARY:")
    if use_resume and already_processed:
        print(f"  Groups already completed (skipped): {len(already_processed)}")
    print(f"  Groups processed successfully: {successful}")
    print(f"  Failed groups: {failed}")
    if use_resume:
        total_completed = len(already_processed) + successful
        print(f"  Total completed: {total_completed}/{len(all_image_groups)}")
    else:
        print(f"  Total processed: {successful + failed}")

    if successful > 0 or (use_resume and already_processed):
        print(f"\nOutput files saved in: {args.output}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
