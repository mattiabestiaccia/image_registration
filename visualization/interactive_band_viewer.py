#!/usr/bin/env python3
"""
Visualizzatore interattivo per le 5 bande MicaSense RedEdge
Navigazione con cursore e frecce per scorrere tra le bande
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets
import tifffile
import argparse
import os
import sys

class InteractiveBandViewer:
    """Visualizzatore interattivo per bande multispettrali"""
    
    def __init__(self, bands_data, file_path):
        """
        Inizializza il visualizzatore
        
        Args:
            bands_data: Array con shape (bands, height, width)
            file_path: Percorso del file per il titolo
        """
        self.bands_data = bands_data
        self.file_path = file_path
        self.current_band = 0
        self.num_bands = bands_data.shape[0]
        
        # Informazioni bande MicaSense RedEdge
        self.band_info = {
            0: {"name": "Banda 1 - Blue", "wavelength": "475 nm", "color": "blue"},
            1: {"name": "Banda 2 - Green", "wavelength": "560 nm", "color": "green"},
            2: {"name": "Banda 3 - Red", "wavelength": "668 nm", "color": "red"},
            3: {"name": "Banda 4 - Red Edge", "wavelength": "717 nm", "color": "darkred"},
            4: {"name": "Banda 5 - Near-IR", "wavelength": "840 nm", "color": "purple"}
        }
        
        # Pre-normalizza tutte le bande per performance
        self.normalized_bands = []
        for i in range(self.num_bands):
            normalized = self.normalize_band(self.bands_data[i])
            self.normalized_bands.append(normalized)
        
        self.setup_plot()
        
    def normalize_band(self, band, percentile_range=(2, 98)):
        """Normalizza una banda per la visualizzazione"""
        p_min, p_max = np.percentile(band, percentile_range)
        normalized = np.clip((band - p_min) / (p_max - p_min + 1e-8), 0, 1)
        return normalized
    
    def setup_plot(self):
        """Configura la finestra di visualizzazione"""
        # Crea figura
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.fig.suptitle(f'MicaSense RedEdge - Visualizzatore Interattivo\n{os.path.basename(self.file_path)}', 
                         fontsize=14, fontweight='bold')
        
        # Spazio per i controlli
        plt.subplots_adjust(bottom=0.25, left=0.1, right=0.9)
        
        # Mostra la prima banda
        self.im = self.ax.imshow(self.normalized_bands[0], cmap='gray', aspect='equal')
        self.ax.set_title(self.get_band_title(0), fontsize=12, fontweight='bold')
        self.ax.axis('off')
        
        # Aggiungi colorbar
        self.cbar = plt.colorbar(self.im, ax=self.ax, fraction=0.046, pad=0.04)
        self.cbar.set_label('Intensità Normalizzata', rotation=270, labelpad=15)
        
        # Aggiungi statistiche
        self.stats_text = self.ax.text(0.02, 0.98, '', transform=self.ax.transAxes,
                                      verticalalignment='top', fontsize=10,
                                      bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Crea slider per navigazione bande
        slider_ax = plt.axes([0.2, 0.1, 0.5, 0.03])
        self.band_slider = widgets.Slider(
            slider_ax, 'Banda', 1, self.num_bands, 
            valinit=1, valfmt='%d', valstep=1
        )
        self.band_slider.on_changed(self.update_band_slider)
        
        # Bottoni per navigazione
        prev_ax = plt.axes([0.1, 0.1, 0.08, 0.04])
        next_ax = plt.axes([0.72, 0.1, 0.08, 0.04])
        self.prev_button = widgets.Button(prev_ax, '◀ Prev')
        self.next_button = widgets.Button(next_ax, 'Next ▶')
        self.prev_button.on_clicked(self.prev_band)
        self.next_button.on_clicked(self.next_band)
        
        # Info panel
        info_ax = plt.axes([0.1, 0.02, 0.8, 0.06])
        info_ax.axis('off')
        self.info_text = info_ax.text(0.5, 0.5, self.get_info_text(), 
                                     ha='center', va='center', fontsize=9,
                                     bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        # Connetti eventi tastiera
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        # Aggiorna display iniziale
        self.update_display()
    
    def get_band_title(self, band_idx):
        """Genera titolo per la banda corrente"""
        info = self.band_info.get(band_idx, {"name": f"Banda {band_idx+1}", "wavelength": "N/A"})
        return f"{info['name']} ({info['wavelength']})"
    
    def get_info_text(self):
        """Genera testo informativo"""
        return ("Navigazione: ← → (frecce) | 1-5 (numeri) | Mouse (slider) | "
                "Spazio (info) | S (salva) | Q (esci)")
    
    def update_display(self):
        """Aggiorna la visualizzazione della banda corrente"""
        # Aggiorna immagine
        self.im.set_array(self.normalized_bands[self.current_band])
        self.im.set_clim(0, 1)
        
        # Aggiorna titolo
        self.ax.set_title(self.get_band_title(self.current_band), fontsize=12, fontweight='bold')
        
        # Aggiorna statistiche
        band_data = self.bands_data[self.current_band]
        stats = self.calculate_stats(band_data)
        stats_text = (f"Min: {stats['min']:.0f}\n"
                     f"Max: {stats['max']:.0f}\n"
                     f"Media: {stats['mean']:.0f}\n"
                     f"Std: {stats['std']:.0f}\n"
                     f"Unici: {stats['unique']:,}")
        self.stats_text.set_text(stats_text)
        
        # Aggiorna slider
        self.band_slider.set_val(self.current_band + 1)
        
        # Aggiorna colore del bordo
        info = self.band_info.get(self.current_band, {"color": "black"})
        for spine in self.ax.spines.values():
            spine.set_color(info['color'])
            spine.set_linewidth(3)
        
        # Ridisegna
        self.fig.canvas.draw()
    
    def calculate_stats(self, band_data):
        """Calcola statistiche per una banda"""
        return {
            'min': np.min(band_data),
            'max': np.max(band_data),
            'mean': np.mean(band_data),
            'std': np.std(band_data),
            'unique': len(np.unique(band_data))
        }
    
    def update_band_slider(self, val):
        """Callback per slider"""
        new_band = int(val) - 1
        if new_band != self.current_band:
            self.current_band = new_band
            self.update_display()
    
    def prev_band(self, event):
        """Vai alla banda precedente"""
        self.current_band = (self.current_band - 1) % self.num_bands
        self.update_display()
    
    def next_band(self, event):
        """Vai alla banda successiva"""
        self.current_band = (self.current_band + 1) % self.num_bands
        self.update_display()
    
    def on_key_press(self, event):
        """Gestisce eventi tastiera"""
        if event.key == 'left' or event.key == 'down':
            self.prev_band(None)
        elif event.key == 'right' or event.key == 'up':
            self.next_band(None)
        elif event.key in ['1', '2', '3', '4', '5']:
            band_num = int(event.key) - 1
            if band_num < self.num_bands:
                self.current_band = band_num
                self.update_display()
        elif event.key == ' ':  # Spazio - mostra info dettagliate
            self.show_detailed_info()
        elif event.key == 's':  # S - salva immagine corrente
            self.save_current_band()
        elif event.key == 'q':  # Q - esci
            plt.close(self.fig)
    
    def show_detailed_info(self):
        """Mostra informazioni dettagliate sulla banda corrente"""
        band_data = self.bands_data[self.current_band]
        info = self.band_info.get(self.current_band, {})
        
        stats = self.calculate_stats(band_data)
        
        info_text = f"""
