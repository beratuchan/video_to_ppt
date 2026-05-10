import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import threading
from PIL import ImageTk
from infrastructure.python_pptx_reader import PythonPPTXReader
from infrastructure.python_pptx_writer import PythonPPTXWriter
from infrastructure.grid_composer import PillowGridComposer
from gui.ppt_grid_controller import PPTGridController

class PPTGridToolWindow(tk.Toplevel):
    def __init__(self, parent, default_pptx_path=None, temp_video_path=None):
        super().__init__(parent)
        self.title("PowerPoint Düzenleme Aracı")
        self.geometry("1100x800")
        self.controller = None
        self.thumbnails = []
        self.selected_indices = []
        self.settings_file = os.path.join(os.path.dirname(__file__), "..", "config", "ppt_grid_settings.json")
        self.current_pptx_path = None
        self.pptx_files = []
        self.temp_video_path = temp_video_path

        self._create_widgets()
        self.load_last_working_directory()
        self._bind_mousewheel()

        if default_pptx_path and os.path.exists(default_pptx_path):
            self.current_pptx_path = default_pptx_path
            self.load_pptx(default_pptx_path)

        self.protocol("WM_DELETE_WINDOW", self._on_close_cleanup)

    def _on_close_cleanup(self):
        if self.temp_video_path and os.path.exists(self.temp_video_path):
            try:
                os.unlink(self.temp_video_path)
                print(f"[Cleanup] Geçici video silindi: {self.temp_video_path}")
            except Exception as e:
                print(f"[Cleanup] Video silinemedi: {e}")
        self.destroy()

    def _bind_mousewheel(self):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _create_widgets(self):
        top_frame = tk.Frame(self)
        top_frame.pack(pady=5, fill=tk.X, padx=10)

        tk.Label(top_frame, text="Çalışma Klasörü:").pack(side=tk.LEFT, padx=5)
        self.folder_path_var = tk.StringVar()
        self.folder_entry = tk.Entry(top_frame, textvariable=self.folder_path_var, width=40)
        self.folder_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Klasör Seç", command=self.browse_folder).pack(side=tk.LEFT)
        tk.Button(top_frame, text="Varsayılan Yap", command=self.set_as_default).pack(side=tk.LEFT, padx=5)

        tk.Label(top_frame, text="Dosya Seç:").pack(side=tk.LEFT, padx=5)
        self.file_combo = ttk.Combobox(top_frame, width=30, state="readonly")
        self.file_combo.pack(side=tk.LEFT, padx=5)
        self.file_combo.bind("<<ComboboxSelected>>", self.on_file_selected)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        self.btn_delete = tk.Button(btn_frame, text="Seçili Slaytları Sil", command=self.delete_selected, bg="#ff9999")
        self.btn_delete.pack(side=tk.LEFT, padx=10)
        self.btn_grid = tk.Button(btn_frame, text="Seçili Slaytları Grid Slaytta Birleştir", command=self.grid_selected, bg="#99ccff")
        self.btn_grid.pack(side=tk.LEFT, padx=10)
        self.btn_upgrade = tk.Button(btn_frame, text="Seçili Slaytları Yüksek Kaliteye Yükselt", command=self.upgrade_selected, bg="#aaffaa")
        self.btn_upgrade.pack(side=tk.LEFT, padx=10)
        self.btn_grid.config(state=tk.DISABLED)
        self.btn_delete.config(state=tk.DISABLED)
        self.btn_upgrade.config(state=tk.DISABLED)

        frame_canvas = tk.Frame(self)
        frame_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(frame_canvas)
        scrollbar_y = tk.Scrollbar(frame_canvas, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar_x = tk.Scrollbar(frame_canvas, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.inner = tk.Frame(self.canvas)
        self.canvas.create_window((0,0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.status_label = tk.Label(self, text="", anchor="w")
        self.status_label.pack(fill=tk.X, padx=10, pady=5)

    def load_last_working_directory(self):
        try:
            with open(self.settings_file, "r") as f:
                data = json.load(f)
                folder = data.get("working_directory")
                if folder and os.path.isdir(folder):
                    self.folder_path_var.set(folder)
                    self.refresh_pptx_list()
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def set_as_default(self):
        folder = self.folder_path_var.get().strip()
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
            self.folder_path_var.set(folder)
            self.refresh_pptx_list()

    def refresh_pptx_list(self):
        folder = self.folder_path_var.get().strip()
        if not folder or not os.path.isdir(folder):
            self.file_combo['values'] = []
            self.status_label.config(text="Klasör geçerli değil")
            return
        files = [f for f in os.listdir(folder) if f.lower().endswith(".pptx")]
        self.pptx_files = [(os.path.join(folder, f), f) for f in files]
        self.file_combo['values'] = [f for _, f in self.pptx_files]
        if self.pptx_files:
            self.file_combo.current(0)
            self.on_file_selected()
        else:
            self.file_combo.set("")
            self.status_label.config(text="Klasörde PowerPoint dosyası bulunamadı")
            self.btn_grid.config(state=tk.DISABLED)
            self.btn_delete.config(state=tk.DISABLED)
            self.btn_upgrade.config(state=tk.DISABLED)

    def on_file_selected(self, event=None):
        selection = self.file_combo.current()
        if selection < 0 or selection >= len(self.pptx_files):
            return
        full_path = self.pptx_files[selection][0]
        self.current_pptx_path = full_path
        self.load_pptx(full_path)

    def load_pptx(self, path):
        try:
            reader = PythonPPTXReader(path)
            writer = PythonPPTXWriter(path)
            composer = PillowGridComposer()
            self.controller = PPTGridController(reader, writer, composer)
            self.refresh_slides()
            self.btn_grid.config(state=tk.NORMAL)
            self.btn_delete.config(state=tk.NORMAL)
            self.btn_upgrade.config(state=tk.NORMAL)
            self.status_label.config(text=f"Yüklendi: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya açılamadı: {e}")
            self.btn_grid.config(state=tk.DISABLED)
            self.btn_delete.config(state=tk.DISABLED)
            self.btn_upgrade.config(state=tk.DISABLED)

    def refresh_slides(self):
        for widget in self.inner.winfo_children():
            widget.destroy()
        self.thumbnails.clear()
        self.selected_indices.clear()
        count = self.controller.get_slide_count()
        if count == 0:
            tk.Label(self.inner, text="Slayt yok").pack()
            return
        cols = 3
        thumb_size = 250
        for idx in range(count):
            if idx % cols == 0:
                row_frame = tk.Frame(self.inner)
                row_frame.pack(anchor="w", pady=10)
            slide_frame = tk.Frame(row_frame, relief=tk.RIDGE, borderwidth=2, padx=5, pady=5)
            slide_frame.pack(side=tk.LEFT, padx=10, pady=5)

            img = self.controller.get_slide_preview(idx, max_size=thumb_size)
            photo = None
            if img:
                photo = ImageTk.PhotoImage(img)
                label_img = tk.Label(slide_frame, image=photo)
                label_img.image = photo
                label_img.pack()
            else:
                placeholder = tk.Label(slide_frame, text="[Resim yok]", width=30, height=20, bg='lightgray')
                placeholder.pack()

            lbl_num = tk.Label(slide_frame, text=f"Slayt {idx+1}", font=("Arial", 12, "bold"))
            lbl_num.pack()
            var = tk.BooleanVar()
            cb = tk.Checkbutton(slide_frame, variable=var, text="Seç", font=("Arial", 10),
                                command=lambda i=idx, v=var: self._toggle(i, v))
            cb.pack()
            self.thumbnails.append((photo, var, idx))

        self.inner.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _toggle(self, idx, var):
        if var.get():
            if idx not in self.selected_indices:
                self.selected_indices.append(idx)
        else:
            if idx in self.selected_indices:
                self.selected_indices.remove(idx)

    def delete_selected(self):
        if not self.selected_indices:
            messagebox.showerror("Hata", "Silinecek slayt seçin")
            return
        try:
            self.status_label.config(text="Slaytlar siliniyor...")
            self.update_idletasks()
            self.controller.delete_slides(self.selected_indices)
            self.controller.save(self.current_pptx_path)
            self.status_label.config(text="Silme tamamlandı, slaytlar güncellendi.")
            self.refresh_slides()
        except Exception as e:
            messagebox.showerror("Hata", str(e))
            self.status_label.config(text="Hata oluştu")

    def grid_selected(self):
        if len(self.selected_indices) < 2:
            messagebox.showerror("Hata", "En az iki slayt seçmelisiniz")
            return
        try:
            self.status_label.config(text="Birleştiriliyor...")
            self.update_idletasks()
            self.controller.apply_grid(self.selected_indices, margin=10)
            self.controller.save(self.current_pptx_path)
            self.status_label.config(text="Birleştirme tamamlandı, slaytlar güncellendi.")
            self.refresh_slides()
        except Exception as e:
            messagebox.showerror("Hata", str(e))
            self.status_label.config(text="Hata oluştu")

    def upgrade_selected(self):
        if not self.selected_indices:
            messagebox.showerror("Hata", "Yükseltilecek slayt seçin")
            return

        self.btn_upgrade.config(state=tk.DISABLED)
        self.btn_grid.config(state=tk.DISABLED)
        self.btn_delete.config(state=tk.DISABLED)

        total = len(self.selected_indices)
        self.status_label.config(text=f"Yüksek kaliteli kareler alınıyor (0/{total})...")
        self.update_idletasks()

        def task():
            try:
                def progress_callback(current, total, slide_idx):
                    self.after(0, lambda: self.status_label.config(
                        text=f"Yüksek kaliteli kareler alınıyor ({current+1}/{total}) - Slayt {slide_idx+1}..."
                    ))
                self.controller.upgrade_slides(self.selected_indices, target_width=1280, progress_callback=progress_callback)
                self.controller.save(self.current_pptx_path)
                self.after(0, self._upgrade_finished_success)
            except Exception as e:
                error_msg = str(e)
                self.after(0, lambda: self._upgrade_finished_error(error_msg))

        threading.Thread(target=task, daemon=True).start()

    def _upgrade_finished_success(self):
        self.status_label.config(text="Yükseltme tamamlandı, slaytlar güncellendi.")
        self.refresh_slides()
        self.btn_upgrade.config(state=tk.NORMAL)
        self.btn_grid.config(state=tk.NORMAL)
        self.btn_delete.config(state=tk.NORMAL)
        for _, var, _ in self.thumbnails:
            var.set(False)
        self.selected_indices.clear()
        messagebox.showinfo("Tamamlandı", "Seçili slaytlar yüksek kaliteye yükseltildi.")

    def _upgrade_finished_error(self, error_msg):
        messagebox.showerror("Hata", f"Yükseltme sırasında hata:\n{error_msg}")
        self.status_label.config(text="Hata oluştu")
        self.btn_upgrade.config(state=tk.NORMAL)
        self.btn_grid.config(state=tk.NORMAL)
        self.btn_delete.config(state=tk.NORMAL)