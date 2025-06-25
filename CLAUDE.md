# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multispectral image registration system designed for MicaSense RedEdge cameras (5 bands). The system provides automatic registration of multispectral images using advanced algorithms including SLIC superpixels, feature matching, and phase correlation, with a complete GUI interface for visualization and project management.

## Common Commands

### Installation & Dependencies
```bash
# Automatic installation (recommended)
python3 install_dependencies.py

# Manual installation
pip install -r requirements.txt

# Create virtual environment with script
python3 -m venv venv_registration
source venv_registration/bin/activate
pip install -r requirements.txt
```

### Running the Application
```bash
# Start GUI directly
python3 run_gui.py

# Start with virtual environment (Linux/macOS)
./start_gui.sh

# Start with virtual environment (Windows)
start_gui.bat
```

### Development Commands
```bash
# Test critical imports
python3 -c "import numpy, cv2, skimage, tifffile, matplotlib, tkinter, imagecodecs, rasterio"

# Test imagecodecs functionality (critical for compressed TIFF files)
python3 -c "import imagecodecs; import tifffile; import numpy as np; print('imagecodecs working')"
```

## Code Architecture

### Core Structure
- **core/**: Registration algorithms and metadata management
  - `image_registration.py`: Main ImageRegistration class with hybrid, features, slic, and phase registration methods
  - `metadata_utils.py`: MetadataManager for preserving geospatial metadata during registration
- **gui/**: Complete tkinter-based interface
  - `main_window.py`: Main application window and processing orchestration
  - `file_selector.py`: File and folder selection interface
  - `project_manager.py`: Project creation and management
  - `image_viewer.py`: Advanced image visualization with multiple modes
- **utils/**: Support utilities
  - `utils.py`: Image loading, saving, group detection, and file management utilities

### Key Classes and Methods
- **ImageRegistration**: Main registration class
  - `register_image_to_reference()`: Core registration method
  - `register_images_batch()`: Batch processing with progress tracking
  - Registration methods: `hybrid`, `features`, `slic`, `phase`
- **MetadataManager**: Handles geospatial metadata and GPS coordinates preservation
  - `extract_gps_coordinates()`: Extracts GPS data from TIFF EXIF
  - `gps_fraction_to_decimal()`: Converts GPS coordinates to decimal format
  - `save_multiband_with_metadata()`: Preserves GPS coordinates in output files
- **GUI Components**: File selection, project management, and multi-mode visualization

### Registration Methods
- **hybrid** (recommended): Combines feature matching + SLIC superpixels
- **features**: Feature matching only (fast)
- **slic**: SLIC superpixels only (robust)
- **phase**: Phase correlation (fallback)

### File Conventions
- Input files follow pattern: `IMG_xxxx_n.tif` where n is band number (1-5)
- MicaSense RedEdge bands: 1=Blue, 2=Green, 3=Red, 4=Red Edge, 5=Near-IR
- Reference band typically band 3 (Red) for best results
- Projects stored in `projects/` directory with metadata and organized outputs

### Visualization Modes
- RGB Natural (3,2,1), Red Edge Enhanced (4,3,2), NDVI-like (5,4,3)
- NDVI calculation with colorbar
- Single band navigation
- Export to PNG/JPEG/PDF formats

### Critical Dependencies
- **imagecodecs**: Essential for compressed TIFF files (LZW, DEFLATE)
- **rasterio**: Required for geospatial metadata preservation
- **scikit-image**: Core image processing and registration algorithms
- **opencv-python**: Computer vision operations
- **tifffile**: TIFF file handling
- **tkinter**: GUI framework

### GPS Coordinate Preservation
The system automatically extracts and preserves GPS coordinates from MicaSense RedEdge images:
- **Extraction**: GPS data (latitude, longitude, altitude) from TIFF EXIF metadata
- **Preservation**: GPS coordinates maintained through registration process
- **Output**: GPS information saved as tags in registered multiband TIFF files
- **Format**: Decimal degrees with reference directions (N/S, E/W)
- **Additional data**: DOP (Dilution of Precision) when available

### Error Handling
The system includes comprehensive error handling for:
- Missing dependencies with specific installation instructions
- File format validation and compatibility checking
- Registration failure fallbacks with alternative methods
- Metadata preservation errors with graceful degradation
- GPS extraction failures (continues without GPS data)