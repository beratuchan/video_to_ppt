# gui/preview_panel.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class PreviewPanel:
    def __init__(self, parent, get_preview_func):
        self.get_preview_func = get_preview_func
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.label = tk.Label(self.frame, bg="#ffffff", relief=tk.SUNKEN, anchor="center")
        self.label.pack(fill=tk.BOTH, expand=True)
        self.label.bind("<Configure>", self._on_resize)

        self.info_label = ttk.Label(self.frame, text="Slayt seçilmedi", anchor="center")
        self.info_label.pack(pady=5)

        carousel_frame = tk.Frame(self.frame)
        carousel_frame.pack(pady=10)
        self.btn_prev = tk.Button(carousel_frame, text="◄ Önceki", command=self.prev, state=tk.DISABLED)
        self.btn_prev.pack(side=tk.LEFT, padx=5)
        self.btn_next = tk.Button(carousel_frame, text="Sonraki ►", command=self.next, state=tk.DISABLED)
        self.btn_next.pack(side=tk.LEFT, padx=5)
        self.counter_label = ttk.Label(self.frame, text="", anchor="center")
        self.counter_label.pack(pady=2)

        self.on_prev_next = None

    def set_on_prev_next(self, callback):
        self.on_prev_next = callback

    def prev(self):
        if self.on_prev_next:
            self.on_prev_next(-1)

    def next(self):
        if self.on_prev_next:
            self.on_prev_next(1)

    def update(self, slide_idx, total_selected, current_pos):
        if slide_idx is None:
            self.label.config(image="", text="Slayt seçilmedi")
            self.info_label.config(text="Slayt seçilmedi")
            self.counter_label.config(text="")
            self.btn_prev.config(state=tk.DISABLED)
            self.btn_next.config(state=tk.DISABLED)
            return

        img = self.get_preview_func(slide_idx, max_size=800)
        if img:
            try:
                w = self.label.winfo_width()
                h = self.label.winfo_height()
                if w > 1 and h > 1:
                    img.thumbnail((w, h), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.label.config(image=photo)
                self.label.image = photo
                self.info_label.config(text=f"Slayt {slide_idx+1} - {img.width}x{img.height}")
            except Exception:
                self.label.config(image="", text="Görsel yüklenemedi")
        else:
            self.label.config(image="", text="Görsel yok")
            self.info_label.config(text=f"Slayt {slide_idx+1} - Görsel yok")

        if total_selected > 1:
            self.btn_prev.config(state=tk.NORMAL)
            self.btn_next.config(state=tk.NORMAL)
            self.counter_label.config(text=f"{current_pos+1} / {total_selected}")
        else:
            self.btn_prev.config(state=tk.DISABLED)
            self.btn_next.config(state=tk.DISABLED)
            self.counter_label.config(text="")

    def _on_resize(self, event):
        pass