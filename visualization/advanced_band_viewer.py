#!/usr/bin/env python3
"""
Visualizzatore avanzato per bande multispettrali MicaSense RedEdge
Modalità multiple: singole bande, composizioni RGB, NDVI
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets
import tifffile
import argparse
import os
import sys

class AdvancedBandViewer:
    """Visualizzatore avanzato con modalità multiple"""
    
    def __init__(self, bands_data, file_path):
        self.bands_data = bands_data
        self.file_path = file_path
        self.current_band = 0
        self.num_bands = bands_data.shape[0]
        self.updating_slider = False
        
        # Modalità di visualizzazione
        self.view_modes = {
            'bands': 'Singole Bande',
            'rgb_natural': 'RGB Naturale',
            'false_color_ir': 'False Color IR',
            'red_edge': 'Red Edge Enhanced',
            'ndvi_like': 'NDVI-like',
            'ndvi': 'NDVI'
        }
        self.current_mode = 'bands'
        
        # Informazioni bande MicaSense RedEdge
        self.band_info = {
            0: {"name": "Banda 1 - Blue", "wavelength": "475 nm"},
            1: {"name": "Banda 2 - Green", "wavelength": "560 nm"},
            2: {"name": "Banda 3 - Red", "wavelength": "668 nm"},
            3: {"name": "Banda 4 - Red Edge", "wavelength": "717 nm"},
            4: {"name": "Banda 5 - Near-IR", "wavelength": "840 nm"}
        }
        
        # Composizioni RGB
        self.rgb_compositions = {
            'rgb_natural': (3, 2, 1),      # Red, Green, Blue
            'false_color_ir': (5, 3, 2),  # NIR, Red, Green
            'red_edge': (4, 3, 2),        # Red Edge, Red, Green
            'ndvi_like': (5, 4, 3)        # NIR, Red Edge, Red
        }
        
        # Pre-calcola NDVI
        self.ndvi_data = self.calculate_ndvi()
        
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
    
    def normalize_band(self, band, percentile_range=(2, 98)):
        """Normalizza una banda per la visualizzazione"""
        p_min, p_max = np.percentile(band, percentile_range)
        return np.clip((band - p_min) / (p_max - p_min + 1e-8), 0, 1)
    
    def create_rgb_composite(self, red_band, green_band, blue_band):
        """Crea composizione RGB"""
        # Converti a indici 0-based
        r_idx = red_band - 1
        g_idx = green_band - 1
        b_idx = blue_band - 1
        
        # Normalizza ogni canale
        red_norm = self.normalize_band(self.bands_data[r_idx])
        green_norm = self.normalize_band(self.bands_data[g_idx])
        blue_norm = self.normalize_band(self.bands_data[b_idx])
        
        # Combina in RGB
        rgb_image = np.stack([red_norm, green_norm, blue_norm], axis=2)
        return rgb_image
    
    def setup_plot(self):
        """Configura la finestra di visualizzazione"""
        self.fig, self.ax = plt.subplots(figsize=(14, 10))
        self.fig.suptitle(f'MicaSense RedEdge - Visualizzatore Avanzato\n{os.path.basename(self.file_path)}', 
                         fontsize=14, fontweight='bold')
        
        # Spazio per i controlli
        plt.subplots_adjust(bottom=0.35, left=0.1, right=0.9)
        
        # Mostra la prima banda
        normalized = self.normalize_band(self.bands_data[0])
        self.im = self.ax.imshow(normalized, cmap='gray', aspect='equal')
        self.ax.set_title(self.get_current_title(), fontsize=12, fontweight='bold')
        self.ax.axis('off')
        
        # Colorbar
        self.cbar = plt.colorbar(self.im, ax=self.ax, fraction=0.046, pad=0.04)
        self.cbar.set_label('Intensità', rotation=270, labelpad=15)
        
        # Controlli per modalità bande
        self.setup_band_controls()
        
        # Controlli per modalità di visualizzazione
        self.setup_mode_controls()
        
        # Info panel
        self.setup_info_panel()
        
        # Eventi tastiera
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        self.update_display()
    
    def setup_band_controls(self):
        """Configura controlli per navigazione bande"""
        # Slider per bande (visibile solo in modalità bands)
        self.slider_ax = plt.axes([0.2, 0.25, 0.5, 0.03])
        self.band_slider = widgets.Slider(
            self.slider_ax, 'Banda', 1, self.num_bands,
            valinit=1, valfmt='%d', valstep=1
        )
        self.band_slider.on_changed(self.update_band_slider)
        
        # Bottoni navigazione bande
        prev_ax = plt.axes([0.1, 0.25, 0.08, 0.04])
        next_ax = plt.axes([0.72, 0.25, 0.08, 0.04])
        self.prev_button = widgets.Button(prev_ax, '◀ Prev')
        self.next_button = widgets.Button(next_ax, 'Next ▶')
        self.prev_button.on_clicked(self.prev_band)
        self.next_button.on_clicked(self.next_band)
    
    def setup_mode_controls(self):
        """Configura controlli per modalità di visualizzazione"""
        # Bottoni per modalità
        mode_buttons_y = 0.15
        button_width = 0.12
        button_height = 0.04
        button_spacing = 0.14
        
        self.mode_buttons = {}
        modes = ['bands', 'rgb_natural', 'false_color_ir', 'red_edge', 'ndvi_like', 'ndvi']
        labels = ['Bande', 'RGB', 'False IR', 'Red Edge', 'NDVI-like', 'NDVI']
        
        for i, (mode, label) in enumerate(zip(modes, labels)):
            x_pos = 0.1 + i * button_spacing
            button_ax = plt.axes([x_pos, mode_buttons_y, button_width, button_height])
            button = widgets.Button(button_ax, label)
            button.on_clicked(lambda event, m=mode: self.set_mode(m))
            self.mode_buttons[mode] = button
    
    def setup_info_panel(self):
        """Configura pannello informazioni"""
        info_ax = plt.axes([0.1, 0.02, 0.8, 0.1])
        info_ax.axis('off')
        self.info_text = info_ax.text(0.5, 0.5, self.get_info_text(), 
                                     ha='center', va='center', fontsize=9,
                                     bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    def get_current_title(self):
        """Genera titolo per la modalità corrente"""
        if self.current_mode == 'bands':
            info = self.band_info.get(self.current_band, {"name": f"Banda {self.current_band+1}", "wavelength": "N/A"})
            return f"{info['name']} ({info['wavelength']})"
        elif self.current_mode == 'ndvi':
            return "NDVI (Normalized Difference Vegetation Index)"
        else:
            mode_name = self.view_modes[self.current_mode]
            if self.current_mode in self.rgb_compositions:
                bands = self.rgb_compositions[self.current_mode]
                return f"{mode_name} (R:{bands[0]}, G:{bands[1]}, B:{bands[2]})"
            return mode_name
    
    def get_info_text(self):
        """Genera testo informativo"""
        if self.current_mode == 'bands':
            return ("Modalità Bande: ← → (frecce) | 1-5 (numeri) | Mouse (slider) | "
                    "Bottoni modalità | S (salva) | Q (esci)")
        else:
            return ("Modalità Composizione: Bottoni modalità per cambiare | "
                    "S (salva) | Q (esci)")
    
    def update_display(self):
        """Aggiorna la visualizzazione"""
        if self.current_mode == 'bands':
            # Modalità singole bande
            normalized = self.normalize_band(self.bands_data[self.current_band])
            self.im.set_array(normalized)
            self.im.set_cmap('gray')
            self.cbar.set_label('Intensità Normalizzata', rotation=270, labelpad=15)
            
            # Aggiorna slider
            if not self.updating_slider:
                self.updating_slider = True
                self.band_slider.set_val(self.current_band + 1)
                self.updating_slider = False
            
            # Mostra controlli bande
            self.slider_ax.set_visible(True)
            self.prev_button.ax.set_visible(True)
            self.next_button.ax.set_visible(True)
            
        elif self.current_mode == 'ndvi':
            # Modalità NDVI
            self.im.set_array(self.ndvi_data)
            self.im.set_cmap('RdYlGn')  # Colormap per NDVI
            self.im.set_clim(-1, 1)
            self.cbar.set_label('NDVI', rotation=270, labelpad=15)
            
            # Nascondi controlli bande
            self.slider_ax.set_visible(False)
            self.prev_button.ax.set_visible(False)
            self.next_button.ax.set_visible(False)
            
        else:
            # Modalità RGB
            if self.current_mode in self.rgb_compositions:
                bands = self.rgb_compositions[self.current_mode]
                rgb_image = self.create_rgb_composite(bands[0], bands[1], bands[2])
                self.im.set_array(rgb_image)
                self.im.set_cmap(None)  # Rimuovi colormap per RGB
                self.cbar.set_label('RGB', rotation=270, labelpad=15)
            
            # Nascondi controlli bande
            self.slider_ax.set_visible(False)
            self.prev_button.ax.set_visible(False)
            self.next_button.ax.set_visible(False)
        
        # Aggiorna titolo e info
        self.ax.set_title(self.get_current_title(), fontsize=12, fontweight='bold')
        self.info_text.set_text(self.get_info_text())
        
        # Evidenzia bottone modalità corrente
        for mode, button in self.mode_buttons.items():
            if mode == self.current_mode:
                button.color = 'lightgreen'
                button.hovercolor = 'green'
            else:
                button.color = 'lightgray'
                button.hovercolor = 'gray'
        
        self.fig.canvas.draw()
    
    def set_mode(self, mode):
        """Cambia modalità di visualizzazione"""
        if mode != self.current_mode:
            self.current_mode = mode
            self.update_display()
    
    def update_band_slider(self, val):
        """Callback per slider bande"""
        if self.updating_slider or self.current_mode != 'bands':
            return
        
        new_band = int(val) - 1
        if new_band != self.current_band:
            self.current_band = new_band
            self.update_display()
    
    def prev_band(self, event):
        """Banda precedente"""
        if self.current_mode == 'bands':
            self.current_band = (self.current_band - 1) % self.num_bands
            self.update_display()
    
    def next_band(self, event):
        """Banda successiva"""
        if self.current_mode == 'bands':
            self.current_band = (self.current_band + 1) % self.num_bands
            self.update_display()
    
    def on_key_press(self, event):
        """Gestisce eventi tastiera"""
        if self.current_mode == 'bands':
            if event.key in ['left', 'down']:
                self.prev_band(None)
            elif event.key in ['right', 'up']:
                self.next_band(None)
            elif event.key in '12345':
                band_num = int(event.key) - 1
                if band_num < self.num_bands:
                    self.current_band = band_num
                    self.update_display()
        
        # Tasti per modalità
        if event.key == 'b':
            self.set_mode('bands')
        elif event.key == 'r':
            self.set_mode('rgb_natural')
        elif event.key == 'f':
            self.set_mode('false_color_ir')
        elif event.key == 'e':
            self.set_mode('red_edge')
        elif event.key == 'n':
            self.set_mode('ndvi')
        elif event.key == 'l':
            self.set_mode('ndvi_like')
        elif event.key == 's':
            self.save_current_view()
        elif event.key == 'q':
            plt.close(self.fig)
    
    def save_current_view(self):
        """Salva la vista corrente"""
        filename = f"{self.current_mode}_{os.path.splitext(os.path.basename(self.file_path))[0]}.png"
        
        # Crea figura temporanea per salvataggio
        fig_save, ax_save = plt.subplots(figsize=(10, 8))
        
        if self.current_mode == 'bands':
            normalized = self.normalize_band(self.bands_data[self.current_band])
            im_save = ax_save.imshow(normalized, cmap='gray', aspect='equal')
        elif self.current_mode == 'ndvi':
            im_save = ax_save.imshow(self.ndvi_data, cmap='RdYlGn', vmin=-1, vmax=1, aspect='equal')
        else:
            bands = self.rgb_compositions[self.current_mode]
            rgb_image = self.create_rgb_composite(bands[0], bands[1], bands[2])
            im_save = ax_save.imshow(rgb_image, aspect='equal')
        
        ax_save.set_title(self.get_current_title(), fontsize=14, fontweight='bold')
        ax_save.axis('off')
        
        if self.current_mode != 'rgb_natural' and self.current_mode not in self.rgb_compositions:
            plt.colorbar(im_save, ax=ax_save, fraction=0.046, pad=0.04)
        
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close(fig_save)
        
        print(f"Vista {self.current_mode} salvata come: {filename}")
    
    def show(self):
        """Mostra il visualizzatore"""
        print("\n🎯 VISUALIZZATORE AVANZATO MULTISPETTRALE")
        print("=" * 60)
        print("MODALITÀ DISPONIBILI:")
        print("• Bande: Singole bande in B&N")
        print("• RGB: Composizione naturale (3,2,1)")
        print("• False IR: Vegetazione in rosso (5,3,2)")
        print("• Red Edge: Stress vegetazione (4,3,2)")
        print("• NDVI-like: Salute vegetazione (5,4,3)")
        print("• NDVI: Indice vegetazione (-1 a +1)")
        print()
        print("CONTROLLI:")
        print("• Bottoni: Cambia modalità")
        print("• Frecce ← →: Naviga bande (solo modalità Bande)")
        print("• Numeri 1-5: Vai alla banda (solo modalità Bande)")
        print("• Tasti rapidi: B(ande), R(GB), F(alse), E(dge), N(DVI), L(ike)")
        print("• S: Salva vista corrente")
        print("• Q: Esci")
        print("=" * 60)
        
        plt.show()

def load_multiband_image(file_path):
    """Carica immagine multibanda"""
    try:
        with tifffile.TiffFile(file_path) as tif:
            data = tif.asarray()
            print(f"File caricato: {file_path}")
            print(f"Shape: {data.shape}, Dtype: {data.dtype}")
            
            if len(data.shape) != 3:
                raise ValueError(f"File deve essere multibanda, trovato shape: {data.shape}")
            
            if data.shape[0] < 5:
                print(f"⚠️  Attenzione: Trovate solo {data.shape[0]} bande (attese 5 per NDVI)")
            
            return data
            
    except Exception as e:
        print(f"Errore nel caricamento: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Visualizzatore avanzato multispettrale MicaSense RedEdge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi d'uso:

1. Visualizzatore completo:
   python advanced_band_viewer.py -i IMG_0001_registered.tif

2. Con file specifico:
   python advanced_band_viewer.py -i /path/to/image.tif

Modalità disponibili:
• Bande: Singole bande navigabili
• RGB: Composizione naturale
• False IR: Vegetazione evidenziata
• Red Edge: Stress vegetazione
• NDVI-like: Composizione salute vegetazione
• NDVI: Indice di vegetazione calcolato

Controlli:
• Bottoni per cambiare modalità
• Frecce per navigare bande
• Tasti rapidi: B, R, F, E, N, L
• S per salvare, Q per uscire
        """
    )
    
    parser.add_argument('-i', '--input', required=True,
                       help='File TIFF multibanda di input')
    
    args = parser.parse_args()
    
    # Verifica file di input
    if not os.path.exists(args.input):
        print(f"Errore: File {args.input} non trovato!")
        sys.exit(1)
    
    # Carica immagine
    print("Caricamento immagine multibanda...")
    bands_data = load_multiband_image(args.input)
    
    if bands_data is None:
        sys.exit(1)
    
    # Crea e mostra visualizzatore
    viewer = AdvancedBandViewer(bands_data, args.input)
    viewer.show()

if __name__ == "__main__":
    main()
