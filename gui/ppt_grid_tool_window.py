import tkinter as tk
import os
from gui.base_ppt_grid_editor import BasePPTGridEditor

class PPTGridToolWindow(tk.Toplevel):
    """
    Bağımsız PPT düzenleme penceresi. Stilli butonlar ve geçici video cleanup içerir.
    """

    def __init__(self, parent, default_pptx_path=None, temp_video_path=None):
        super().__init__(parent)
        self.title("PowerPoint Düzenleme Aracı")
        self.geometry("1100x800")
        self.temp_video_path = temp_video_path

        # İç frame olarak stilli editor'ü kullan
        self.editor = _StyledPPTGridEditor(self, temp_video_path=temp_video_path)
        self.editor.pack(fill=tk.BOTH, expand=True)

        if default_pptx_path and os.path.exists(default_pptx_path):
            self.editor.set_pptx_and_video(default_pptx_path, temp_video_path)

        self.protocol("WM_DELETE_WINDOW", self._on_close_cleanup)

    def _on_close_cleanup(self):
        if self.temp_video_path and os.path.exists(self.temp_video_path):
            try:
                os.unlink(self.temp_video_path)
                print(f"[Cleanup] Geçici video silindi: {self.temp_video_path}")
            except Exception as e:
                print(f"[Cleanup] Video silinemedi: {e}")
        self.destroy()


class _StyledPPTGridEditor(BasePPTGridEditor):
    """
    PPTGridToolWindow için özel stillendirilmiş editor.
    Butonlar renkli.
    """

    def get_button_bg_color(self, button_name: str) -> str:
        colors = {
            "delete": "#ff9999",
            "grid": "#99ccff",
            "upgrade": "#aaffaa",
            "gif": ""  # varsayılan
        }
        return colors.get(button_name, "")

    # Diğer stillendirme metodları isteğe bağlı override edilebilir