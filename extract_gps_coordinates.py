#!/usr/bin/env python3
"""
Script per estrarre le coordinate GPS da immagini TIFF multispettrali MicaSense RedEdge.
Estrae latitudine, longitudine e altitudine dai metadati EXIF.
"""

import tifffile
import sys
import os
from fractions import Fraction

try:
    import rasterio
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False


def gps_fraction_to_decimal(gps_coord):
    """
    Converte coordinate GPS dal formato frazione (gradi, minuti, secondi) al formato decimale.
    
    Args:
        gps_coord: Tupla di 3 valori (gradi, minuti, secondi) come frazioni o interi
        
    Returns:
        float: Coordinata in formato decimale
    """
    # Gestisce il caso in cui i valori sono già numerici o tuple
    def parse_value(val):
        if isinstance(val, (int, float)):
            return float(val)
        elif isinstance(val, tuple) and len(val) == 2:
            return Fraction(val[0], val[1])
        else:
            return float(val)
    
    # I valori GPS sono in formato (numeratore, denominatore) per ogni componente
    degrees = parse_value(gps_coord[0]) / 10000000  # Diviso per 10^7
    minutes = parse_value(gps_coord[1]) / 10000000  # Diviso per 10^7
    seconds = parse_value(gps_coord[2]) / 10000000  # Diviso per 10^7
    
    return float(degrees + minutes/60 + seconds/3600)


def extract_gps_coordinates(tiff_path):
    """
    Estrae le coordinate GPS da un file TIFF.
    Cerca prima nei tag rasterio (file processati), poi nei tag EXIF (file originali).
    
    Args:
        tiff_path: Percorso al file TIFF
        
    Returns:
        dict: Dizionario con latitudine, longitudine e altitudine
    """
    # Prima prova con rasterio (per file processati)
    if RASTERIO_AVAILABLE:
        try:
            with rasterio.open(tiff_path) as src:
                tags = src.tags()
                gps_data = {}
                
                # Cerca tag GPS nei metadati rasterio
                if 'GPS_LATITUDE' in tags:
                    gps_data['latitude'] = float(tags['GPS_LATITUDE'])
                    gps_data['latitude_ref'] = tags.get('GPS_LATITUDE_REF', 'N')
                
                if 'GPS_LONGITUDE' in tags:
                    gps_data['longitude'] = float(tags['GPS_LONGITUDE'])
                    gps_data['longitude_ref'] = tags.get('GPS_LONGITUDE_REF', 'E')
                
                if 'GPS_ALTITUDE' in tags:
                    gps_data['altitude'] = float(tags['GPS_ALTITUDE'])
                
                if 'GPS_DOP' in tags:
                    gps_data['dop'] = float(tags['GPS_DOP'])
                
                if gps_data:
                    return gps_data
                    
        except Exception:
            pass  # Fallback to tifffile method
    
    # Fallback: prova con tifffile (per file originali)
    try:
        with tifffile.TiffFile(tiff_path) as tif:
            page = tif.pages[0]
            
            # Cerca il tag GPS
            gps_tag = None
            for tag in page.tags:
                if tag.name == 'GPSTag':
                    gps_tag = tag.value
                    break
            
            if not gps_tag:
                return {"error": "Nessun dato GPS trovato nel file"}
            
            # Estrai i dati GPS
            gps_data = {}
            
            # Latitudine
            if 'GPSLatitude' in gps_tag and 'GPSLatitudeRef' in gps_tag:
                lat_decimal = gps_fraction_to_decimal(gps_tag['GPSLatitude'])
                if gps_tag['GPSLatitudeRef'] == 'S':
                    lat_decimal = -lat_decimal
                gps_data['latitude'] = lat_decimal
                gps_data['latitude_ref'] = gps_tag['GPSLatitudeRef']
            
            # Longitudine
            if 'GPSLongitude' in gps_tag and 'GPSLongitudeRef' in gps_tag:
                lon_decimal = gps_fraction_to_decimal(gps_tag['GPSLongitude'])
                if gps_tag['GPSLongitudeRef'] == 'W':
                    lon_decimal = -lon_decimal
                gps_data['longitude'] = lon_decimal
                gps_data['longitude_ref'] = gps_tag['GPSLongitudeRef']
            
            # Altitudine
            if 'GPSAltitude' in gps_tag:
                alt_frac = gps_tag['GPSAltitude']
                altitude = Fraction(alt_frac[0], alt_frac[1])
                gps_data['altitude'] = float(altitude)
                
                # Riferimento altitudine (0 = sopra il livello del mare, 1 = sotto)
                if 'GPSAltitudeRef' in gps_tag:
                    if gps_tag['GPSAltitudeRef'] == 1:
                        gps_data['altitude'] = -gps_data['altitude']
            
            # DOP (Dilution of Precision)
            if 'GPSDOP' in gps_tag:
                dop = gps_tag['GPSDOP']
                if dop[1] != 0:  # Evita divisione per zero
                    gps_data['dop'] = float(Fraction(dop[0], dop[1]))
            
            return gps_data
            
    except Exception as e:
        return {"error": f"Errore nella lettura del file: {str(e)}"}


def main():
    """
    Funzione principale del script.
    """
    if len(sys.argv) != 2:
        print("Uso: python extract_gps_coordinates.py <percorso_file_tiff>")
        sys.exit(1)
    
    tiff_path = sys.argv[1]
    
    if not os.path.exists(tiff_path):
        print(f"Errore: File '{tiff_path}' non trovato")
        sys.exit(1)
    
    print(f"Estrazione coordinate GPS da: {tiff_path}")
    print("-" * 50)
    
    coordinates = extract_gps_coordinates(tiff_path)
    
    if "error" in coordinates:
        print(f"Errore: {coordinates['error']}")
        sys.exit(1)
    
    # Stampa i risultati
    if 'latitude' in coordinates:
        print(f"Latitudine: {coordinates['latitude']:.8f}° {coordinates['latitude_ref']}")
    
    if 'longitude' in coordinates:
        print(f"Longitudine: {coordinates['longitude']:.8f}° {coordinates['longitude_ref']}")
    
    if 'altitude' in coordinates:
        print(f"Altitudine: {coordinates['altitude']:.2f} m")
    
    if 'dop' in coordinates:
        print(f"DOP (Dilution of Precision): {float(coordinates['dop']):.2f}")
    
    # Formato per Google Maps/GPS
    if 'latitude' in coordinates and 'longitude' in coordinates:
        print(f"\nCoordinate decimali:")
        print(f"Lat: {coordinates['latitude']:.8f}, Lon: {coordinates['longitude']:.8f}")
        print(f"\nLink Google Maps:")
        print(f"https://maps.google.com/?q={coordinates['latitude']:.8f},{coordinates['longitude']:.8f}")


if __name__ == "__main__":
    main()