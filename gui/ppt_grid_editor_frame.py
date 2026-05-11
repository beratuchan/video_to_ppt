from gui.base_ppt_grid_editor import BasePPTGridEditor

class PPTGridEditorFrame(BasePPTGridEditor):
    """
    Ana pencere içindeki PPT düzenleme sekmesi.
    Varsayılan stilleri kullanır, ek özelleştirme yok.
    """

    def __init__(self, parent, temp_video_path=None):
        super().__init__(parent, temp_video_path=temp_video_path)