BANDA {self.current_band + 1} - INFORMAZIONI DETTAGLIATE

Nome: {info.get('name', f'Banda {self.current_band + 1}')}
Lunghezza d'onda: {info.get('wavelength', 'N/A')}
Dimensioni: {band_data.shape[0]} x {band_data.shape[1]} pixel

STATISTICHE:
• Minimo: {stats['min']:.0f}
• Massimo: {stats['max']:.0f}
• Media: {stats['mean']:.2f}
• Deviazione standard: {stats['std']:.2f}
• Valori unici: {stats['unique']:,}

PERCENTILI:
• 1%: {np.percentile(band_data, 1):.0f}
• 5%: {np.percentile(band_data, 5):.0f}
• 25%: {np.percentile(band_data, 25):.0f}
• 50% (mediana): {np.percentile(band_data, 50):.0f}
• 75%: {np.percentile(band_data, 75):.0f}
• 95%: {np.percentile(band_data, 95):.0f}
• 99%: {np.percentile(band_data, 99):.0f}
        """
        
        print(info_text)
    
    def save_current_band(self):
        """Salva la banda corrente come immagine"""
        filename = f"band_{self.current_band + 1}_{os.path.splitext(os.path.basename(self.file_path))[0]}.png"
        
        # Crea una figura temporanea per il salvataggio
        fig_save, ax_save = plt.subplots(figsize=(10, 8))
        im_save = ax_save.imshow(self.normalized_bands[self.current_band], cmap='gray', aspect='equal')
        ax_save.set_title(self.get_band_title(self.current_band), fontsize=14, fontweight='bold')
        ax_save.axis('off')
        
        # Aggiungi colorbar
        cbar_save = plt.colorbar(im_save, ax=ax_save, fraction=0.046, pad=0.04)
        cbar_save.set_label('Intensità Normalizzata', rotation=270, labelpad=15)
        
        # Salva
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close(fig_save)
        
        print(f"Banda {self.current_band + 1} salvata come: {filename}")
    
    def show(self):
        """Mostra il visualizzatore"""
        print("\n🎯 VISUALIZZATORE INTERATTIVO BANDE MULTISPETTRALI")
        print("=" * 60)
        print("CONTROLLI:")
        print("• Frecce ← → : Naviga tra le bande")
        print("• Numeri 1-5 : Vai direttamente alla banda")
        print("• Mouse : Usa lo slider per navigare")
        print("• Spazio : Mostra info dettagliate banda corrente")
        print("• S : Salva banda corrente come PNG")
        print("• Q : Esci")
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
                print(f"⚠️  Attenzione: Trovate solo {data.shape[0]} bande (attese 5)")
            
            return data
            
    except Exception as e:
        print(f"Errore nel caricamento: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Visualizzatore interattivo per bande multispettrali MicaSense RedEdge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi d'uso:

1. Visualizza file registrato:
   python interactive_band_viewer.py -i IMG_0001_registered.tif

2. Visualizza con titolo personalizzato:
   python interactive_band_viewer.py -i image.tif

Controlli durante la visualizzazione:
• Frecce ← → : Naviga tra le bande
• Numeri 1-5 : Vai direttamente alla banda
• Spazio : Info dettagliate
• S : Salva banda corrente
• Q : Esci
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
    viewer = InteractiveBandViewer(bands_data, args.input)
    viewer.show()

if __name__ == "__main__":
    main()
