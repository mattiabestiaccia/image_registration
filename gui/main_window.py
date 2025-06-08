#!/usr/bin/env python3
"""
Main Window - Finestra principale dell'interfaccia Image Registration

Interfaccia tkinter principale che integra selezione file, gestione progetti,
elaborazione immagini e visualizzazione.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
from pathlib import Path

try:
    # Import relativi (quando usato come modulo)
    from .file_selector import FileSelector
    from .project_manager import ProjectManager
    from .image_viewer import ImageViewer
    from ..core.image_registration import ImageRegistration
    from ..utils.utils import find_image_groups
except ImportError:
    # Import assoluti (quando eseguito direttamente)
    from file_selector import FileSelector
    from project_manager import ProjectManager
    from image_viewer import ImageViewer
    from core.image_registration import ImageRegistration
    from utils.utils import find_image_groups


class MainWindow:
    """Finestra principale dell'applicazione"""
    
    def __init__(self):
        """Inizializza la finestra principale"""
        self.root = tk.Tk()
        self.root.title("Image Registration - Multispectral Processing")
        self.root.geometry("1200x800")
        
        # Managers
        self.project_manager = ProjectManager()
        self.image_registration = ImageRegistration()
        
        # Stato applicazione
        self.current_project_path = None
        self.processing_active = False
        
        self.setup_ui()
        self.setup_menu()
        
        # Gestione chiusura finestra
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """Configura l'interfaccia utente"""
        # Frame principale con pannelli
        main_paned = ttk.PanedWindow(self.root, orient="horizontal")
        main_paned.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Pannello sinistro - Controlli
        left_frame = ttk.Frame(main_paned, width=400)
        main_paned.add(left_frame, weight=1)
        
        # Pannello destro - Visualizzazione
        right_frame = ttk.Frame(main_paned, width=800)
        main_paned.add(right_frame, weight=2)
        
        # === PANNELLO SINISTRO ===
        
        # Selettore file
        self.file_selector = FileSelector(left_frame, self.on_selection_change, self.on_file_double_click)
        
        # Informazioni progetto
        self.setup_project_info(left_frame)
        
        # Controlli elaborazione
        self.setup_processing_controls(left_frame)
        
        # === PANNELLO DESTRO ===
        
        # Visualizzatore immagini
        self.image_viewer = ImageViewer(right_frame, self.on_visualization_saved)
        
        # Barra di stato
        self.setup_status_bar()
    
    def setup_project_info(self, parent):
        """Configura il pannello informazioni progetto"""
        self.project_frame = ttk.LabelFrame(parent, text="Progetto Corrente", padding=10)
        self.project_frame.pack(fill="x", padx=10, pady=5)
        
        # Nome progetto
        name_frame = ttk.Frame(self.project_frame)
        name_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(name_frame, text="Nome:").pack(side="left")
        self.project_name_var = tk.StringVar()
        self.project_name_entry = ttk.Entry(name_frame, textvariable=self.project_name_var)
        self.project_name_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        # Bottoni progetto
        buttons_frame = ttk.Frame(self.project_frame)
        buttons_frame.pack(fill="x")
        
        ttk.Button(buttons_frame, text="📁 Nuovo Progetto", 
                  command=self.create_new_project).pack(side="left", padx=(0, 5))
        ttk.Button(buttons_frame, text="📂 Apri Cartella", 
                  command=self.open_project_folder).pack(side="left")
        
        # Info progetto
        self.project_info_label = ttk.Label(self.project_frame, 
                                           text="Nessun progetto attivo", 
                                           foreground="gray")
        self.project_info_label.pack(anchor="w", pady=(5, 0))
    
    def setup_processing_controls(self, parent):
        """Configura i controlli di elaborazione"""
        self.processing_frame = ttk.LabelFrame(parent, text="Elaborazione", padding=10)
        self.processing_frame.pack(fill="x", padx=10, pady=5)
        
        # Parametri registrazione
        params_frame = ttk.LabelFrame(self.processing_frame, text="Parametri", padding=5)
        params_frame.pack(fill="x", pady=(0, 10))
        
        # Metodo registrazione
        ttk.Label(params_frame, text="Metodo:").grid(row=0, column=0, sticky="w")
        self.method_var = tk.StringVar(value="hybrid")
        method_combo = ttk.Combobox(params_frame, textvariable=self.method_var,
                                   values=["hybrid", "slic", "features", "phase"],
                                   state="readonly", width=15)
        method_combo.grid(row=0, column=1, sticky="w", padx=(5, 0))
        
        # Banda di riferimento
        ttk.Label(params_frame, text="Banda rif.:").grid(row=1, column=0, sticky="w")
        self.ref_band_var = tk.IntVar(value=3)
        ref_band_spin = ttk.Spinbox(params_frame, from_=1, to=5, 
                                   textvariable=self.ref_band_var, width=5)
        ref_band_spin.grid(row=1, column=1, sticky="w", padx=(5, 0))
        
        # Bottoni elaborazione
        buttons_frame = ttk.Frame(self.processing_frame)
        buttons_frame.pack(fill="x")
        
        self.process_button = ttk.Button(buttons_frame, text="🚀 Elabora Immagini", 
                                        command=self.start_processing)
        self.process_button.pack(side="left", padx=(0, 5))
        
        self.stop_button = ttk.Button(buttons_frame, text="⏹️ Stop", 
                                     command=self.stop_processing, state="disabled")
        self.stop_button.pack(side="left")
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.processing_frame, 
                                           variable=self.progress_var,
                                           mode="determinate")
        self.progress_bar.pack(fill="x", pady=(10, 0))
        
        # Log elaborazione
        log_frame = ttk.LabelFrame(self.processing_frame, text="Log", padding=5)
        log_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Text widget con scrollbar
        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill="both", expand=True)
        
        self.log_text = tk.Text(text_frame, height=8, wrap="word")
        log_scrollbar = ttk.Scrollbar(text_frame, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")
    
    def setup_status_bar(self):
        """Configura la barra di stato"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill="x", side="bottom")
        
        self.status_label = ttk.Label(self.status_frame, text="Pronto")
        self.status_label.pack(side="left", padx=5)
        
        # Indicatore progetto
        self.project_status_label = ttk.Label(self.status_frame, text="Nessun progetto")
        self.project_status_label.pack(side="right", padx=5)
    
    def setup_menu(self):
        """Configura il menu principale"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menu File
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Nuovo Progetto", command=self.create_new_project)
        file_menu.add_separator()
        file_menu.add_command(label="Esci", command=self.on_closing)
        
        # Menu Visualizza
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Visualizza", menu=view_menu)
        view_menu.add_command(label="Apri Cartella Progetto", command=self.open_project_folder)
        
        # Menu Aiuto
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aiuto", menu=help_menu)
        help_menu.add_command(label="Info", command=self.show_about)
    
    def on_selection_change(self, selected_paths, selection_type):
        """Gestisce il cambio di selezione file"""
        self.log(f"Selezione: {selection_type} - {len(selected_paths)} elementi")

        # Se c'è una selezione e nessun progetto, crea automaticamente
        if selected_paths and not self.current_project_path:
            self.create_new_project()

        # Carica automaticamente la prima immagine nel visualizzatore
        self.load_first_image_in_viewer(selected_paths, selection_type)

    def _group_selected_files(self, selected_paths):
        """
        Raggruppa file selezionati per nome base se hanno struttura IMG_xxxx_n

        Args:
            selected_paths: Lista di path file selezionati

        Returns:
            Dict con gruppi di immagini {base_name: [file_paths]}
        """
        import re

        # Pattern per riconoscere IMG_xxxx_n (dove n è 1-5)
        pattern = r'^(.+)_([1-5])$'

        groups = {}
        ungrouped = {}

        for path in selected_paths:
            filename = os.path.splitext(os.path.basename(path))[0]

            # Verifica se il file ha la struttura IMG_xxxx_n
            match = re.match(pattern, filename)

            if match:
                base_name = match.group(1)  # IMG_xxxx parte
                band_num = int(match.group(2))  # numero banda (1-5)

                if base_name not in groups:
                    groups[base_name] = []

                groups[base_name].append(path)
                self.log(f"📷 Banda {band_num} aggiunta al gruppo {base_name}")
            else:
                # File non strutturato - tratta come gruppo singolo
                ungrouped[filename] = [path]
                self.log(f"📄 File singolo: {filename}")

        # Verifica che i gruppi abbiano tutte le 5 bande
        valid_groups = {}
        for base_name, file_paths in groups.items():
            if len(file_paths) == 5:
                # Ordina i file per numero banda
                sorted_paths = self._sort_band_files(file_paths)
                valid_groups[base_name] = sorted_paths
                self.log(f"✅ Gruppo completo: {base_name} (5 bande)")
            else:
                self.log(f"⚠️ Gruppo incompleto: {base_name} ({len(file_paths)} bande)")
                # Tratta file incompleti come singoli
                for path in file_paths:
                    filename = os.path.splitext(os.path.basename(path))[0]
                    ungrouped[filename] = [path]

        # Combina gruppi validi e file singoli
        all_groups = {**valid_groups, **ungrouped}

        return all_groups

    def _sort_band_files(self, file_paths):
        """
        Ordina i file delle bande per numero (1,2,3,4,5)

        Args:
            file_paths: Lista di path file da ordinare

        Returns:
            Lista ordinata per numero banda
        """
        import re

        def get_band_number(path):
            filename = os.path.splitext(os.path.basename(path))[0]
            match = re.search(r'_([1-5])$', filename)
            return int(match.group(1)) if match else 0

        return sorted(file_paths, key=get_band_number)

    def load_first_image_in_viewer(self, selected_paths, selection_type):
        """Carica la prima immagine disponibile nel visualizzatore"""
        if not selected_paths:
            return

        try:
            first_image_path = None

            if selection_type == "single_file":
                first_image_path = selected_paths[0]
            elif selection_type == "multiple_files":
                first_image_path = selected_paths[0]
            elif selection_type == "folder":
                # Trova il primo file TIFF nella cartella
                tiff_files = self.file_selector._find_tiff_files(selected_paths[0])
                if tiff_files:
                    first_image_path = tiff_files[0]

            if first_image_path and os.path.exists(first_image_path):
                success = self.image_viewer.load_image(first_image_path)
                if success:
                    self.log(f"📷 Immagine caricata: {os.path.basename(first_image_path)}")
                else:
                    self.log(f"❌ Impossibile caricare: {os.path.basename(first_image_path)}")

        except Exception as e:
            self.log(f"❌ Errore caricamento immagine: {e}")

    def create_new_project(self):
        """Crea un nuovo progetto"""
        # Ottieni selezione corrente
        selected_paths, selection_type = self.file_selector.get_selection()
        
        # Nome progetto
        project_name = self.project_name_var.get().strip()
        if not project_name:
            project_name = None  # Auto-generato
        
        # Crea progetto
        try:
            project_path = self.project_manager.create_project(project_name, selected_paths)
            self.current_project_path = project_path

            # Imposta cartella visualizzazioni nel visualizzatore
            project_paths = self.project_manager.get_project_paths()
            if "visualizations" in project_paths:
                self.image_viewer.set_project_visualizations_dir(project_paths["visualizations"])

            # Aggiorna UI
            self.update_project_info()
            self.log(f"✅ Progetto creato: {os.path.basename(project_path)}")

        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile creare progetto:\n{e}")
    
    def update_project_info(self):
        """Aggiorna le informazioni del progetto"""
        if not self.current_project_path:
            self.project_info_label.config(text="Nessun progetto attivo", foreground="gray")
            self.project_status_label.config(text="Nessun progetto")
            return
        
        project_name = os.path.basename(self.current_project_path)
        source_info = self.project_manager.get_source_info()
        
        info_text = f"Cartella: {project_name}\n"
        info_text += f"Sorgenti: {source_info.get('type', 'N/A')} ({source_info.get('count', 0)})"
        
        self.project_info_label.config(text=info_text, foreground="blue")
        self.project_status_label.config(text=f"Progetto: {project_name}")
    
    def open_project_folder(self):
        """Apre la cartella del progetto corrente"""
        if not self.current_project_path:
            messagebox.showwarning("Attenzione", "Nessun progetto attivo")
            return
        
        try:
            os.startfile(self.current_project_path)  # Windows
        except AttributeError:
            os.system(f"xdg-open '{self.current_project_path}'")  # Linux
    
    def start_processing(self):
        """Avvia l'elaborazione delle immagini"""
        if not self.file_selector.has_selection():
            messagebox.showwarning("Attenzione", "Seleziona prima file o cartella")
            return
        
        if not self.current_project_path:
            messagebox.showwarning("Attenzione", "Crea prima un progetto")
            return
        
        # Avvia elaborazione in thread separato
        self.processing_active = True
        self.process_button.config(state="disabled")
        self.stop_button.config(state="normal")
        
        thread = threading.Thread(target=self.process_images_thread)
        thread.daemon = True
        thread.start()
    
    def process_images_thread(self):
        """Thread per elaborazione immagini"""
        try:
            self.log("🚀 Avvio elaborazione...")
            
            # Ottieni file da elaborare
            selected_paths, selection_type = self.file_selector.get_selection()
            
            if selection_type == "folder":
                # Trova gruppi di immagini nella cartella
                image_groups = find_image_groups(selected_paths[0])
            else:
                # File singoli o multipli - raggruppa per nome base se strutturati
                image_groups = self._group_selected_files(selected_paths)
            
            if not image_groups:
                self.log("❌ Nessun gruppo di immagini trovato")
                return
            
            # Configura registrazione
            self.image_registration.reference_band = self.ref_band_var.get() - 1
            self.image_registration.registration_method = self.method_var.get()
            
            # Elabora gruppi
            total_groups = len(image_groups)
            project_paths = self.project_manager.get_project_paths()
            output_dir = project_paths["registered"]
            
            for i, (base_name, file_paths) in enumerate(image_groups.items()):
                if not self.processing_active:
                    break
                
                self.log(f"📷 Elaborazione {base_name}...")
                
                # Aggiorna progress
                progress = (i / total_groups) * 100
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                
                # Crea path output completo
                output_file = os.path.join(output_dir, f"{base_name}_registered.tif")

                # Elabora gruppo
                success = self.image_registration.process_image_group(file_paths, output_file)

                if success:
                    self.log(f"✅ {base_name} completato")
                    # Verifica che il file sia stato creato
                    if os.path.exists(output_file):
                        self.log(f"📁 File salvato: {output_file}")
                        # Aggiorna metadata progetto
                        self.project_manager.add_processed_file(str(file_paths), output_file)
                    else:
                        self.log(f"⚠️ File non trovato: {output_file}")
                        success = False

                    # Carica il primo risultato nel visualizzatore
                    if i == 0:  # Solo per il primo file elaborato
                        self.root.after(0, lambda: self.load_processed_result(output_file))
                else:
                    self.log(f"❌ {base_name} fallito")
            
            self.log("🎉 Elaborazione completata!")
            self.root.after(0, lambda: self.progress_var.set(100))
            
        except Exception as e:
            self.log(f"❌ Errore elaborazione: {e}")
        finally:
            # Ripristina UI
            self.root.after(0, self.processing_finished)
    
    def stop_processing(self):
        """Ferma l'elaborazione"""
        self.processing_active = False
        self.log("⏹️ Elaborazione interrotta")
    
    def processing_finished(self):
        """Chiamato al termine dell'elaborazione"""
        self.processing_active = False
        self.process_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def load_processed_result(self, output_file):
        """Carica un risultato elaborato nel visualizzatore"""
        try:
            if os.path.exists(output_file):
                success = self.image_viewer.load_image(output_file)
                if success:
                    self.log(f"🖼️ Risultato caricato nel visualizzatore: {os.path.basename(output_file)}")
                else:
                    self.log(f"❌ Impossibile visualizzare: {os.path.basename(output_file)}")
        except Exception as e:
            self.log(f"❌ Errore caricamento risultato: {e}")

    def on_file_double_click(self, file_path):
        """Gestisce doppio click su file per caricarlo nel visualizzatore"""
        try:
            success = self.image_viewer.load_image(file_path)
            if success:
                self.log(f"🖼️ Immagine caricata: {os.path.basename(file_path)}")
            else:
                self.log(f"❌ Impossibile caricare: {os.path.basename(file_path)}")
        except Exception as e:
            self.log(f"❌ Errore caricamento: {e}")

    def on_visualization_saved(self, file_path, visualization_type):
        """Chiamato quando viene salvata una visualizzazione"""
        if self.project_manager.current_project:
            self.project_manager.add_visualization(file_path, visualization_type)
            self.log(f"💾 Visualizzazione salvata: {os.path.basename(file_path)}")
    
    def log(self, message):
        """Aggiunge messaggio al log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def show_about(self):
        """Mostra informazioni sull'applicazione"""
        about_text = """Image Registration v1.0
        
Elaborazione avanzata di immagini multispettrali
con registrazione automatica a 5 bande.

Supporta fotocamere MicaSense RedEdge con
algoritmi SLIC, feature matching e correlazione di fase."""
        
        messagebox.showinfo("Informazioni", about_text)
    
    def on_closing(self):
        """Gestisce la chiusura dell'applicazione"""
        if self.processing_active:
            if not messagebox.askokcancel("Elaborazione in corso", 
                                         "Elaborazione in corso. Vuoi davvero uscire?"):
                return
        
        # Pulizia progetto vuoto
        if self.project_manager.current_project:
            self.project_manager.cleanup_empty_project()
        
        self.root.destroy()
    
    def run(self):
        """Avvia l'applicazione"""
        self.root.mainloop()


def launch_gui():
    """Lancia l'interfaccia grafica"""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    launch_gui()
