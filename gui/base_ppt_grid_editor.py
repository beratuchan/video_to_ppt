# gui/base_ppt_grid_editor.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
import threading
from .ppt_file_manager import PPTXFileManager
from .slide_selection_manager import SlideSelectionManager
from .thumbnail_grid_view import ThumbnailGridView
from .preview_panel import PreviewPanel
from config.settings import DEFAULT_GRID_MARGIN_PX, DEFAULT_UPGRADE_TARGET_WIDTH


class BasePPTGridEditor(tk.Frame):
    def __init__(self, parent, temp_video_path=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.temp_video_path = temp_video_path
        self.controller = None
        self.current_pptx_path = None

        self.settings_file = os.path.join(os.path.dirname(__file__), "..", "config", "ppt_grid_settings.json")
        self.folder_path_var = tk.StringVar()

        self._create_widgets()
        self._setup_components()
        self.file_manager.load_last_working_directory()

    def _create_widgets(self):
        # Üst kısım
        top_frame = ttk.Frame(self)
        top_frame.pack(pady=5, fill=tk.X, padx=10)

        ttk.Label(top_frame, text="Çalışma Klasörü:").pack(side=tk.LEFT, padx=5)
        self.folder_entry = ttk.Entry(top_frame, textvariable=self.folder_path_var, width=40)
        self.folder_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Klasör Seç", command=self._browse_folder).pack(side=tk.LEFT)
        ttk.Button(top_frame, text="Varsayılan Yap", command=self._set_as_default).pack(side=tk.LEFT, padx=5)

        ttk.Label(top_frame, text="Dosya Seç:").pack(side=tk.LEFT, padx=5)
        self.file_combo = ttk.Combobox(top_frame, width=30, state="readonly")
        self.file_combo.pack(side=tk.LEFT, padx=5)
        self.file_combo.bind("<<ComboboxSelected>>", self._on_file_selected)

        # Butonlar
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        self.btn_delete = tk.Button(btn_frame, text="Seçili Slaytları Sil", command=self._delete_selected)
        self.btn_delete.pack(side=tk.LEFT, padx=10)
        self.btn_grid = tk.Button(btn_frame, text="Seçili Slaytları Grid Slaytta Birleştir", command=self._grid_selected)
        self.btn_grid.pack(side=tk.LEFT, padx=10)
        self.btn_upgrade = tk.Button(btn_frame, text="Seçili Slaytları Yüksek Kaliteye Yükselt", command=self._upgrade_selected)
        self.btn_upgrade.pack(side=tk.LEFT, padx=10)
        self.btn_gif = tk.Button(btn_frame, text="Seçili Slaytları GIF Animasyonu Yap", command=self._gif_selected)
        self.btn_gif.pack(side=tk.LEFT, padx=10)

        self._set_buttons_state(tk.DISABLED)

        # Orta kısım: PanedWindow
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        # Sol taraf: scrollable canvas + thumbnail grid
        canvas = tk.Canvas(left_frame, bg="#f0f0f0")
        scroll_y = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=canvas.yview)
        scroll_x = ttk.Scrollbar(left_frame, orient=tk.HORIZONTAL, command=canvas.xview)
        canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.thumbnails_container = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=self.thumbnails_container, anchor="nw")
        self.thumbnails_container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Mousewheel
        def on_mousewheel(event):
            if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
                canvas.yview_scroll(-1, "units")
            elif event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
                canvas.yview_scroll(1, "units")
            else:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        canvas.bind_all("<Button-4>", on_mousewheel)
        canvas.bind_all("<Button-5>", on_mousewheel)

        # Sağ taraf: önizleme paneli
        self.preview_panel = PreviewPanel(right_frame, self._get_slide_preview)

        # Alt durum çubuğu
        self.status_label = ttk.Label(self, text="", anchor="w")
        self.status_label.pack(fill=tk.X, padx=10, pady=5)

    def _setup_components(self):
        self.file_manager = PPTXFileManager(
            settings_file=self.settings_file,
            folder_var=self.folder_path_var,
            refresh_callback=self._refresh_pptx_list
        )
        self.selection = SlideSelectionManager(total_slides=0, update_ui_callback=self._on_selection_changed)
        self.thumbnail_view = ThumbnailGridView(
            parent=self.thumbnails_container,
            on_slide_click=self._on_slide_click,
            get_preview_func=self._get_slide_preview
        )
        self.preview_panel.set_on_prev_next(self._carousel_move)

    def _get_slide_preview(self, slide_idx, max_size=100):
        if self.controller:
            return self.controller.get_slide_preview(slide_idx, max_size)
        return None

    def _refresh_pptx_list(self):
        files = self.file_manager.get_pptx_files()
        self.pptx_files = files
        self.file_combo['values'] = [f for _, f in files]
        if files:
            self.file_combo.current(0)
            self._on_file_selected()
        else:
            self.file_combo.set("")
            self.status_label.config(text="Klasörde PowerPoint dosyası bulunamadı")
            self._set_buttons_state(tk.DISABLED)

    def _on_file_selected(self, event=None):
        selection = self.file_combo.current()
        if selection < 0 or selection >= len(self.pptx_files):
            return
        full_path = self.pptx_files[selection][0]
        self.current_pptx_path = full_path
        self.file_manager.load_pptx(
            path=full_path,
            status_callback=self._set_status,
            enable_buttons_callback=self._set_buttons_enabled,
            refresh_slides_callback=self._set_controller_and_refresh
        )

    def _set_controller_and_refresh(self, controller):
        self.controller = controller
        self.selection.set_total_slides(controller.get_slide_count())
        self._refresh_slides()

    def _refresh_slides(self):
        if not self.controller:
            return
        count = self.controller.get_slide_count()
        self.selection.set_total_slides(count)
        self.thumbnail_view.rebuild(count, "white")
        self.thumbnail_view.update_checkboxes(self.selection.selected_indices)
        self._on_selection_changed(self.selection)

    def _on_selection_changed(self, selection):
        self.thumbnail_view.update_checkboxes(selection.selected_indices)
        current = selection.get_current_slide()
        if current is not None:
            self.preview_panel.update(
                slide_idx=current,
                total_selected=len(selection.selected_indices),
                current_pos=selection.carousel_index
            )
        else:
            self.preview_panel.update(None, 0, 0)

    def _carousel_move(self, delta):
        self.selection.move_carousel(delta)

    def _on_slide_click(self, event, idx):
        shift_pressed = (event.state & 0x0001) != 0
        if shift_pressed and self.selection.last_clicked_index is not None:
            self.selection.select_range(self.selection.last_clicked_index, idx)
        else:
            self.selection.toggle_single(idx)
        self.selection.last_clicked_index = idx

    def _set_buttons_state(self, state):
        for btn in (self.btn_delete, self.btn_grid, self.btn_upgrade, self.btn_gif):
            btn.config(state=state)

    def _set_buttons_enabled(self, enabled):
        self._set_buttons_state(tk.NORMAL if enabled else tk.DISABLED)

    def _set_status(self, text):
        self.status_label.config(text=text)

    def _browse_folder(self):
        self.file_manager.browse_folder()
        self._refresh_pptx_list()

    def _set_as_default(self):
        self.file_manager.set_as_default()

    def _delete_selected(self):
        if not self.selection.selected_indices:
            messagebox.showerror("Hata", "Silinecek slayt seçin")
            return
        self._run_async(lambda: self.controller.delete_slides(self.selection.selected_indices),
                        "Slaytlar siliniyor...", "Slaytlar silindi")

    def _grid_selected(self):
        if len(self.selection.selected_indices) < 2:
            messagebox.showerror("Hata", "En az iki slayt seçmelisiniz")
            return
        self._run_async(lambda: self.controller.apply_grid(self.selection.selected_indices, margin=DEFAULT_GRID_MARGIN_PX),
                        "Birleştiriliyor...", "Grid slayt oluşturuldu")

    def _upgrade_selected(self):
        if not self.selection.selected_indices:
            messagebox.showerror("Hata", "Yükseltilecek slayt seçin")
            return
        def action():
            def progress_cb(curr, total, slide_idx):
                self.after(0, lambda: self.status_label.config(
                    text=f"Yüksek kaliteli kareler alınıyor ({curr+1}/{total}) - Slayt {slide_idx+1}..."
                ))
            def status_cb(msg):
                self.after(0, lambda: self.status_label.config(text=msg))
            self.controller.upgrade_selected_slides(
                self.selection.selected_indices,
                target_width=DEFAULT_UPGRADE_TARGET_WIDTH,
                progress_callback=progress_cb,
                status_callback=status_cb
            )
        self._run_async(action, "Yükseltme başlatıldı...", "Yükseltme tamamlandı")

    def _gif_selected(self):
        if len(self.selection.selected_indices) < 2:
            messagebox.showerror("Hata", "En az iki slayt seçmelisiniz")
            return
        self._run_async(lambda: self.controller.replace_slides_with_gif(self.selection.selected_indices, duration_per_frame=0.5),
                        "GIF oluşturuluyor...", "GIF animasyonu eklendi")

    def _run_async(self, action, start_msg, success_msg):
        self._set_buttons_state(tk.DISABLED)
        self.status_label.config(text=start_msg)
        self.update_idletasks()
        def task():
            try:
                action()
                self.controller.save(self.current_pptx_path)
                self.after(0, lambda: self._async_success(success_msg))
            except Exception as e:
                self.after(0, lambda: self._async_error(str(e)))
        threading.Thread(target=task, daemon=True).start()

    def _async_success(self, msg):
        self.status_label.config(text=msg)
        self._refresh_slides()
        self._set_buttons_state(tk.NORMAL)
        messagebox.showinfo("Tamamlandı", msg)

    def _async_error(self, error_msg):
        messagebox.showerror("Hata", f"İşlem sırasında hata:\n{error_msg}")
        self.status_label.config(text="Hata oluştu")
        self._set_buttons_state(tk.NORMAL)

    def set_pptx_and_video(self, pptx_path, video_path):
        self.temp_video_path = video_path
        if pptx_path and os.path.exists(pptx_path):
            self.current_pptx_path = pptx_path
            folder = os.path.dirname(pptx_path)
            self.folder_path_var.set(folder)
            self._refresh_pptx_list()
            for i, (fp, fn) in enumerate(self.pptx_files):
                if fp == pptx_path:
                    self.file_combo.current(i)
                    self._on_file_selected()
                    break