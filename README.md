# Advanced Multiband Image Registration Module

This module implements an advanced system for automatic registration of 5-band misaligned multiband images using multiple techniques: SLIC (Simple Linear Iterative Clustering), ORB feature matching, robust affine transformations, and phase cross-correlation.

## Advanced Features

- **Multiband image support**: Handles groups of 5 TIFF images per band
- **Multiple algorithms**: SLIC, feature matching, phase correlation and hybrid method
- **Robust registration**: Uses RANSAC for robust affine transformations
- **Automatic enhancement**: CLAHE and histogram matching to improve coherence
- **Metadata preservation**: Maintains CRS, geotransformations and original tags
- **GeoTIFF support**: Full compatibility with geospatial files
- **Resume functionality**: Automatically resumes from where interrupted
- **Input flexibility**: Accepts single image groups or multiple folders
- **Unified output**: Produces TIFF files with 5 aligned layers
- **Intuitive CLI**: Command-line interface with advanced parameters

## Installation

1. Clone or download the project
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Input File Format

The module expects TIFF files with the following naming pattern:
- `IMG_xxxx_1.tif` - Band 1
- `IMG_xxxx_2.tif` - Band 2
- `IMG_xxxx_3.tif` - Band 3
- `IMG_xxxx_4.tif` - Band 4
- `IMG_xxxx_5.tif` - Band 5

Where `xxxx` is a common numeric identifier for all bands of the same group.

## Usage

### Command Line Interface

#### Process a single image group:
```bash
python main.py -i IMG_1234_1.tif -o ./output/
```

#### Process all images in a folder:
```bash
python main.py -i ./input_folder/ -o ./output/
```

#### With custom parameters:
```bash
python main.py -i ./input/ -o ./output/ --segments 2000 --compactness 15 --reference-band 3 --method hybrid
```

#### Available registration methods:
```bash
# Hybrid method (recommended) - combines feature matching and SLIC
python main.py -i ./input/ -o ./output/ --method hybrid

# Feature matching only with ORB
python main.py -i ./input/ -o ./output/ --method features

# SLIC-based registration only
python main.py -i ./input/ -o ./output/ --method slic

# Phase cross-correlation only
python main.py -i ./input/ -o ./output/ --method phase

# Metadata preservation (default behavior)
python main.py -i ./input/ -o ./output/

# Disable metadata preservation (only if necessary)
python main.py -i ./input/ -o ./output/ --no-metadata

# Force complete reprocessing (ignore existing files)
python main.py -i ./input/ -o ./output/ --no-resume
```

### Available Parameters

- `-i, --input`: Single file path or folder (required)
- `-o, --output`: Output directory (required)
- `--segments`: Number of superpixels for SLIC (default: 1000)
- `--compactness`: Compactness parameter for SLIC (default: 10.0)
- `--sigma`: Sigma for Gaussian filter (default: 1.0)
- `--reference-band`: Reference band 1-5 (default: 1)
- `--method`: Registration method: hybrid, features, slic, phase (default: hybrid)
- `--no-metadata`: Disable geospatial metadata preservation (default: always preserve)
- `--resume`: Resume from where interrupted, skipping already processed files (default: True)
- `--no-resume`: Force reprocessing of all files, even if already existing
- `--verbose, -v`: Verbose output

### Programmatic Usage

```python
from image_registration import ImageRegistration
from utils import find_image_groups, create_output_filename

# Initialize registrator
registrator = ImageRegistration(
    n_segments=1000,
    compactness=10.0,
    reference_band=1
)

# Find image groups
groups = find_image_groups("./input_folder/")

# Process each group
for base_name, band_paths in groups.items():
    output_path = create_output_filename(base_name, "./output/")
    success = registrator.process_image_group(band_paths, output_path)
    print(f"Group {base_name}: {'OK' if success else 'ERROR'}")
```

## Advanced Algorithm

