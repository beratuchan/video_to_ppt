import threading
from typing import List, Optional, Callable
from PIL import Image
from domain.i_pptx_reader import IPPTXReader
from domain.i_pptx_writer import IPPTXWriter
from domain.i_grid_composer import IGridComposer
from utils.grid_utils import calculate_grid_dimensions
from services.slide_upgrader import SlideUpgrader
from services.gif_animator import GifAnimator
from services.grid_composer_service import GridComposerService
from domain.i_frame_extractor import IFrameExtractor
import re

class PPTGridController:
    def __init__(self, reader: IPPTXReader, writer: IPPTXWriter, composer: IGridComposer):
        self.reader = reader
        self.writer = writer
        self.composer = composer
        self.grid_service = GridComposerService(reader, writer, composer)
        self._lock = threading.Lock()      # YENİ: writer işlemlerini korumak için kilit

    def get_slide_count(self) -> int:
        return self.reader.get_slide_count()

    def get_slide_preview(self, index: int, max_size: int = 100) -> Optional[Image.Image]:
        return self.reader.get_first_image_thumbnail(index, max_size)

    def delete_slides(self, selected_indices: List[int]) -> None:
        if not selected_indices:
            raise ValueError("Silinecek slayt seçilmedi")
        with self._lock:
            self.writer.delete_slides(selected_indices)
            self.reader.update_from_writer(self.writer)

    def apply_grid(self, selected_indices: List[int], margin: int = 10) -> None:
        with self._lock:
            self.grid_service.apply_grid(selected_indices, margin)

    def save(self, path: str) -> None:
        with self._lock:
            self.writer.save(path)

    def close(self):
        with self._lock:
            self.reader.close()
            self.writer.close()

    def upgrade_slides(self, selected_indices: List[int], extractor: IFrameExtractor, target_width: int = 1920, progress_callback: Optional[Callable[[int, int, int], None]] = None) -> None:
        with self._lock:
            SlideUpgrader.upgrade_slides(self.reader, self.writer, selected_indices, extractor, target_width, progress_callback)

    def replace_slides_with_gif(self, selected_indices: List[int], duration_per_frame: float = 0.5) -> None:
        with self._lock:
            GifAnimator.replace_slides_with_gif(self.reader, self.writer, selected_indices, duration_per_frame)

    def get_video_url_from_first_slide(self) -> Optional[str]:
        first_slide_text = self.reader.get_slide_text(0)
        return self._extract_url_from_text(first_slide_text)

    def _extract_url_from_text(self, text: str) -> Optional[str]:
        match = re.search(r'Video URL:\s*(https?://[^\s]+)', text)
        return match.group(1) if match else None