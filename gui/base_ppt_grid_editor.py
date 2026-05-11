# gui/base_ppt_grid_editor.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import threading
from PIL import Image, ImageTk

from infrastructure.python_pptx_reader import PythonPPTXReader
from infrastructure.python_pptx_writer import PythonPPTXWriter
from infrastructure.grid_composer import PillowGridComposer
from gui.ppt_grid_controller import PPTGridController
from gui.preview_panel import PreviewPanel
from gui.frame_carousel_widget import FrameCarouselWidget
from utils.url_resolver import resolve_video_url
from infrastructure.high_res_frame_extractor import HighResFrameExtractor
from config.settings import DEFAULT_GRID_MARGIN_PX, DEFAULT_UPGRADE_TARGET_WIDTH


class BasePPTGridEditor(tk.Frame):
    """
    Tüm PPT düzenleyici frame'ler için temel sınıf.
    Alt sınıflar stil ve cleanup gibi özelleştirmeleri sağlayabilir.
    """

    def __init__(self, parent, temp_video_path=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.controller = None
        self.thumbnails = []          # (photo, var, index)
        self.selected_indices = []    # sorted list
        self.carousel_index = 0       # selected slaytlar içinde gezinme
        self.settings_file = os.path.join(os.path.dirname(__file__), "..", "config", "ppt_grid_settings.json")
        self.current_pptx_path = None
        self.pptx_files = []
        self.temp_video_path = temp_video_path
        self.last_clicked_index = None

        # Carousel modu yönetimi
        self.carousel_mode_active = False
        self.frame_carousel_widget = None

        self._create_widgets()
        self.load_last_working_directory()
        self._bind_mousewheel()

    # ---- Stil özelleştirmeleri (alt sınıflar override edebilir) ----
    def get_button_bg_color(self, button_name: str) -> str:
        return ""

    def get_button_fg_color(self, button_name: str) -> str:
        return ""

    def get_canvas_bg_color(self) -> str:
        return "#f0f0f0"

    def get_slide_frame_bg(self) -> str:
        return "white"

    def on_close_cleanup(self):
        pass

    # ---- GUI Oluşturma ----
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
        # Üst kısım: klasör seçimi ve dosya listesi
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

        # Butonlar (sil, grid, yükselt, gif)
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        btn_kwargs = {}
        bg = self.get_button_bg_color("delete")
        if bg:
            btn_kwargs["bg"] = bg
        fg = self.get_button_fg_color("delete")
        if fg:
            btn_kwargs["fg"] = fg
        self.btn_delete = tk.Button(btn_frame, text="Seçili Slaytları Sil", command=self.delete_selected, **btn_kwargs)
        self.btn_delete.pack(side=tk.LEFT, padx=10)

        btn_kwargs = {}
        bg = self.get_button_bg_color("grid")
        if bg:
            btn_kwargs["bg"] = bg
        fg = self.get_button_fg_color("grid")
        if fg:
            btn_kwargs["fg"] = fg
        self.btn_grid = tk.Button(btn_frame, text="Seçili Slaytları Grid Slaytta Birleştir", command=self.grid_selected, **btn_kwargs)
        self.btn_grid.pack(side=tk.LEFT, padx=10)

        btn_kwargs = {}
        bg = self.get_button_bg_color("upgrade")
        if bg:
            btn_kwargs["bg"] = bg
        fg = self.get_button_fg_color("upgrade")
        if fg:
            btn_kwargs["fg"] = fg
        self.btn_upgrade = tk.Button(btn_frame, text="Seçili Slaytları Yüksek Kaliteye Yükselt", command=self.upgrade_selected, **btn_kwargs)
        self.btn_upgrade.pack(side=tk.LEFT, padx=10)

        btn_kwargs = {}
        bg = self.get_button_bg_color("gif")
        if bg:
            btn_kwargs["bg"] = bg
        fg = self.get_button_fg_color("gif")
        if fg:
            btn_kwargs["fg"] = fg
        self.btn_gif = tk.Button(btn_frame, text="Seçili Slaytları GIF Animasyonu Yap", command=self.gif_selected, **btn_kwargs)
        self.btn_gif.pack(side=tk.LEFT, padx=10)

        self._disable_buttons()

        # Orta kısım: PanedWindow (sol: thumbnail grid, sağ: önizleme + carousel)
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Sol taraf: scrollable canvas + thumbnail grid
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        self.canvas = tk.Canvas(left_frame, bg=self.get_canvas_bg_color())
        scrollbar_y = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar_x = ttk.Scrollbar(left_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.inner = ttk.Frame(self.canvas)
        self.canvas.create_window((0,0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Sağ taraf: normal önizleme paneli ve carousel modu için frame
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        # Normal mod (slayt önizleme)
        self.normal_frame = ttk.Frame(right_frame)
        self.normal_frame.pack(fill=tk.BOTH, expand=True)

        self.preview_label = tk.Label(self.normal_frame, bg="#ffffff", relief=tk.SUNKEN, anchor="center")
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.preview_label.bind("<Configure>", self._on_preview_resize)

        self.preview_info_label = ttk.Label(self.normal_frame, text="Slayt seçilmedi", anchor="center")
        self.preview_info_label.pack(pady=5)

        # Slaytlar arası gezinme (normal mod)
        slide_carousel_frame = tk.Frame(self.normal_frame)
        slide_carousel_frame.pack(pady=10)
        self.btn_prev_slide = tk.Button(slide_carousel_frame, text="◄ Önceki", command=self._carousel_prev, state=tk.DISABLED)
        self.btn_prev_slide.pack(side=tk.LEFT, padx=5)
        self.btn_next_slide = tk.Button(slide_carousel_frame, text="Sonraki ►", command=self._carousel_next, state=tk.DISABLED)
        self.btn_next_slide.pack(side=tk.LEFT, padx=5)
        self.carousel_counter = ttk.Label(self.normal_frame, text="", anchor="center")
        self.carousel_counter.pack(pady=2)

        # Kareyi Değiştir butonu (normal modda)
        self.btn_change_frame = tk.Button(
            self.normal_frame,
            text="🖼️ Kareyi Değiştir",
            command=self._enter_frame_carousel_mode,
            state=tk.DISABLED
        )
        self.btn_change_frame.pack(pady=5)

        # Carousel modu için frame (başlangıçta gizli)
        self.carousel_frame = ttk.Frame(right_frame)

        # Alt durum çubuğu
        self.status_label = ttk.Label(self, text="", anchor="w")
        self.status_label.pack(fill=tk.X, padx=10, pady=5)

    def _on_preview_resize(self, event):
        self._update_current_preview()

    # ---- Dosya ve Klasör Yönetimi ----
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

    # ---- Slayt Listesi ve Önizleme ----
    def refresh_slides(self):
        # Temizlik
        for widget in self.inner.winfo_children():
            widget.destroy()
        self.thumbnails.clear()
        self.selected_indices.clear()
        self.carousel_index = 0
        self.last_clicked_index = None

        count = self.controller.get_slide_count()
        if count == 0:
            ttk.Label(self.inner, text="Slayt yok").pack()
            self.preview_label.config(image="", text="Slayt yok")
            self.preview_info_label.config(text="Slayt yok")
            self._update_carousel_buttons()
            self.btn_change_frame.config(state=tk.DISABLED)
            return

        cols = 3
        thumb_size = 220
        for idx in range(count):
            if idx % cols == 0:
                row_frame = ttk.Frame(self.inner)
                row_frame.pack(anchor="w", pady=10)

            slide_frame = tk.Frame(row_frame, relief=tk.RIDGE, borderwidth=1, bg=self.get_slide_frame_bg(), cursor="hand2")
            slide_frame.pack(side=tk.LEFT, padx=10, pady=5)
            slide_frame.bind("<Button-1>", lambda e, i=idx: self._on_slide_click(e, i))

            img = self.controller.get_slide_preview(idx, max_size=thumb_size)
            photo = None
            if img:
                photo = ImageTk.PhotoImage(img)
                label_img = tk.Label(slide_frame, image=photo, bg=self.get_slide_frame_bg())
                label_img.image = photo
                label_img.pack(padx=2, pady=2)
                label_img.bind("<Button-1>", lambda e, i=idx: self._on_slide_click(e, i))
            else:
                placeholder = tk.Label(slide_frame, text="[Resim yok]", width=25, height=15, bg='lightgray')
                placeholder.pack()
                placeholder.bind("<Button-1>", lambda e, i=idx: self._on_slide_click(e, i))

            lbl_num = tk.Label(slide_frame, text=f"Slayt {idx+1}", font=("Arial", 10, "bold"), bg=self.get_slide_frame_bg())
            lbl_num.pack()
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(slide_frame, variable=var, text="Seç", command=lambda i=idx: self._on_checkbutton_click(i))
            cb.pack()
            self.thumbnails.append((photo, var, idx))

        self.inner.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # İlk slaytı seç (eğer hiç seçili yoksa)
        if not self.selected_indices and count > 0:
            self.selected_indices = [0]
            self.carousel_index = 0
        self._update_current_preview()
        self._update_carousel_buttons()
        # Kareyi değiştir butonunu aktif et (eğer video URL'si varsa)
        self.btn_change_frame.config(state=tk.NORMAL if self.controller else tk.DISABLED)

    def _update_current_preview(self):
        if not self.controller or not self.selected_indices:
            self.preview_label.config(image="", text="Slayt seçilmedi")
            self.preview_info_label.config(text="Slayt seçilmedi")
            self.carousel_counter.config(text="")
            return
        slide_idx = self.selected_indices[self.carousel_index]
        img = self.controller.get_slide_preview(slide_idx, max_size=800)
        if img:
            try:
                w = self.preview_label.winfo_width()
                h = self.preview_label.winfo_height()
                if w > 1 and h > 1:
                    img.thumbnail((w, h), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.preview_label.config(image=photo)
                self.preview_label.image = photo
                self.preview_info_label.config(text=f"Slayt {slide_idx+1} - {img.width}x{img.height}")
            except Exception:
                self.preview_label.config(image="", text="Görsel yüklenemedi")
        else:
            self.preview_label.config(image="", text="Görsel yok")
            self.preview_info_label.config(text=f"Slayt {slide_idx+1} - Görsel yok")
        self.carousel_counter.config(text=f"{self.carousel_index+1} / {len(self.selected_indices)}")

    def _update_carousel_buttons(self):
        if len(self.selected_indices) > 1:
            self.btn_prev_slide.config(state=tk.NORMAL)
            self.btn_next_slide.config(state=tk.NORMAL)
        else:
            self.btn_prev_slide.config(state=tk.DISABLED)
            self.btn_next_slide.config(state=tk.DISABLED)

    def _carousel_prev(self):
        if len(self.selected_indices) > 1:
            self.carousel_index = (self.carousel_index - 1) % len(self.selected_indices)
            self._update_current_preview()

    def _carousel_next(self):
        if len(self.selected_indices) > 1:
            self.carousel_index = (self.carousel_index + 1) % len(self.selected_indices)
            self._update_current_preview()

    # ---- Seçim Yönetimi ----
    def _on_checkbutton_click(self, idx):
        if idx in self.selected_indices:
            self.selected_indices.remove(idx)
        else:
            self.selected_indices.append(idx)
            self.selected_indices.sort()
        # Checkbox'ları güncelle
        for photo, var, i in self.thumbnails:
            var.set(i in self.selected_indices)
        # Carousel indeksini ayarla
        if self.selected_indices:
            if idx in self.selected_indices:
                self.carousel_index = self.selected_indices.index(idx)
            else:
                if self.carousel_index >= len(self.selected_indices):
                    self.carousel_index = max(0, len(self.selected_indices)-1)
        else:
            self.carousel_index = 0
        self._update_current_preview()
        self._update_carousel_buttons()
        self.last_clicked_index = idx

    def _on_slide_click(self, event, idx):
        shift_pressed = (event.state & 0x0001) != 0
        if shift_pressed and self.last_clicked_index is not None:
            start = min(self.last_clicked_index, idx)
            end = max(self.last_clicked_index, idx)
            for i in range(start, end+1):
                if i not in self.selected_indices:
                    self.selected_indices.append(i)
            self.selected_indices.sort()
            for photo, var, i in self.thumbnails:
                var.set(i in self.selected_indices)
            self.carousel_index = 0
            self._update_current_preview()
            self._update_carousel_buttons()
        else:
            if idx in self.selected_indices:
                self.selected_indices.remove(idx)
            else:
                self.selected_indices.append(idx)
                self.selected_indices.sort()
            for photo, var, i in self.thumbnails:
                var.set(i in self.selected_indices)
            if self.selected_indices:
                if idx in self.selected_indices:
                    self.carousel_index = self.selected_indices.index(idx)
                else:
                    if self.carousel_index >= len(self.selected_indices):
                        self.carousel_index = max(0, len(self.selected_indices)-1)
            else:
                self.carousel_index = 0
            self._update_current_preview()
            self._update_carousel_buttons()
        self.last_clicked_index = idx

    # ---- Buton Durumları ----
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

    # ---- İşlemler (Sil, Grid, Yükselt, GIF) ----
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
            new_slide_index = min(self.selected_indices)
            self.controller.apply_grid(self.selected_indices, margin=DEFAULT_GRID_MARGIN_PX)
            self.controller.save(self.current_pptx_path)
            self.status_label.config(text="Birleştirme tamamlandı, slaytlar güncellendi.")
            self.refresh_slides()
            self.selected_indices = [new_slide_index]
            self.carousel_index = 0
            self._update_current_preview()
            self._update_carousel_buttons()
        except Exception as e:
            messagebox.showerror("Hata", str(e))
            self.status_label.config(text="Hata oluştu")

    def upgrade_selected(self):
        if not self.selected_indices:
            messagebox.showerror("Hata", "Yükseltilecek slayt seçin")
            return
        self._disable_buttons()

        total = len(self.selected_indices)
        self.status_label.config(text=f"Yüksek kaliteli kareler alınıyor (0/{total})...")
        self.update_idletasks()

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
                self.controller.upgrade_slides(self.selected_indices, extractor, target_width=DEFAULT_UPGRADE_TARGET_WIDTH, progress_callback=progress_callback)
                self.controller.save(self.current_pptx_path)
                self.after(0, self._upgrade_finished_success)
            except Exception as e:
                # DÜZELTME: doğrudan after ile argüman gönder
                self.after(0, self._upgrade_finished_error, str(e))

        threading.Thread(target=task, daemon=True).start()

    def _upgrade_finished_success(self):
        self.status_label.config(text="Yükseltme tamamlandı, slaytlar güncellendi.")
        self.refresh_slides()
        self._enable_buttons()
        self._update_current_preview()
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
            new_index = min(self.selected_indices)
            self.controller.replace_slides_with_gif(self.selected_indices, duration_per_frame=0.5)
            self.controller.save(self.current_pptx_path)
            self.status_label.config(text="GIF slayt oluşturuldu.")
            self.refresh_slides()
            self.selected_indices = [new_index]
            self.carousel_index = 0
            self._update_current_preview()
            self._update_carousel_buttons()
            self._enable_buttons()
            messagebox.showinfo("Tamamlandı", "GIF animasyonu başarıyla slayta eklendi.")
        except Exception as e:
            messagebox.showerror("Hata", str(e))
            self._enable_buttons()

    # ---- Yeni: Kare Değiştirme (Frame Carousel) Modu ----
    def _enter_frame_carousel_mode(self):
        if self.carousel_mode_active:
            return
        if not self.selected_indices:
            messagebox.showerror("Hata", "Lütfen bir slayt seçin.")
            return
        current_slide = self.selected_indices[self.carousel_index] if self.selected_indices else None
        if current_slide is None:
            messagebox.showerror("Hata", "Geçerli bir slayt seçin.")
            return

        self.status_label.config(text="Video segmenti hazırlanıyor...")
        self.update_idletasks()

        def task():
            try:
                def progress_cb(percent, msg):
                    self.after(0, lambda: self.status_label.config(text=msg))
                carousel = self.controller.get_frame_carousel(current_slide, progress_callback=progress_cb)
                self.after(0, lambda: self._show_frame_carousel(carousel, current_slide))
            except Exception as e:
                # DÜZELTME: doğrudan after ile argüman gönder
                self.after(0, self._carousel_error, str(e))

        threading.Thread(target=task, daemon=True).start()

    def _show_frame_carousel(self, carousel, slide_index):
        # Normal modu gizle, carousel frame'ini göster
        self.normal_frame.pack_forget()
        self.carousel_frame.pack(fill=tk.BOTH, expand=True)

        if self.frame_carousel_widget:
            self.frame_carousel_widget.destroy()

        self.frame_carousel_widget = FrameCarouselWidget(
            self.carousel_frame,
            carousel_service=carousel,
            on_select_callback=lambda frame: self._replace_slide_frame(slide_index, frame),
            on_cancel_callback=self._exit_frame_carousel_mode
        )
        self.frame_carousel_widget.pack(fill=tk.BOTH, expand=True)

        self.carousel_mode_active = True
        self.status_label.config(text="Kare seçici modu aktif. Gezinmek için okları kullanın, uzun basarak hızlı geçin. 'Yeni Kareyi Seç' ile değiştirin.")

    def _replace_slide_frame(self, slide_index, frame_bgr):
        try:
            self.controller.replace_slide_with_frame(slide_index, frame_bgr)
            self.controller.save(self.current_pptx_path)
            self.status_label.config(text="Slayt resmi güncellendi.")
            self._exit_frame_carousel_mode()
            self.refresh_slides()
        except Exception as e:
            messagebox.showerror("Hata", f"Resim değiştirilemedi: {e}")
            self._exit_frame_carousel_mode()

    def _carousel_error(self, err_msg):
        messagebox.showerror("Hata", f"Kare seçici başlatılamadı:\n{err_msg}")
        self.status_label.config(text="Hata oluştu")
        self._exit_frame_carousel_mode()

    def _exit_frame_carousel_mode(self):
        if not self.carousel_mode_active:
            return
        self.carousel_mode_active = False
        if self.frame_carousel_widget:
            self.frame_carousel_widget.destroy()
            self.frame_carousel_widget = None
        self.carousel_frame.pack_forget()
        self.normal_frame.pack(fill=tk.BOTH, expand=True)
        self.status_label.config(text="")
        self.refresh_slides()

    # ---- Dışarıdan PPTX ve Video yükleme (ConversionController tarafından kullanılır) ----
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