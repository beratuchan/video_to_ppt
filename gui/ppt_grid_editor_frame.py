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
from utils.url_resolver import resolve_video_url
from infrastructure.high_res_frame_extractor import HighResFrameExtractor
import threading

class PPTGridEditorFrame(ttk.Frame):
    def __init__(self, parent, temp_video_path=None):
        super().__init__(parent)
        self.controller = None
        self.thumbnails = []
        self.selected_indices = []
        self.settings_file = os.path.join(os.path.dirname(__file__), "..", "config", "ppt_grid_settings.json")
        self.current_pptx_path = None
        self.pptx_files = []
        self.temp_video_path = temp_video_path
        self.last_clicked_index = None
        self._create_widgets()
        self.load_last_working_directory()
        self._bind_mousewheel()

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
        top_frame = ttk.Frame(self)
        top_frame.pack(pady=5, fill=tk.X, padx=10)

        ttk.Label(top_frame, text="Çalışma Klasörü:").pack(side=tk.LEFT, padx=5)
        self.folder_path_var = tk.StringVar()
        self.folder_entry = ttk.Entry(top_frame, textvariable=self.folder_path_var, width=40)
        self.folder_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Klasör Seç", command=self.browse_folder).pack(side=tk.LEFT)
        ttk.Button(top_frame, text="Varsayılan Yap", command=self.set_as_default).pack(side=tk.LEFT, padx=5)

        ttk.Label(top_frame, text="Dosya Seç:").pack(side=tk.LEFT, padx=5)
        self.file_combo = ttk.Combobox(top_frame, width=30, state="readonly")
        self.file_combo.pack(side=tk.LEFT, padx=5)
        self.file_combo.bind("<<ComboboxSelected>>", self.on_file_selected)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        self.btn_delete = ttk.Button(btn_frame, text="Seçili Slaytları Sil", command=self.delete_selected)
        self.btn_delete.pack(side=tk.LEFT, padx=10)
        self.btn_grid = ttk.Button(btn_frame, text="Seçili Slaytları Grid Slaytta Birleştir", command=self.grid_selected)
        self.btn_grid.pack(side=tk.LEFT, padx=10)
        self.btn_upgrade = ttk.Button(btn_frame, text="Seçili Slaytları Yüksek Kaliteye Yükselt", command=self.upgrade_selected)
        self.btn_upgrade.pack(side=tk.LEFT, padx=10)
        self.btn_gif = ttk.Button(btn_frame, text="Seçili Slaytları GIF Animasyonu Yap", command=self.gif_selected)
        self.btn_gif.pack(side=tk.LEFT, padx=10)
        self._disable_buttons()

        frame_canvas = ttk.Frame(self)
        frame_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(frame_canvas, bg='#f0f0f0')
        scrollbar_y = ttk.Scrollbar(frame_canvas, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar_x = ttk.Scrollbar(frame_canvas, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.inner = ttk.Frame(self.canvas)
        self.canvas.create_window((0,0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.status_label = ttk.Label(self, text="", anchor="w")
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
            self._disable_buttons()

    def _disable_buttons(self):
        self.btn_delete.config(state=tk.DISABLED)
        self.btn_grid.config(state=tk.DISABLED)
        self.btn_upgrade.config(state=tk.DISABLED)
        self.btn_gif.config(state=tk.DISABLED)

    def _enable_buttons(self):
        self.btn_delete.config(state=tk.NORMAL)
        self.btn_grid.config(state=tk.NORMAL)
        self.btn_upgrade.config(state=tk.NORMAL)
        self.btn_gif.config(state=tk.NORMAL)

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
            self._enable_buttons()
            self.status_label.config(text=f"Yüklendi: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya açılamadı: {e}")
            self._disable_buttons()

    def refresh_slides(self):
        for widget in self.inner.winfo_children():
            widget.destroy()
        self.thumbnails.clear()
        self.selected_indices.clear()
        self.last_clicked_index = None
        count = self.controller.get_slide_count()
        if count == 0:
            ttk.Label(self.inner, text="Slayt yok").pack()
            return
        cols = 3
        thumb_size = 220
        for idx in range(count):
            if idx % cols == 0:
                row_frame = ttk.Frame(self.inner)
                row_frame.pack(anchor="w", pady=10)

            slide_frame = tk.Frame(row_frame, relief=tk.RIDGE, borderwidth=1, bg='white', cursor="hand2")
            slide_frame.pack(side=tk.LEFT, padx=10, pady=5)
            slide_frame.bind("<Button-1>", lambda e, i=idx: self._on_slide_click(e, i))

            img = self.controller.get_slide_preview(idx, max_size=thumb_size)
            photo = None
            if img:
                photo = ImageTk.PhotoImage(img)
                label_img = tk.Label(slide_frame, image=photo, bg='white')
                label_img.image = photo
                label_img.pack(padx=2, pady=2)
                label_img.bind("<Button-1>", lambda e, i=idx: self._on_slide_click(e, i))
            else:
                placeholder = tk.Label(slide_frame, text="[Resim yok]", width=25, height=15, bg='lightgray')
                placeholder.pack()
                placeholder.bind("<Button-1>", lambda e, i=idx: self._on_slide_click(e, i))

            lbl_num = tk.Label(slide_frame, text=f"Slayt {idx+1}", font=("Arial", 10, "bold"), bg='white')
            lbl_num.pack()
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(slide_frame, variable=var, text="Seç", command=lambda i=idx: self._on_checkbutton_click(i))
            cb.pack()
            self.thumbnails.append((photo, var, idx))

        self.inner.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_checkbutton_click(self, idx):
        if idx in self.selected_indices:
            self._select_single(idx, False)
        else:
            self._select_single(idx, True)
        self.last_clicked_index = idx

    def _on_slide_click(self, event, idx):
        shift_pressed = (event.state & 0x0001) != 0
        if shift_pressed and self.last_clicked_index is not None:
            start = min(self.last_clicked_index, idx)
            end = max(self.last_clicked_index, idx)
            for i in range(start, end+1):
                if i not in self.selected_indices:
                    self._select_single(i, True)
            self.last_clicked_index = idx
        else:
            if idx in self.selected_indices:
                self._select_single(idx, False)
            else:
                self._select_single(idx, True)
            self.last_clicked_index = idx

    def _select_single(self, idx, select):
        if select:
            if idx not in self.selected_indices:
                self.selected_indices.append(idx)
        else:
            if idx in self.selected_indices:
                self.selected_indices.remove(idx)
        if idx < len(self.thumbnails):
            var = self.thumbnails[idx][1]
            var.set(select)

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
        self.btn_gif.config(state=tk.DISABLED)

        total = len(self.selected_indices)
        self.status_label.config(text=f"Yüksek kaliteli kareler alınıyor (0/{total})...")
        self.update_idletasks()

        # İlk slayttan video URL'sini al
        youtube_url = self.controller.get_video_url_from_first_slide()
        if not youtube_url:
            messagebox.showerror("Hata", "İlk slaytta video URL'si bulunamadı")
            self._enable_buttons()
            return
        video_stream_url = resolve_video_url(youtube_url)
        if not video_stream_url:
            messagebox.showerror("Hata", "Video akış URL'si alınamadı")
            self._enable_buttons()
            return
        extractor = HighResFrameExtractor(video_stream_url)

        def task():
            try:
                def progress_callback(current, total, slide_idx):
                    self.after(0, lambda: self.status_label.config(
                        text=f"Yüksek kaliteli kareler alınıyor ({current+1}/{total}) - Slayt {slide_idx+1}..."
                    ))
                self.controller.upgrade_slides(self.selected_indices, extractor, target_width=1280, progress_callback=progress_callback)
                self.controller.save(self.current_pptx_path)
                self.after(0, self._upgrade_finished_success)
            except Exception as e:
                error_msg = str(e)
                self.after(0, lambda: self._upgrade_finished_error(error_msg))

        threading.Thread(target=task, daemon=True).start()

    def _upgrade_finished_success(self):
        self.status_label.config(text="Yükseltme tamamlandı, slaytlar güncellendi.")
        self.refresh_slides()
        self._enable_buttons()
        for _, var, _ in self.thumbnails:
            var.set(False)
        self.selected_indices.clear()
        messagebox.showinfo("Tamamlandı", "Seçili slaytlar yüksek kaliteye yükseltildi.")

    def _upgrade_finished_error(self, error_msg):
        messagebox.showerror("Hata", f"Yükseltme sırasında hata:\n{error_msg}")
        self.status_label.config(text="Hata oluştu")
        self._enable_buttons()

    def gif_selected(self):
        if len(self.selected_indices) < 2:
            messagebox.showerror("Hata", "En az iki slayt seçmelisiniz")
            return
        try:
            self.status_label.config(text="GIF animasyonu oluşturuluyor...")
            self.update_idletasks()
            self._disable_buttons()
            self.controller.replace_slides_with_gif(self.selected_indices, duration_per_frame=0.5)
            self.controller.save(self.current_pptx_path)
            self.status_label.config(text="GIF slayt oluşturuldu.")
            self.refresh_slides()
            self._enable_buttons()
            messagebox.showinfo("Tamamlandı", 
                "GIF animasyonu başarıyla slayta eklendi.\n\n"
                "Slayt gösterisi başladığında GIF otomatik olarak dönecektir.\n"
                "Not: PowerPoint'te GIF'in döngüye girmesi için herhangi bir ek ayar gerekmez.")
        except Exception as e:
            messagebox.showerror("Hata", str(e))
            self._enable_buttons()

    def set_pptx_and_video(self, pptx_path, video_path):
        self.temp_video_path = video_path
        if pptx_path and os.path.exists(pptx_path):
            self.current_pptx_path = pptx_path
            folder = os.path.dirname(pptx_path)
            self.folder_path_var.set(folder)
            self.refresh_pptx_list()
            for i, (fp, fn) in enumerate(self.pptx_files):
                if fp == pptx_path:
                    self.file_combo.current(i)
                    self.on_file_selected()
                    break