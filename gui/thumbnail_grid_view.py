# gui/thumbnail_grid_view.py
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk

class ThumbnailGridView:
    def __init__(self, parent, on_slide_click, get_preview_func, container=None):
        """
        parent: Tkinter parent (genelde üst frame)
        on_slide_click: callback(event, slide_index)
        get_preview_func: func(slide_index, max_size) -> PIL.Image
        container: eğer verilirse, bu frame içine thumbnail’ler yerleştirilir.
                   Verilmezse yeni bir ttk.Frame oluşturulup parent içine pack’lenir.
        """
        self.parent = parent
        self.on_slide_click = on_slide_click
        self.get_preview_func = get_preview_func
        self.thumbnails = []  # (photo, var, index)

        if container is not None:
            self.inner = container
        else:
            self.inner = ttk.Frame(parent)
            self.inner.pack(fill=tk.BOTH, expand=True)

    def clear(self):
        for widget in self.inner.winfo_children():
            widget.destroy()
        self.thumbnails.clear()

    def rebuild(self, count, slide_bg_color):
        self.clear()
        if count == 0:
            ttk.Label(self.inner, text="Slayt yok").pack()
            return

        cols = 3
        thumb_size = 220
        for idx in range(count):
            if idx % cols == 0:
                row_frame = ttk.Frame(self.inner)
                row_frame.pack(anchor="w", pady=10)
            self._add_thumbnail(idx, row_frame, thumb_size, slide_bg_color)

    def _add_thumbnail(self, idx, parent_frame, thumb_size, bg_color):
        slide_frame = tk.Frame(parent_frame, relief=tk.RIDGE, borderwidth=1, bg=bg_color, cursor="hand2")
        slide_frame.pack(side=tk.LEFT, padx=10, pady=5)
        slide_frame.bind("<Button-1>", lambda e, i=idx: self.on_slide_click(e, i))

        img = self.get_preview_func(idx, max_size=thumb_size)
        if img:
            photo = ImageTk.PhotoImage(img)
            label_img = tk.Label(slide_frame, image=photo, bg=bg_color)
            label_img.image = photo
            label_img.pack(padx=2, pady=2)
            label_img.bind("<Button-1>", lambda e, i=idx: self.on_slide_click(e, i))
        else:
            placeholder = tk.Label(slide_frame, text="[Resim yok]", width=25, height=15, bg='lightgray')
            placeholder.pack()
            placeholder.bind("<Button-1>", lambda e, i=idx: self.on_slide_click(e, i))

        lbl_num = tk.Label(slide_frame, text=f"Slayt {idx+1}", font=("Arial", 10, "bold"), bg=bg_color)
        lbl_num.pack()
        var = tk.BooleanVar()
        cb = ttk.Checkbutton(slide_frame, variable=var, text="Seç",
                             command=lambda i=idx: self._on_checkbox_click(i))
        cb.pack()
        self.thumbnails.append((photo if img else None, var, idx))

    def _on_checkbox_click(self, idx):
        # Simulate a dummy event with state=0 (no shift)
        class DummyEvent:
            state = 0
        self.on_slide_click(DummyEvent(), idx)

    def update_checkboxes(self, selected_indices):
        for photo, var, idx in self.thumbnails:
            var.set(idx in selected_indices)