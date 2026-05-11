# gui/ppt_grid_controller.py (tam dosya, yeni metodlar eklendi)

import threading
from typing import List, Optional, Callable, Tuple
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
import cv2
import numpy as np

class PPTGridController:
    def __init__(self, reader: IPPTXReader, writer: IPPTXWriter, composer: IGridComposer):
        self.reader = reader
        self.writer = writer
        self.composer = composer
        self.grid_service = GridComposerService(reader, writer, composer)
        self._lock = threading.Lock()

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

    # ========== YENİ METODLAR (F5 Carousel için) ==========
    def get_slide_time_range(self, slide_index: int, total_duration: float = None) -> Tuple[float, float]:
        """
        Belirtilen slaydın zaman aralığını döndürür: (start_sec, end_sec)
        start_sec: bir önceki slaydın zamanı (veya 0)
        end_sec: bir sonraki slaydın zamanı (veya total_duration)
        total_duration: son slayt için gerekli, eğer None verilmezse videonun gerçek süresi bilinmiyorsa büyük sayı verilir.
        """
        count = self.get_slide_count()
        if slide_index < 0 or slide_index >= count:
            raise ValueError("Geçersiz slayt indeksi")
        
        # Önceki slaytın zamanını al
        if slide_index > 0:
            prev_text = self.reader.get_slide_text(slide_index - 1)
            prev_sec = self._extract_timestamp_from_text(prev_text)
            if prev_sec is None:
                prev_sec = 0.0
        else:
            prev_sec = 0.0
        
        # Sonraki slaytın zamanını al
        if slide_index < count - 1:
            next_text = self.reader.get_slide_text(slide_index + 1)
            next_sec = self._extract_timestamp_from_text(next_text)
            if next_sec is None:
                next_sec = total_duration if total_duration is not None else float('inf')
        else:
            next_sec = total_duration if total_duration is not None else float('inf')
        
        return (prev_sec, next_sec)
    
    def _extract_timestamp_from_text(self, text: str) -> Optional[float]:
        """Slayt metninden MM:SS:mmm formatında zaman damgasını çıkarır."""
        match = re.search(r'(\d{2}):(\d{2}):(\d{3})', text)
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            ms = int(match.group(3))
            return minutes * 60 + seconds + ms / 1000.0
        return None

    def replace_slide_with_frame(self, slide_index: int, frame_bgr: np.ndarray) -> None:
        """Slayttaki mevcut resmi, verilen BGR frame ile değiştirir."""
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        
        with self._lock:
            self.writer.replace_slide_image(slide_index, pil_img)
            self.reader.update_from_writer(self.writer)