### Hybrid Method (Recommended)
1. **Loading**: The 5 bands are loaded and validated
2. **Advanced pre-processing**:
   - Normalization and contrast enhancement with CLAHE
   - Gaussian filter for noise reduction
   - Histogram matching towards reference band
3. **Feature matching**:
   - Keypoint detection with ORB
   - Robust descriptor matching
   - Affine transformation estimation with RANSAC
4. **SLIC fallback**: If feature matching fails:
   - SLIC segmentation into superpixels
   - Matching based on intensity and area similarity
   - Transformation estimation from matched centroids
5. **Final fallback**: Phase cross-correlation for simple shift
6. **Alignment**: Application of affine transformations to original images
7. **Output**: Saving of aligned multiband TIFF file

### Advantages of Hybrid Method
- **Robustness**: Multiple fallback algorithms
- **Precision**: Affine transformations handle rotations and scaling
- **Adaptability**: Automatically adapts to type of misalignment

## Output

For each group of 5 input bands, a TIFF file is produced with:
- 5 layers corresponding to aligned bands
- Name format: `IMG_xxxx_registered.tif`
- Preservation of original resolution and depth
- **Preserved metadata** (if enabled):
  - Coordinate system (CRS)
  - Geotransformation
  - Custom tags
  - Band descriptions
  - Compression information

## Geospatial Metadata Management

The module **automatically preserves all geospatial metadata** by default:

### Supported Metadata
- **CRS (Coordinate Reference System)**: EPSG, WKT, PROJ4
- **Geotransformation**: Geographic pixel-to-world coordinates
- **TIFF Tags**: Custom metadata (sensor, date, processing level)
- **Band descriptions**: Names and descriptions for each band
- **Compression parameters**: LZW, tiling, block size

### Automatic Validation
- Verify CRS consistency across all bands
- Check dimensions and transformations
- Warnings for inconsistent metadata

### Transformation Updates
- Geotransformations are updated to reflect registration
- Maintenance of geographic precision
- Compatibility with GIS software (QGIS, ArcGIS, GDAL)

## Resume Functionality

The module supports **automatic processing resumption**:

### Automatic Behavior
- **Scans output folder**: Identifies already processed files
- **Skips completed groups**: Avoids unnecessary reprocessing
- **Continues from interruption**: Resumes with remaining groups
- **Detailed reporting**: Shows progress and skipped files

### Advantages
- **Time saving**: Doesn't reprocess already completed files
- **Robustness**: Handles interruptions (Ctrl+C, crashes, etc.)
- **Flexibility**: Allows incremental processing
- **Safety**: Preserves work already done

### Usage Examples

#### Normal Processing (with Resume)
```bash
# First execution - processes all files
python main.py -i ./input/ -o ./output/

# Second execution - skips already done files
python main.py -i ./input/ -o ./output/
# Output: "Found 50 total groups: 30 already processed (skipped), 20 to process"
```

#### Force Reprocessing
```bash
# Reprocess everything, ignoring existing files
python main.py -i ./input/ -o ./output/ --no-resume
```

## Dependencies

- numpy: Numerical array operations
- opencv-python: Image processing and geometric transformations
- scikit-image: Segmentation and registration algorithms
- tifffile: I/O for TIFF files
- Pillow: Additional support for image formats
- tqdm: Progress bars

## Limitations

- Supports only complete groups of 5 bands
- Optimized for translational shifts (not rotations or complex deformations)
- Requires images to have similar dimensions

## Troubleshooting

### Error "Invalid image group"
- Verify there are exactly 5 files per group
- Check that names follow the pattern `IMG_xxxx_N.tif`
- Ensure all files exist and are accessible

### Poor registration results
- Try increasing the number of SLIC segments (`--segments`)
- Modify the compactness parameter (`--compactness`)
- Change the reference band (`--reference-band`)

### Memory errors
- Reduce the number of SLIC segments
- Process images in smaller batches
