import rasterio
import numpy as np
import matplotlib.pyplot as plt

# Percorso al file GeoTIFF (può essere una singola banda o un multibanda)
tif_path = '/home/brus/Projects/HPL/wst/image_registration/test_output/IMG_0127_registered.tif'

# Apri il file
with rasterio.open(tif_path) as src:
    print(f"File: {tif_path}")
    print(f"Numero di bande: {src.count}")
    print(f"Dimensioni (height, width): {src.height}, {src.width}")
    print(f"Coordinate CRS: {src.crs}")

    # Analizza ogni banda
    for i in range(1, src.count + 1):
        band = src.read(i)
        print(f"\nBanda {i}:")
        print(f"  Min: {np.min(band)}")
        print(f"  Max: {np.max(band)}")
        print(f"  Mean: {np.mean(band):.2f}")
        print(f"  Std: {np.std(band):.2f}")

    # Se contiene almeno 3 bande, visualizza una composizione RGB (Red=3, Green=2, Blue=1)
    if src.count >= 3:
        red = src.read(3)
        green = src.read(2)
        blue = src.read(1)

        # Normalizza per visualizzazione
        def normalize(band):
            return (band - band.min()) / (band.max() - band.min())

        rgb = np.stack([normalize(red), normalize(green), normalize(blue)], axis=-1)

        plt.figure(figsize=(10, 10))
        plt.imshow(rgb)
        plt.title('Composizione RGB (bande 3-2-1)')
        plt.axis('off')
        plt.show()
