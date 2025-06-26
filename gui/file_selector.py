#!/usr/bin/env python3
"""
File Selector - Componenti per selezione file e cartelle

Fornisce widget tkinter per la selezione di immagini singole, multiple
o cartelle per l'elaborazione multispettrale.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pathlib import Path
from typing import List, Optional, Callable


class FileSelector:
    """Widget per selezione file e cartelle con preview"""

    def __init__(self, parent, on_selection_change: Callable = None, on_file_double_click: Callable = None):
        """
        Inizializza il selettore file

        Args:
            parent: Widget parent tkinter
            on_selection_change: Callback chiamato quando cambia la selezione
            on_file_double_click: Callback chiamato al doppio click su un file
        """
        self.parent = parent
        self.on_selection_change = on_selection_change
        self.on_file_double_click_callback = on_file_double_click
        self.selected_paths = []
        self.selection_type = "none"  # "none", "single_file", "multiple_files", "folder", "dual_images"

        self.setup_ui()
    
    def setup_ui(self):
        """Configura l'interfaccia utente"""
        # Frame principale
        self.main_frame = ttk.LabelFrame(self.parent, text="Selezione File/Cartelle", padding=10)
        self.main_frame.pack(fill="x", padx=10, pady=5)
        
        # Frame bottoni
        buttons_frame = ttk.Frame(self.main_frame)
        buttons_frame.pack(fill="x", pady=(0, 10))
        
        # Bottoni selezione
        ttk.Button(
            buttons_frame, 
            text="📄 Seleziona File Singolo",
            command=self.select_single_file
        ).pack(side="left", padx=(0, 5))
        
        ttk.Button(
            buttons_frame, 
            text="📄📄 Seleziona File Multipli",
            command=self.select_multiple_files
        ).pack(side="left", padx=5)
        
        ttk.Button(
            buttons_frame, 
            text="📁 Seleziona Cartella",
            command=self.select_folder
        ).pack(side="left", padx=5)
        
        ttk.Button(
            buttons_frame, 
            text="🔄 Due Immagini",
            command=self.select_dual_images
        ).pack(side="left", padx=5)
        
        ttk.Button(
            buttons_frame, 
            text="🗑️ Pulisci",
            command=self.clear_selection
        ).pack(side="right")
        
        # Area preview selezione
        self.preview_frame = ttk.LabelFrame(self.main_frame, text="Selezione Corrente", padding=5)
        self.preview_frame.pack(fill="both", expand=True)
        
        # Testo info selezione
        self.info_label = ttk.Label(self.preview_frame, text="Nessuna selezione", foreground="gray")
        self.info_label.pack(anchor="w")
        
        # Lista file (scrollable)
        list_frame = ttk.Frame(self.preview_frame)
        list_frame.pack(fill="both", expand=True, pady=(5, 0))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Listbox
        self.files_listbox = tk.Listbox(
            list_frame, 
            yscrollcommand=scrollbar.set,
            height=6,
            selectmode="single"
        )
        self.files_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.files_listbox.yview)
        
        # Bind doppio click per aprire file
        self.files_listbox.bind("<Double-Button-1>", self.on_file_double_click)
    
    def select_single_file(self):
        """Seleziona un singolo file TIFF"""
        file_path = filedialog.askopenfilename(
            title="Seleziona Immagine TIFF",
            filetypes=[
                ("File TIFF", "*.tif *.tiff"),
                ("Tutti i file", "*.*")
            ]
        )
        
        if file_path:
            self.selected_paths = [file_path]
            self.selection_type = "single_file"
            self.update_preview()
            self._notify_change()
    
    def select_multiple_files(self):
        """Seleziona file multipli TIFF"""
        file_paths = filedialog.askopenfilenames(
            title="Seleziona Immagini TIFF",
            filetypes=[
                ("File TIFF", "*.tif *.tiff"),
                ("Tutti i file", "*.*")
            ]
        )
        
        if file_paths:
            self.selected_paths = list(file_paths)
            self.selection_type = "multiple_files"
            self.update_preview()
            self._notify_change()
    
    def select_dual_images(self):
        """Seleziona esattamente 2 immagini per registrazione"""
        file_paths = filedialog.askopenfilenames(
            title="Seleziona 2 Immagini per Registrazione",
            filetypes=[
                ("File immagine", "*.jpg *.jpeg *.png *.tif *.tiff"),
                ("JPEG", "*.jpg *.jpeg"),
                ("TIFF", "*.tif *.tiff"),
                ("PNG", "*.png"),
                ("Tutti i file", "*.*")
            ]
        )
        
        if file_paths:
            if len(file_paths) != 2:
                messagebox.showwarning(
                    "Selezione Errata",
                    f"Seleziona esattamente 2 immagini.\nHai selezionato {len(file_paths)} file."
                )
                return
            
            self.selected_paths = list(file_paths)
            self.selection_type = "dual_images"
            self.update_preview()
            self._notify_change()
    
    def select_folder(self):
        """Seleziona una cartella"""
        folder_path = filedialog.askdirectory(
            title="Seleziona Cartella con Immagini"
        )
        
        if folder_path:
            # Verifica che la cartella contenga file TIFF
            tiff_files = self._find_tiff_files(folder_path)
            if not tiff_files:
                messagebox.showwarning(
                    "Cartella Vuota",
                    "La cartella selezionata non contiene file TIFF."
                )
                return
            
            self.selected_paths = [folder_path]
            self.selection_type = "folder"
            self.update_preview()
            self._notify_change()
    
    def clear_selection(self):
        """Pulisce la selezione corrente"""
        self.selected_paths = []
        self.selection_type = "none"
        self.update_preview()
        self._notify_change()
    
    def _find_tiff_files(self, folder_path: str) -> List[str]:
        """Trova file TIFF in una cartella"""
        tiff_files = []
        folder = Path(folder_path)
        
        for pattern in ["*.tif", "*.tiff", "*.TIF", "*.TIFF"]:
            tiff_files.extend(folder.glob(pattern))
        
        return [str(f) for f in sorted(tiff_files)]
    
    def update_preview(self):
        """Aggiorna la preview della selezione"""
        # Pulisci listbox
        self.files_listbox.delete(0, tk.END)
        
        if not self.selected_paths:
            self.info_label.config(text="Nessuna selezione", foreground="gray")
            return
        
        if self.selection_type == "single_file":
            file_path = self.selected_paths[0]
            self.info_label.config(
                text=f"File singolo: {os.path.basename(file_path)}", 
                foreground="blue"
            )
            self.files_listbox.insert(0, os.path.basename(file_path))
            
        elif self.selection_type == "multiple_files":
            count = len(self.selected_paths)
            self.info_label.config(
                text=f"File multipli: {count} file selezionati", 
                foreground="green"
            )
            for path in self.selected_paths:
                self.files_listbox.insert(tk.END, os.path.basename(path))
        
        elif self.selection_type == "dual_images":
            self.info_label.config(
                text="Registrazione: 2 immagini selezionate", 
                foreground="orange"
            )
            for i, path in enumerate(self.selected_paths):
                label = "Riferimento" if i == 0 else "Target"
                self.files_listbox.insert(tk.END, f"{label}: {os.path.basename(path)}")
                
        elif self.selection_type == "folder":
            folder_path = self.selected_paths[0]
            tiff_files = self._find_tiff_files(folder_path)
            self.info_label.config(
                text=f"Cartella: {os.path.basename(folder_path)} ({len(tiff_files)} file TIFF)", 
                foreground="purple"
            )
            for file_path in tiff_files[:20]:  # Mostra max 20 file
                self.files_listbox.insert(tk.END, os.path.basename(file_path))
            
            if len(tiff_files) > 20:
                self.files_listbox.insert(tk.END, f"... e altri {len(tiff_files) - 20} file")
    
    def on_file_double_click(self, event):
        """Gestisce doppio click su file nella lista"""
        selection = self.files_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        
        if self.selection_type == "single_file":
            file_path = self.selected_paths[0]
        elif self.selection_type == "multiple_files":
            if index < len(self.selected_paths):
                file_path = self.selected_paths[index]
            else:
                return
        elif self.selection_type == "dual_images":
            if index < len(self.selected_paths):
                file_path = self.selected_paths[index]
            else:
                return
        elif self.selection_type == "folder":
            folder_path = self.selected_paths[0]
            tiff_files = self._find_tiff_files(folder_path)
            if index < len(tiff_files):
                file_path = tiff_files[index]
            else:
                return
        else:
            return
        
        # Chiama callback per caricare nel visualizzatore
        if self.on_file_double_click_callback:
            self.on_file_double_click_callback(file_path)
        else:
            # Fallback: mostra info file
            self._show_file_info(file_path)
    
    def _show_file_info(self, file_path: str):
        """Mostra informazioni su un file"""
        try:
            stat = os.stat(file_path)
            size_mb = stat.st_size / (1024 * 1024)
            
            info = f"File: {os.path.basename(file_path)}\n"
            info += f"Percorso: {file_path}\n"
            info += f"Dimensione: {size_mb:.1f} MB"
            
            messagebox.showinfo("Informazioni File", info)
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile leggere il file:\n{e}")
    
    def _notify_change(self):
        """Notifica il cambio di selezione"""
        if self.on_selection_change:
            self.on_selection_change(self.selected_paths, self.selection_type)
    
    def get_selection(self) -> tuple:
        """Restituisce la selezione corrente"""
        return self.selected_paths, self.selection_type
    
    def has_selection(self) -> bool:
        """Verifica se c'è una selezione"""
        return len(self.selected_paths) > 0
