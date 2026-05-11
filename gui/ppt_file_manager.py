# gui/ppt_file_manager.py
import json
import os
from tkinter import filedialog, messagebox

class PPTXFileManager:
    def __init__(self, settings_file, folder_var, refresh_callback):
        self.settings_file = settings_file
        self.folder_var = folder_var
        self.refresh_callback = refresh_callback

    def load_last_working_directory(self):
        try:
            with open(self.settings_file, "r") as f:
                data = json.load(f)
                folder = data.get("working_directory")
                if folder and os.path.isdir(folder):
                    self.folder_var.set(folder)
                    self.refresh_callback()
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def set_as_default(self):
        folder = self.folder_var.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Hata", "Geçerli bir klasör seçin")
            return
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        with open(self.settings_file, "w") as f:
            json.dump({"working_directory": folder}, f)
        messagebox.showinfo("Başarılı", "Bu klasör varsayılan çalışma klasörü olarak kaydedildi.")

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Çalışma Klasörünü Seçin")
        if folder:
            self.folder_var.set(folder)
            self.refresh_callback()

    def get_pptx_files(self):
        folder = self.folder_var.get().strip()
        if not folder or not os.path.isdir(folder):
            return []
        files = [f for f in os.listdir(folder) if f.lower().endswith(".pptx")]
        return [(os.path.join(folder, f), f) for f in files]

    def load_pptx(self, path, status_callback, enable_buttons_callback, refresh_slides_callback):
        # Dairesel importu önlemek için fonksiyon içinde import
        from infrastructure.python_pptx_reader import PythonPPTXReader
        from infrastructure.python_pptx_writer import PythonPPTXWriter
        from infrastructure.grid_composer import PillowGridComposer
        from gui.ppt_grid_controller import PPTGridController

        try:
            reader = PythonPPTXReader(path)
            writer = PythonPPTXWriter(path)
            composer = PillowGridComposer()
            controller = PPTGridController(reader, writer, composer)
            status_callback(f"Yüklendi: {os.path.basename(path)}")
            enable_buttons_callback(True)
            refresh_slides_callback(controller)
            return controller
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya açılamadı: {e}")
            enable_buttons_callback(False)
            return None