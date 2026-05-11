# gui/slide_selection_manager.py

class SlideSelectionManager:
    def __init__(self, total_slides, update_ui_callback):
        self.total_slides = total_slides
        self.selected_indices = []
        self.carousel_index = 0
        self.last_clicked_index = None
        self.update_ui_callback = update_ui_callback

    def set_total_slides(self, total):
        self.total_slides = total
        self.clear_selection()

    def clear_selection(self):
        self.selected_indices = []
        self.carousel_index = 0
        self.last_clicked_index = None
        self._notify_update()

    def toggle_single(self, idx):
        if idx in self.selected_indices:
            self.selected_indices.remove(idx)
        else:
            self.selected_indices.append(idx)
        self.selected_indices.sort()
        if idx in self.selected_indices:
            self.carousel_index = self.selected_indices.index(idx)
        else:
            if self.carousel_index >= len(self.selected_indices):
                self.carousel_index = max(0, len(self.selected_indices) - 1)
        self._notify_update()

    def select_range(self, start, end):
        new_sel = set(self.selected_indices)
        for i in range(min(start, end), max(start, end) + 1):
            new_sel.add(i)
        self.selected_indices = sorted(new_sel)
        self.carousel_index = 0
        self._notify_update()

    def set_selection(self, indices):
        self.selected_indices = sorted(set(indices))
        if self.selected_indices and self.carousel_index >= len(self.selected_indices):
            self.carousel_index = len(self.selected_indices) - 1
        self._notify_update()

    def get_current_slide(self):
        if self.selected_indices and 0 <= self.carousel_index < len(self.selected_indices):
            return self.selected_indices[self.carousel_index]
        return None

    def move_carousel(self, delta):
        if len(self.selected_indices) <= 1:
            return
        self.carousel_index = (self.carousel_index + delta) % len(self.selected_indices)
        self._notify_update()

    def _notify_update(self):
        if self.update_ui_callback:
            self.update_ui_callback(self)