# gui/frame_carousel_widget.py

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import numpy as np
from typing import Callable, Optional


class FrameCarouselWidget(tk.Frame):
    """
    Video kareleri arasında gezinmeyi sağlayan widget.
    Uzun basma ile hızlı geçiş desteği.
    """

    def __init__(
        self,
        parent,
        carousel_service,          # FrameCarouselService instance
        on_select_callback: Callable[[np.ndarray], None],
        on_cancel_callback: Callable[[], None]
    ):
        super().__init__(parent)
        self.carousel = carousel_service
        self.on_select = on_select_callback
        self.on_cancel = on_cancel_callback

        self.current_photo = None
        self._long_press_timer = None
        self._long_press_direction = 0
        self._repeat_delay = 500      # ms
        self._repeat_interval = 100   # ms

        self._create_widgets()
        self._update_image()
        self.image_label.bind("<Configure>", self._on_label_resize)

    def _create_widgets(self):
        # Ana frame'i doldur
        self.pack(fill=tk.BOTH, expand=True)

        # Resim etiketi
        self.image_label = tk.Label(self, bg="#ffffff", relief=tk.SUNKEN, anchor="center")
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Bilgi etiketi
        self.info_label = ttk.Label(self, text="", anchor="center")
        self.info_label.pack(pady=5)

        # Buton çerçevesi
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        self.btn_prev = tk.Button(btn_frame, text="◄", command=self._prev_click, width=4)
        self.btn_prev.pack(side=tk.LEFT, padx=5)

        self.btn_next = tk.Button(btn_frame, text="►", command=self._next_click, width=4)
        self.btn_next.pack(side=tk.LEFT, padx=5)

        self.btn_select = tk.Button(btn_frame, text="Yeni Kareyi Seç", command=self._select)
        self.btn_select.pack(side=tk.LEFT, padx=10)

        self.btn_cancel = tk.Button(btn_frame, text="Vazgeç", command=self._cancel)
        self.btn_cancel.pack(side=tk.LEFT, padx=5)

        # Uzun basma olayları
        self.btn_prev.bind("<ButtonPress-1>", lambda e: self._start_long_press(-1))
        self.btn_prev.bind("<ButtonRelease-1>", self._stop_long_press)
        self.btn_next.bind("<ButtonPress-1>", lambda e: self._start_long_press(1))
        self.btn_next.bind("<ButtonRelease-1>", self._stop_long_press)

        self._update_info()

    def _on_label_resize(self, event):
        self._update_image()

    def _update_info(self):
        total = self.carousel.get_frame_count()
        idx = self.carousel.current_index + 1 if total > 0 else 0
        self.info_label.config(text=f"Kare {idx} / {total}")

    def _update_image(self):
        frame = self.carousel.get_current_frame()
        if frame is None:
            self.image_label.config(image="", text="Kare yok")
            return

        # BGR -> RGB -> PIL
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)

        # Label boyutunu al
        w = self.image_label.winfo_width()
        h = self.image_label.winfo_height()
        if w <= 1:
            w = 400
        if h <= 1:
            h = 300

        # Resmi label boyutuna sığdır (oran korunarak)
        pil_img.thumbnail((w, h), Image.Resampling.LANCZOS)

        self.current_photo = ImageTk.PhotoImage(pil_img)
        self.image_label.config(image=self.current_photo)
        self._update_info()

    def _prev_click(self):
        self.carousel.previous_frame()
        self._update_image()

    def _next_click(self):
        self.carousel.next_frame()
        self._update_image()

    def _start_long_press(self, direction: int):
        self._long_press_direction = direction
        if self._long_press_timer is None:
            self._long_press_timer = self.after(self._repeat_delay, self._repeat_long_press)

    def _repeat_long_press(self):
        if self._long_press_direction == -1:
            self.carousel.previous_frame()
        elif self._long_press_direction == 1:
            self.carousel.next_frame()
        self._update_image()
        self._long_press_timer = self.after(self._repeat_interval, self._repeat_long_press)

    def _stop_long_press(self, event=None):
        if self._long_press_timer:
            self.after_cancel(self._long_press_timer)
            self._long_press_timer = None
        self._long_press_direction = 0

    def _select(self):
        frame = self.carousel.select_current_frame()
        if frame is not None:
            self.on_select(frame)

    def _cancel(self):
        self.on_cancel()