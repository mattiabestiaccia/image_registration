#!/usr/bin/env python3
"""
Image Viewer - Visualizzatore integrato per immagini multispettrali

Visualizzatore tkinter integrato per immagini multispettrali con supporto
per navigazione bande, composizioni RGB e calcolo NDVI.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import tifffile
from typing import Optional, Callable
import os


class ImageViewer:
    """Visualizzatore integrato per immagini multispettrali"""
    
    def __init__(self, parent, on_save_callback: Callable = None):
        """
        Inizializza il visualizzatore
        
        Args:
            parent: Widget parent tkinter
            on_save_callback: Callback per salvare visualizzazioni
        """
        self.parent = parent
        self.on_save_callback = on_save_callback
        
        # Dati immagine
        self.bands_data = None
        self.current_file = None
        self.current_band = 0
        self.view_mode = "bands"  # "bands", "rgb", "ndvi"
        self.colorbar = None  # Riferimento alla colorbar corrente
        self.project_visualizations_dir = None  # Cartella visualizzazioni progetto
        
        # Nomi bande MicaSense
        self.band_names = [
            "Banda 1 - Blue (475nm)",
            "Banda 2 - Green (560nm)", 
            "Banda 3 - Red (668nm)",
            "Banda 4 - Red Edge (717nm)",
            "Banda 5 - Near-IR (840nm)"
        ]
        
        self.setup_ui()

    def set_project_visualizations_dir(self, visualizations_dir: str):
        """Imposta la cartella visualizzazioni del progetto"""
        self.project_visualizations_dir = visualizations_dir

    def setup_ui(self):
        """Configura l'interfaccia utente"""
        # Frame principale
        self.main_frame = ttk.LabelFrame(self.parent, text="Visualizzatore Immagini", padding=5)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Frame controlli
        controls_frame = ttk.Frame(self.main_frame)
        controls_frame.pack(fill="x", pady=(0, 5))
        
        # Modalità visualizzazione
        mode_frame = ttk.LabelFrame(controls_frame, text="Modalità", padding=5)
        mode_frame.pack(side="left", padx=(0, 10))

        # Menu a tendina per modalità
        self.mode_var = tk.StringVar(value="bands")
        self.mode_options = {
            "bands": "Bande Singole",
            "rgb": "RGB Naturale (3,2,1)",
            "red_edge": "Red Edge Enhanced (4,3,2)",
            "ndvi_like": "NDVI-like (5,4,3)",
            "ndvi": "NDVI (Indice Vegetazione)"
        }

        # Crea lista valori descrittivi per il combobox
        mode_values = list(self.mode_options.values())

        self.mode_combo = ttk.Combobox(
            mode_frame,
            values=mode_values,
            state="readonly",
            width=25
        )
        self.mode_combo.pack(side="left")
        self.mode_combo.bind("<<ComboboxSelected>>", self.on_mode_change)

        # Imposta valore iniziale
        self.mode_combo.set(self.mode_options["bands"])
        
        # Controlli banda (solo per modalità bande)
        self.band_frame = ttk.LabelFrame(controls_frame, text="Banda", padding=5)
        self.band_frame.pack(side="left", padx=(0, 10))
        
        ttk.Button(self.band_frame, text="◀", command=self.prev_band, width=3).pack(side="left")
        self.band_label = ttk.Label(self.band_frame, text="1/5", width=6)
        self.band_label.pack(side="left", padx=5)
        ttk.Button(self.band_frame, text="▶", command=self.next_band, width=3).pack(side="left")
        
        # Bottoni azione
        action_frame = ttk.Frame(controls_frame)
        action_frame.pack(side="right")

        ttk.Button(action_frame, text="📂 Carica", command=self.load_image_dialog).pack(side="left", padx=2)
        ttk.Button(action_frame, text="💾 Salva", command=self.save_current_view).pack(side="left", padx=2)
        ttk.Button(action_frame, text="⚡ Salva Rapido", command=self.quick_save).pack(side="left", padx=2)
        ttk.Button(action_frame, text="📊 Info", command=self.show_image_info).pack(side="left", padx=2)
        
        # Area matplotlib
        self.setup_matplotlib()
        
        # Inizialmente disabilita controlli
        self.set_controls_enabled(False)
    
    def setup_matplotlib(self):
        """Configura l'area matplotlib"""
        # Figura matplotlib
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # Canvas tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, self.main_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Toolbar navigazione
        toolbar_frame = ttk.Frame(self.main_frame)
        toolbar_frame.pack(fill="x")
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        
        # Messaggio iniziale
        self.ax.text(0.5, 0.5, "Nessuna immagine caricata", 
                    ha="center", va="center", transform=self.ax.transAxes,
                    fontsize=14, color="gray")
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw()

    def load_image_dialog(self):
        """Apre dialog per caricare un'immagine"""
        file_path = filedialog.askopenfilename(
            title="Carica Immagine TIFF",
            filetypes=[
                ("File TIFF", "*.tif *.tiff"),
                ("Tutti i file", "*.*")
            ]
        )

        if file_path:
            self.load_image(file_path)

    def load_image(self, file_path: str) -> bool:
        """
        Carica un'immagine multispettrale
        
        Args:
            file_path: Percorso del file TIFF
            
        Returns:
            True se caricamento riuscito
        """
        try:
            # Carica immagine
            self.bands_data = tifffile.imread(file_path)
            self.current_file = file_path
            
            # Verifica formato
            if len(self.bands_data.shape) != 3:
                messagebox.showerror("Errore", "Il file deve essere un TIFF multibanda")
                return False
            
            if self.bands_data.shape[0] != 5:
                messagebox.showwarning("Attenzione", 
                    f"Immagine con {self.bands_data.shape[0]} bande (attese 5)")
            
            # Reset visualizzazione
            self.current_band = 0
            self.view_mode = "bands"
            self.mode_var.set("bands")
            self.mode_combo.set(self.mode_options["bands"])

            # Reset colorbar
            if self.colorbar is not None:
                self.colorbar.remove()
                self.colorbar = None
            
            # Abilita controlli
            self.set_controls_enabled(True)
            
            # Aggiorna visualizzazione
            self.update_display()
            
            return True
            
        except Exception as e:
            messagebox.showerror("Errore Caricamento", f"Impossibile caricare l'immagine:\n{e}")
            return False
    
    def set_controls_enabled(self, enabled: bool):
        """Abilita/disabilita controlli"""
        state = "normal" if enabled else "disabled"
        
        # Controlli modalità
        for child in self.mode_var.get():
            pass  # I radiobutton si gestiscono automaticamente
        
        # Controlli banda
        for child in self.band_frame.winfo_children():
            if isinstance(child, ttk.Button):
                child.config(state=state)
    
    def update_mode_display(self):
        """Aggiorna il display del combobox con nomi descrittivi"""
        current_mode = self.mode_var.get()
        if current_mode in self.mode_options:
            self.mode_combo.set(self.mode_options[current_mode])

    def on_mode_change(self, event=None):
        """Gestisce il cambio di modalità dal combobox"""
        # Trova la chiave corrispondente al valore selezionato
        selected_display = self.mode_combo.get()

        # Trova la chiave corrispondente
        for key, value in self.mode_options.items():
            if value == selected_display:
                self.view_mode = key
                self.mode_var.set(key)
        
                break

        self.update_band_controls_visibility()
        self.update_display()

    def change_view_mode(self):
        """Cambia modalità di visualizzazione (compatibilità)"""
        self.view_mode = self.mode_var.get()
        self.update_mode_display()
        self.update_band_controls_visibility()
        self.update_display()

    def update_band_controls_visibility(self):
        """Mostra/nasconde controlli banda in base alla modalità"""
        if self.view_mode == "bands":
            # Mostra controlli banda
            for child in self.band_frame.winfo_children():
                child.pack(side="left", padx=2)
        else:
            # Nascondi controlli banda (ma mantieni il frame)
            pass  # I controlli rimangono visibili ma disabilitati per semplicità
    
    def prev_band(self):
        """Banda precedente"""
        if self.bands_data is None:
            return
        
        self.current_band = (self.current_band - 1) % self.bands_data.shape[0]
        if self.view_mode == "bands":
            self.update_display()
    
    def next_band(self):
        """Banda successiva"""
        if self.bands_data is None:
            return
        
        self.current_band = (self.current_band + 1) % self.bands_data.shape[0]
        if self.view_mode == "bands":
            self.update_display()
    
    def update_display(self):
        """Aggiorna la visualizzazione"""
        if self.bands_data is None:
            return

        # Rimuovi colorbar esistente se presente
        if self.colorbar is not None:
            self.colorbar.remove()
            self.colorbar = None

        self.ax.clear()

        try:
            if self.view_mode == "bands":
                self._display_single_band()
            elif self.view_mode == "rgb":
                self._display_rgb()
            elif self.view_mode == "red_edge":
                self._display_red_edge()
            elif self.view_mode == "ndvi_like":
                self._display_ndvi_like()
            elif self.view_mode == "ndvi":
                self._display_ndvi()

            self.canvas.draw()

        except Exception as e:
            messagebox.showerror("Errore Visualizzazione", f"Errore nella visualizzazione:\n{e}")
    
    def _display_single_band(self):
        """Visualizza singola banda"""
        band_data = self.bands_data[self.current_band]
        normalized = self._normalize_band(band_data)
        
        self.ax.imshow(normalized, cmap='gray')
        self.ax.set_title(f"{self.band_names[self.current_band]}")
        self.ax.axis('off')
        
        # Aggiorna label banda
        self.band_label.config(text=f"{self.current_band + 1}/{self.bands_data.shape[0]}")
    
    def _display_rgb(self):
        """Visualizza composizione RGB (bande 3,2,1)"""
        if self.bands_data.shape[0] < 3:
            self.ax.text(0.5, 0.5, "RGB richiede almeno 3 bande", 
                        ha="center", va="center", transform=self.ax.transAxes)
            return
        
        # RGB naturale: Red(3), Green(2), Blue(1) - indici 2,1,0
        rgb = np.stack([
            self._normalize_band(self.bands_data[2]),  # Red
            self._normalize_band(self.bands_data[1]),  # Green  
            self._normalize_band(self.bands_data[0])   # Blue
        ], axis=2)
        
        self.ax.imshow(rgb)
        self.ax.set_title("Composizione RGB Naturale (3,2,1)")
        self.ax.axis('off')

    def _display_red_edge(self):
        """Visualizza composizione Red Edge Enhanced (4,3,2)"""
        if self.bands_data.shape[0] < 4:
            self.ax.text(0.5, 0.5, "Red Edge Enhanced richiede almeno 4 bande",
                        ha="center", va="center", transform=self.ax.transAxes)
            return

        # Red Edge Enhanced: Red Edge(4), Red(3), Green(2) - indici 3,2,1
        red_edge_rgb = np.stack([
            self._normalize_band(self.bands_data[3]),  # Red Edge -> Red channel
            self._normalize_band(self.bands_data[2]),  # Red -> Green channel
            self._normalize_band(self.bands_data[1])   # Green -> Blue channel
        ], axis=2)

        self.ax.imshow(red_edge_rgb)
        self.ax.set_title("Red Edge Enhanced (4,3,2) - Stress Vegetazione")
        self.ax.axis('off')

    def _display_ndvi_like(self):
        """Visualizza composizione NDVI-like (5,4,3)"""
        if self.bands_data.shape[0] < 5:
            self.ax.text(0.5, 0.5, "NDVI-like richiede 5 bande",
                        ha="center", va="center", transform=self.ax.transAxes)
            return

        # NDVI-like: NIR(5), Red Edge(4), Red(3) - indici 4,3,2
        ndvi_like_rgb = np.stack([
            self._normalize_band(self.bands_data[4]),  # NIR -> Red channel
            self._normalize_band(self.bands_data[3]),  # Red Edge -> Green channel
            self._normalize_band(self.bands_data[2])   # Red -> Blue channel
        ], axis=2)

        self.ax.imshow(ndvi_like_rgb)
        self.ax.set_title("NDVI-like (5,4,3) - Salute Vegetazione")
        self.ax.axis('off')

    def _display_ndvi(self):
        """Visualizza NDVI"""
        if self.bands_data.shape[0] < 5:
            self.ax.text(0.5, 0.5, "NDVI richiede 5 bande", 
                        ha="center", va="center", transform=self.ax.transAxes)
            return
        
        # NDVI = (NIR - Red) / (NIR + Red)
        nir = self.bands_data[4].astype(float)  # Banda 5
        red = self.bands_data[2].astype(float)  # Banda 3
        
        # Evita divisione per zero
        denominator = nir + red
        denominator[denominator == 0] = 1
        
        ndvi = (nir - red) / denominator
        
        im = self.ax.imshow(ndvi, cmap='RdYlGn', vmin=-1, vmax=1)
        self.ax.set_title("NDVI (Indice Vegetazione)")
        self.ax.axis('off')

        # Colorbar (salva riferimento per rimozione successiva)
        self.colorbar = self.fig.colorbar(im, ax=self.ax, shrink=0.8)
    
    def _normalize_band(self, band_data: np.ndarray) -> np.ndarray:
        """Normalizza banda per visualizzazione"""
        band_min = np.percentile(band_data, 2)
        band_max = np.percentile(band_data, 98)
        
        if band_max > band_min:
            normalized = (band_data - band_min) / (band_max - band_min)
            return np.clip(normalized, 0, 1)
        else:
            return np.zeros_like(band_data)
    
    def save_current_view(self):
        """Salva la visualizzazione corrente"""
        if self.bands_data is None:
            messagebox.showwarning("Attenzione", "Nessuna immagine caricata")
            return

        # Suggerisci nome file
        if self.current_file:
            base_name = os.path.splitext(os.path.basename(self.current_file))[0]
            suggested_name = f"{base_name}_{self.view_mode}.png"
        else:
            suggested_name = f"visualization_{self.view_mode}.png"

        # Determina directory iniziale (cartella visualizations del progetto se disponibile)
        initial_dir = os.getcwd()
        if hasattr(self, 'project_visualizations_dir') and self.project_visualizations_dir:
            initial_dir = self.project_visualizations_dir
            # Crea la cartella se non esiste
            os.makedirs(initial_dir, exist_ok=True)

        # Dialog salvataggio
        file_path = filedialog.asksaveasfilename(
            title="Salva Visualizzazione",
            defaultextension=".png",
            initialfile=suggested_name,
            initialdir=initial_dir,
            filetypes=[
                ("PNG", "*.png"),
                ("JPEG", "*.jpg"),
                ("PDF", "*.pdf"),
                ("Tutti i file", "*.*")
            ]
        )
        
        if file_path:
            try:
                # Crea la directory se non esiste
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                # Salva la visualizzazione
                self.fig.savefig(file_path, dpi=300, bbox_inches='tight')

                # Verifica che il file sia stato salvato
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    messagebox.showinfo("Successo",
                        f"Visualizzazione salvata:\n{file_path}\n\nDimensione: {file_size:,} bytes")

                    # Notifica callback
                    if self.on_save_callback:
                        self.on_save_callback(file_path, self.view_mode)
                else:
                    messagebox.showerror("Errore", f"File non creato:\n{file_path}")

            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile salvare:\n{e}")

    def quick_save(self):
        """Salva rapidamente nella cartella del progetto"""
        if self.bands_data is None:
            messagebox.showwarning("Attenzione", "Nessuna immagine caricata")
            return

        if not self.project_visualizations_dir:
            messagebox.showwarning("Attenzione", "Nessun progetto attivo. Usa 'Salva' normale.")
            return

        try:
            # Genera nome file automatico
            if self.current_file:
                base_name = os.path.splitext(os.path.basename(self.current_file))[0]
            else:
                base_name = "visualization"

            # Aggiungi timestamp per evitare sovrascritture
            from datetime import datetime
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{base_name}_{self.view_mode}_{timestamp}.png"

            # Path completo
            file_path = os.path.join(self.project_visualizations_dir, filename)

            # Crea directory se non esiste
            os.makedirs(self.project_visualizations_dir, exist_ok=True)

            # Salva
            self.fig.savefig(file_path, dpi=300, bbox_inches='tight')

            # Verifica
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                messagebox.showinfo("Salvataggio Rapido",
                    f"✅ Salvato nel progetto:\n{filename}\n\nDimensione: {file_size:,} bytes")

                # Notifica callback
                if self.on_save_callback:
                    self.on_save_callback(file_path, self.view_mode)
            else:
                messagebox.showerror("Errore", f"File non creato:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Errore Salvataggio Rapido", f"Impossibile salvare:\n{e}")

    def show_image_info(self):
        """Mostra informazioni sull'immagine"""
        if self.bands_data is None:
            messagebox.showwarning("Attenzione", "Nessuna immagine caricata")
            return
        
        info = f"File: {os.path.basename(self.current_file) if self.current_file else 'N/A'}\n"
        info += f"Dimensioni: {self.bands_data.shape[2]} x {self.bands_data.shape[1]} pixel\n"
        info += f"Bande: {self.bands_data.shape[0]}\n"
        info += f"Tipo dati: {self.bands_data.dtype}\n"
        
        if self.view_mode == "bands":
            band_data = self.bands_data[self.current_band]
            info += f"\nBanda corrente: {self.current_band + 1}\n"
            info += f"Min: {band_data.min()}\n"
            info += f"Max: {band_data.max()}\n"
            info += f"Media: {band_data.mean():.2f}\n"
        
        messagebox.showinfo("Informazioni Immagine", info)
