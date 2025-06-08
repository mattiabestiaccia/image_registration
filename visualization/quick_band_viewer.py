#!/usr/bin/env python3
"""
Visualizzatore rapido e semplice per bande multispettrali
Uso: python quick_band_viewer.py image.tif
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets
import tifffile
import sys
import os

class QuickBandViewer:
    """Visualizzatore semplice per bande multispettrali"""

    def __init__(self, bands_data, file_path):
        self.bands_data = bands_data
        self.file_path = file_path
        self.current_band = 0
        self.num_bands = bands_data.shape[0]
        self.updating_slider = False  # Flag per evitare loop

        # Modalità di visualizzazione
        self.view_mode = 'bands'  # 'bands', 'rgb', 'ndvi'

        # Nomi bande MicaSense
        self.band_names = [
            "Banda 1 - Blue (475nm)",
            "Banda 2 - Green (560nm)",
            "Banda 3 - Red (668nm)",
            "Banda 4 - Red Edge (717nm)",
            "Banda 5 - Near-IR (840nm)"
        ]

        # Pre-calcola NDVI se possibile
        self.ndvi_data = self.calculate_ndvi() if self.num_bands >= 5 else None

        self.setup_plot()

    def calculate_ndvi(self):
        """Calcola NDVI usando bande 5 (NIR) e 3 (Red)"""
        if self.num_bands >= 5:
            nir = self.bands_data[4].astype(float)  # Banda 5 (NIR)
            red = self.bands_data[2].astype(float)  # Banda 3 (Red)

            # Calcola NDVI evitando divisione per zero
            denominator = nir + red
            ndvi = np.where(denominator != 0, (nir - red) / denominator, 0)

            # Clamp tra -1 e 1
            ndvi = np.clip(ndvi, -1, 1)
            return ndvi
        else:
            return np.zeros_like(self.bands_data[0])

    def create_rgb_composite(self):
        """Crea composizione RGB naturale (bande 3,2,1)"""
        if self.num_bands >= 3:
            red = self.normalize_band(self.bands_data[2])    # Banda 3
            green = self.normalize_band(self.bands_data[1])  # Banda 2
            blue = self.normalize_band(self.bands_data[0])   # Banda 1

            rgb_image = np.stack([red, green, blue], axis=2)
            return rgb_image
        else:
            # Fallback per meno di 3 bande
            gray = self.normalize_band(self.bands_data[0])
            return np.stack([gray, gray, gray], axis=2)

    def normalize_band(self, band):
        """Normalizza banda per visualizzazione"""
        p2, p98 = np.percentile(band, (2, 98))
        return np.clip((band - p2) / (p98 - p2 + 1e-8), 0, 1)
    
    def setup_plot(self):
        """Configura visualizzazione"""
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        plt.subplots_adjust(bottom=0.15)
        
        # Mostra prima banda
        normalized = self.normalize_band(self.bands_data[0])
        self.im = self.ax.imshow(normalized, cmap='gray')
        self.ax.set_title(self.get_title(), fontsize=12, fontweight='bold')
        self.ax.axis('off')
        
        # Slider
        slider_ax = plt.axes([0.2, 0.05, 0.5, 0.03])
        self.slider = widgets.Slider(
            slider_ax, 'Banda', 1, self.num_bands,
            valinit=1, valfmt='%d', valstep=1
        )
        self.slider.on_changed(self.update_band)
        
        # Bottoni navigazione
        prev_ax = plt.axes([0.1, 0.05, 0.08, 0.04])
        next_ax = plt.axes([0.72, 0.05, 0.08, 0.04])
        self.prev_btn = widgets.Button(prev_ax, '◀')
        self.next_btn = widgets.Button(next_ax, '▶')
        self.prev_btn.on_clicked(self.prev_band)
        self.next_btn.on_clicked(self.next_band)

        # Bottoni modalità
        bands_ax = plt.axes([0.1, 0.12, 0.08, 0.04])
        rgb_ax = plt.axes([0.2, 0.12, 0.08, 0.04])
        ndvi_ax = plt.axes([0.3, 0.12, 0.08, 0.04])

        self.bands_btn = widgets.Button(bands_ax, 'Bande')
        self.rgb_btn = widgets.Button(rgb_ax, 'RGB')
        self.ndvi_btn = widgets.Button(ndvi_ax, 'NDVI')

        self.bands_btn.on_clicked(lambda event: self.set_mode('bands'))
        self.rgb_btn.on_clicked(lambda event: self.set_mode('rgb'))
        self.ndvi_btn.on_clicked(lambda event: self.set_mode('ndvi'))
        
        # Eventi tastiera
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        
        self.update_display()
    
    def get_title(self):
        """Titolo per modalità corrente"""
        if self.view_mode == 'bands':
            band_name = (self.band_names[self.current_band]
                        if self.current_band < len(self.band_names)
                        else f"Banda {self.current_band + 1}")
            return f"{band_name}\n{os.path.basename(self.file_path)}"
        elif self.view_mode == 'rgb':
            return f"RGB Naturale (3,2,1)\n{os.path.basename(self.file_path)}"
        elif self.view_mode == 'ndvi':
            return f"NDVI (NIR-Red)/(NIR+Red)\n{os.path.basename(self.file_path)}"
        else:
            return f"{self.view_mode}\n{os.path.basename(self.file_path)}"
    
    def set_mode(self, mode):
        """Cambia modalità di visualizzazione"""
        if mode != self.view_mode:
            self.view_mode = mode
            self.update_display()

    def update_display(self):
        """Aggiorna visualizzazione"""
        if self.view_mode == 'bands':
            # Modalità singole bande
            normalized = self.normalize_band(self.bands_data[self.current_band])
            self.im.set_array(normalized)
            self.im.set_cmap('gray')

            # Aggiorna slider senza triggare callback
            if not self.updating_slider:
                self.updating_slider = True
                self.slider.set_val(self.current_band + 1)
                self.updating_slider = False

            # Mostra controlli bande
            self.slider.ax.set_visible(True)
            self.prev_btn.ax.set_visible(True)
            self.next_btn.ax.set_visible(True)

        elif self.view_mode == 'rgb':
            # Modalità RGB
            rgb_image = self.create_rgb_composite()
            self.im.set_array(rgb_image)
            self.im.set_cmap(None)

            # Nascondi controlli bande
            self.slider.ax.set_visible(False)
            self.prev_btn.ax.set_visible(False)
            self.next_btn.ax.set_visible(False)

        elif self.view_mode == 'ndvi':
            # Modalità NDVI
            if self.ndvi_data is not None:
                self.im.set_array(self.ndvi_data)
                self.im.set_cmap('RdYlGn')
                self.im.set_clim(-1, 1)
            else:
                # Fallback se NDVI non disponibile
                normalized = self.normalize_band(self.bands_data[0])
                self.im.set_array(normalized)
                self.im.set_cmap('gray')

            # Nascondi controlli bande
            self.slider.ax.set_visible(False)
            self.prev_btn.ax.set_visible(False)
            self.next_btn.ax.set_visible(False)

        # Evidenzia bottone modalità corrente
        self.bands_btn.color = 'lightgreen' if self.view_mode == 'bands' else 'lightgray'
        self.rgb_btn.color = 'lightgreen' if self.view_mode == 'rgb' else 'lightgray'
        self.ndvi_btn.color = 'lightgreen' if self.view_mode == 'ndvi' else 'lightgray'

        self.ax.set_title(self.get_title(), fontsize=12, fontweight='bold')
        self.fig.canvas.draw()

    def update_band(self, val):
        """Callback slider"""
        if self.updating_slider:
            return

        new_band = int(val) - 1
        if new_band != self.current_band:
            self.current_band = new_band
            normalized = self.normalize_band(self.bands_data[self.current_band])
            self.im.set_array(normalized)
            self.ax.set_title(self.get_title(), fontsize=12, fontweight='bold')
            self.fig.canvas.draw()

    def prev_band(self, event):
        """Banda precedente"""
        self.current_band = (self.current_band - 1) % self.num_bands
        self.update_display()
    
    def next_band(self, event):
        """Banda successiva"""
        self.current_band = (self.current_band + 1) % self.num_bands
        self.update_display()
    
    def on_key(self, event):
        """Eventi tastiera"""
        # Controlli per modalità bande
        if self.view_mode == 'bands':
            if event.key in ['left', 'down']:
                self.prev_band(None)
            elif event.key in ['right', 'up']:
                self.next_band(None)
            elif event.key in '12345':
                band = int(event.key) - 1
                if band < self.num_bands:
                    self.current_band = band
                    self.update_display()

        # Controlli modalità
        if event.key == 'b':
            self.set_mode('bands')
        elif event.key == 'r':
            self.set_mode('rgb')
        elif event.key == 'n':
            self.set_mode('ndvi')
        elif event.key == 'q':
            plt.close()
    
    def show(self):
        """Mostra visualizzatore"""
        print(f"\n🎯 VISUALIZZATORE MULTISPETTRALE: {os.path.basename(self.file_path)}")
        print("=" * 60)
        print("MODALITÀ DISPONIBILI:")
        print("• Bande: Singole bande in scala di grigi")
        print("• RGB: Composizione naturale (bande 3,2,1)")
        if self.ndvi_data is not None:
            print("• NDVI: Indice di vegetazione (-1 a +1)")
        print()
        print("CONTROLLI:")
        print("• Bottoni: Cambia modalità di visualizzazione")
        print("• Frecce ← →: Naviga bande (solo modalità Bande)")
        print("• Numeri 1-5: Vai alla banda (solo modalità Bande)")
        print("• Tasti rapidi: B(ande), R(GB), N(DVI)")
        print("• Q: Esci")
        print("=" * 60)
        plt.show()

def main():
    if len(sys.argv) != 2:
        print("Uso: python quick_band_viewer.py <file.tif>")
        print("Esempio: python quick_band_viewer.py IMG_0001_registered.tif")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Errore: File {file_path} non trovato!")
        sys.exit(1)
    
    # Carica file
    try:
        with tifffile.TiffFile(file_path) as tif:
            data = tif.asarray()
            print(f"Caricato: {file_path}")
            print(f"Shape: {data.shape}, Dtype: {data.dtype}")
    except Exception as e:
        print(f"Errore: {e}")
        sys.exit(1)
    
    if len(data.shape) != 3:
        print(f"Errore: File deve essere multibanda, shape: {data.shape}")
        sys.exit(1)
    
    # Crea visualizzatore
    viewer = QuickBandViewer(data, file_path)
    viewer.show()

if __name__ == "__main__":
    main()
