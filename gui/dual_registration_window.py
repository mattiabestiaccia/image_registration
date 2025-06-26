"""
Dual Registration Window - Finestra per registrazione di due immagini singole

Interfaccia specializzata per registrare due immagini singole di dimensioni diverse,
tipicamente un'immagine termica e un'immagine RGB.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import os
from datetime import datetime
from typing import Optional, Dict, Any

try:
    from ..core.dual_image_registration import DualImageRegistration
except ImportError:
    try:
        from core.dual_image_registration import DualImageRegistration
    except ImportError:
        from dual_image_registration import DualImageRegistration


class DualRegistrationWindow:
    """Finestra per registrazione di immagini duali"""
    
    def __init__(self, parent=None):
        """
        Inizializza la finestra
        
        Args:
            parent: Widget parent (opzionale)
        """
        self.parent = parent
        
        # Crea finestra
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title("Registrazione Dual Image - Termica + RGB")
        self.window.geometry("1200x800")
        
        # Dati
        self.reference_path = None
        self.target_path = None
        self.registration_result = None
        self.registrator = DualImageRegistration()
        
        # Setup UI
        self.setup_ui()
        
        # Se è una finestra principale, gestisci la chiusura
        if not parent:
            self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """Configura l'interfaccia utente"""
        # Frame principale
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Titolo
        title_label = ttk.Label(main_frame, text="Registrazione Dual Image", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Frame selezione file
        self.setup_file_selection(main_frame)
        
        # Frame controlli
        self.setup_controls(main_frame)
        
        # Frame visualizzazione
        self.setup_visualization(main_frame)
        
        # Frame stato
        self.setup_status_bar(main_frame)
    
    def setup_file_selection(self, parent):
        """Setup area selezione file"""
        file_frame = ttk.LabelFrame(parent, text="Selezione Immagini", padding=10)
        file_frame.pack(fill="x", pady=(0, 10))
        
        # Reference image (RGB grande)
        ref_frame = ttk.Frame(file_frame)
        ref_frame.pack(fill="x", pady=2)
        
        ttk.Label(ref_frame, text="Immagine RGB (grande):").pack(side="left")
        self.ref_path_var = tk.StringVar()
        ref_entry = ttk.Entry(ref_frame, textvariable=self.ref_path_var, state="readonly")
        ref_entry.pack(side="left", fill="x", expand=True, padx=(10, 5))
        ttk.Button(ref_frame, text="Sfoglia...", 
                  command=self.select_reference_image).pack(side="right")
        
        # Target image (termica piccola)
        target_frame = ttk.Frame(file_frame)
        target_frame.pack(fill="x", pady=2)
        
        ttk.Label(target_frame, text="Immagine Termica (piccola):").pack(side="left")
        self.target_path_var = tk.StringVar()
        target_entry = ttk.Entry(target_frame, textvariable=self.target_path_var, state="readonly")
        target_entry.pack(side="left", fill="x", expand=True, padx=(10, 5))
        ttk.Button(target_frame, text="Sfoglia...", 
                  command=self.select_target_image).pack(side="right")
    
    def setup_controls(self, parent):
        """Setup controlli registrazione"""
        controls_frame = ttk.LabelFrame(parent, text="Controlli Registrazione", padding=10)
        controls_frame.pack(fill="x", pady=(0, 10))
        
        # Metodo registrazione
        method_frame = ttk.Frame(controls_frame)
        method_frame.pack(side="left", padx=(0, 20))
        
        ttk.Label(method_frame, text="Metodo:").pack()
        self.method_var = tk.StringVar(value="hybrid")
        method_combo = ttk.Combobox(method_frame, textvariable=self.method_var,
                                   values=["hybrid", "features", "phase"],
                                   state="readonly", width=15)
        method_combo.pack()
        
        # Opzioni
        options_frame = ttk.Frame(controls_frame)
        options_frame.pack(side="left", padx=(0, 20))
        
        self.scale_estimation_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Stima scala automatica",
                       variable=self.scale_estimation_var).pack(anchor="w")
        
        self.enhance_contrast_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Migliora contrasto",
                       variable=self.enhance_contrast_var).pack(anchor="w")
        
        # Modalità visualizzazione
        viz_frame = ttk.Frame(controls_frame)
        viz_frame.pack(side="left", padx=(0, 20))
        
        ttk.Label(viz_frame, text="Visualizzazione:").pack()
        self.viz_mode_var = tk.StringVar(value="thermal_overlay")
        viz_combo = ttk.Combobox(viz_frame, textvariable=self.viz_mode_var,
                                values=["thermal_overlay", "blend", "checkerboard", "side_by_side"],
                                state="readonly", width=15)
        viz_combo.pack()
        viz_combo.bind("<<ComboboxSelected>>", self.update_visualization)
        
        # Bottoni azione
        action_frame = ttk.Frame(controls_frame)
        action_frame.pack(side="right")
        
        ttk.Button(action_frame, text="🔄 Registra", 
                  command=self.perform_registration).pack(pady=2)
        ttk.Button(action_frame, text="💾 Salva Risultato", 
                  command=self.save_result).pack(pady=2)
    
    def setup_visualization(self, parent):
        """Setup area visualizzazione"""
        viz_frame = ttk.LabelFrame(parent, text="Visualizzazione", padding=5)
        viz_frame.pack(fill="both", expand=True)
        
        # Figura matplotlib
        self.fig = Figure(figsize=(12, 6), dpi=100)
        
        # Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, viz_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Messaggio iniziale
        self.show_initial_message()
    
    def setup_status_bar(self, parent):
        """Setup barra di stato"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill="x", pady=(5, 0))
        
        self.status_var = tk.StringVar(value="Pronto")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side="left")
        
        # Progress bar
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=200)
        self.progress.pack(side="right")
    
    def show_initial_message(self):
        """Mostra messaggio iniziale"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.text(0.5, 0.5, "Seleziona due immagini per iniziare", 
                ha="center", va="center", transform=ax.transAxes,
                fontsize=14, color="gray")
        ax.set_xticks([])
        ax.set_yticks([])
        self.canvas.draw()
    
    def select_reference_image(self):
        """Seleziona immagine di riferimento"""
        file_path = filedialog.askopenfilename(
            title="Seleziona Immagine RGB (Reference)",
            filetypes=[
                ("File immagine", "*.jpg *.jpeg *.png *.tif *.tiff"),
                ("JPEG", "*.jpg *.jpeg"),
                ("TIFF", "*.tif *.tiff"),
                ("PNG", "*.png"),
                ("Tutti i file", "*.*")
            ]
        )
        
        if file_path:
            self.reference_path = file_path
            self.ref_path_var.set(os.path.basename(file_path))
            self.status_var.set(f"Reference: {os.path.basename(file_path)}")
            self.update_preview()
    
    def select_target_image(self):
        """Seleziona immagine target"""
        file_path = filedialog.askopenfilename(
            title="Seleziona Immagine Termica (Target)",
            filetypes=[
                ("File immagine", "*.jpg *.jpeg *.png *.tif *.tiff"),
                ("JPEG", "*.jpg *.jpeg"),
                ("TIFF", "*.tif *.tiff"),
                ("PNG", "*.png"),
                ("Tutti i file", "*.*")
            ]
        )
        
        if file_path:
            self.target_path = file_path
            self.target_path_var.set(os.path.basename(file_path))
            self.status_var.set(f"Target: {os.path.basename(file_path)}")
            self.update_preview()
    
    def update_preview(self):
        """Aggiorna anteprima immagini"""
        if not self.reference_path or not self.target_path:
            return
        
        try:
            # Carica immagini per preview
            ref_img = self.registrator.load_and_preprocess_image(self.reference_path)
            target_img = self.registrator.load_and_preprocess_image(self.target_path)
            
            # Mostra preview
            self.fig.clear()
            
            ax1 = self.fig.add_subplot(121)
            ax1.imshow(ref_img, cmap='gray')
            ax1.set_title(f"RGB Reference\\n{ref_img.shape}")
            ax1.axis('off')
            
            ax2 = self.fig.add_subplot(122)
            ax2.imshow(target_img, cmap='hot')
            ax2.set_title(f"Termica Target\\n{target_img.shape}")
            ax2.axis('off')
            
            self.fig.tight_layout()
            self.canvas.draw()
            
            self.status_var.set("Immagini caricate - Pronto per registrazione")
            
        except Exception as e:
            messagebox.showerror("Errore", f"Errore nel caricamento preview:\\n{e}")
    
    def perform_registration(self):
        """Esegue la registrazione"""
        if not self.reference_path or not self.target_path:
            messagebox.showwarning("Attenzione", "Seleziona entrambe le immagini")
            return
        
        try:
            # Aggiorna impostazioni registratore
            self.registrator.registration_method = self.method_var.get()
            self.registrator.scale_factor_estimation = self.scale_estimation_var.get()
            self.registrator.enhance_contrast = self.enhance_contrast_var.get()
            
            # Mostra progress
            self.progress.start()
            self.status_var.set("Registrazione in corso...")
            self.window.update()
            
            # Esegui registrazione
            self.registration_result = self.registrator.register_images(
                self.reference_path, self.target_path
            )
            
            # Ferma progress
            self.progress.stop()
            
            # Aggiorna visualizzazione
            self.update_visualization()
            
            # Status
            method = self.registration_result['method_used']
            scale = self.registration_result['scale_factor']
            self.status_var.set(f"Registrazione completata - Metodo: {method}, Scala: {scale:.2f}")
            
        except Exception as e:
            self.progress.stop()
            self.status_var.set("Errore nella registrazione")
            messagebox.showerror("Errore Registrazione", f"Errore:\\n{e}")
    
    def update_visualization(self, event=None):
        """Aggiorna visualizzazione risultato"""
        if not self.registration_result:
            return
        
        try:
            # Crea visualizzazione
            overlay_mode = self.viz_mode_var.get()
            overlay_image = self.registrator.create_overlay_visualization(
                self.registration_result, overlay_mode
            )
            
            # Mostra risultato
            self.fig.clear()
            
            if overlay_mode == 'side_by_side':
                # Side by side: due subplot
                ax1 = self.fig.add_subplot(121)
                ax1.imshow(self.registration_result['reference_image'], cmap='gray')
                ax1.set_title("RGB Reference")
                ax1.axis('off')
                
                ax2 = self.fig.add_subplot(122)
                ax2.imshow(self.registration_result['registered_target'], cmap='hot')
                ax2.set_title("Termica Registrata")
                ax2.axis('off')
            else:
                # Single image overlay
                ax = self.fig.add_subplot(111)
                
                if overlay_mode == 'thermal_overlay':
                    ax.imshow(overlay_image)
                else:
                    ax.imshow(overlay_image, cmap='gray')
                
                ax.set_title(f"Overlay - {overlay_mode.replace('_', ' ').title()}")
                ax.axis('off')
            
            self.fig.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Errore Visualizzazione", f"Errore:\\n{e}")
    
    def save_result(self):
        """Salva il risultato della registrazione"""
        if not self.registration_result:
            messagebox.showwarning("Attenzione", "Nessun risultato da salvare")
            return
        
        # Genera nome file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ref_name = os.path.splitext(os.path.basename(self.reference_path))[0]
        target_name = os.path.splitext(os.path.basename(self.target_path))[0]
        overlay_mode = self.viz_mode_var.get()
        
        suggested_name = f"dual_registration_{ref_name}_{target_name}_{overlay_mode}_{timestamp}.png"
        
        # Dialog salvataggio
        file_path = filedialog.asksaveasfilename(
            title="Salva Risultato Registrazione",
            defaultextension=".png",
            initialfile=suggested_name,
            filetypes=[
                ("PNG", "*.png"),
                ("JPEG", "*.jpg"),
                ("TIFF", "*.tif"),
                ("Tutti i file", "*.*")
            ]
        )
        
        if file_path:
            try:
                # Crea visualizzazione per salvataggio
                overlay_image = self.registrator.create_overlay_visualization(
                    self.registration_result, self.viz_mode_var.get()
                )
                
                # Salva
                if self.viz_mode_var.get() == 'thermal_overlay':
                    plt.imsave(file_path, overlay_image)
                else:
                    plt.imsave(file_path, overlay_image, cmap='gray')
                
                # Salva anche metadati
                metadata_path = os.path.splitext(file_path)[0] + "_metadata.txt"
                with open(metadata_path, 'w') as f:
                    f.write(f"Dual Image Registration Metadata\\n")
                    f.write(f"Timestamp: {timestamp}\\n")
                    f.write(f"Reference Image: {self.reference_path}\\n")
                    f.write(f"Target Image: {self.target_path}\\n")
                    f.write(f"Registration Method: {self.registration_result['method_used']}\\n")
                    f.write(f"Scale Factor: {self.registration_result['scale_factor']:.4f}\\n")
                    f.write(f"Overlay Mode: {self.viz_mode_var.get()}\\n")
                    
                    # Transform matrix
                    if self.registration_result['transform_matrix'] is not None:
                        f.write(f"Transform Matrix:\\n")
                        f.write(f"{self.registration_result['transform_matrix']}\\n")
                
                messagebox.showinfo("Successo", 
                    f"Risultato salvato:\\n{file_path}\\n\\nMetadati salvati:\\n{metadata_path}")
                
            except Exception as e:
                messagebox.showerror("Errore Salvataggio", f"Errore:\\n{e}")
    
    def on_closing(self):
        """Gestisce chiusura finestra"""
        self.window.destroy()
    
    def run(self):
        """Esegue la finestra (se standalone)"""
        if not self.parent:
            self.window.mainloop()


# Funzione di test standalone
def main():
    """Test standalone"""
    app = DualRegistrationWindow()
    app.run()


if __name__ == "__main__":
    main()