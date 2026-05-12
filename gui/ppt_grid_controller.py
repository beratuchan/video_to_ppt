import threading
import re
import cv2
import numpy as np
import hashlib
import tempfile
import os
from typing import List, Optional, Callable, Tuple
from PIL import Image

from domain.i_pptx_reader import IPPTXReader
from domain.i_pptx_writer import IPPTXWriter
from domain.i_grid_composer import IGridComposer
from domain.i_frame_extractor import IFrameExtractor

from utils.grid_utils import calculate_grid_dimensions
from utils.url_resolver import resolve_video_url
from utils.settings_manager import SettingsManager
from utils.time_utils import extract_timestamp_seconds   # <-- YENİ
from config.settings import DEFAULT_UPGRADE_TARGET_WIDTH

from services.slide_upgrader import SlideUpgrader
from services.gif_animator import GifAnimator
from services.grid_composer_service import GridComposerService
from services.segment_downloader import SegmentDownloader
from services.frame_carousel_service import FrameCarouselService

from infrastructure.high_res_frame_extractor import HighResFrameExtractor


class PPTGridController:
    """
    PowerPoint slaytları üzerinde düzenleme işlemlerini yönetir.
    """

    def __init__(self, reader: IPPTXReader, writer: IPPTXWriter, composer: IGridComposer):
        self.reader = reader
        self.writer = writer
        self.composer = composer
        self.grid_service = GridComposerService(reader, writer, composer)
        self._lock = threading.Lock()

    # ------------------- Temel Bilgiler -------------------
    def get_slide_count(self) -> int:
        return self.reader.get_slide_count()

    def get_slide_preview(self, index: int, max_size: int = 100) -> Optional[Image.Image]:
        return self.reader.get_first_image_thumbnail(index, max_size)

    # ------------------- Düzenleme İşlemleri -------------------
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

    # ------------------- Yükseltme -------------------
    def upgrade_slides(
        self,
        selected_indices: List[int],
        extractor: IFrameExtractor,
        target_width: int = 1920,
        progress_callback: Optional[Callable[[int, int, int], None]] = None
    ) -> None:
        with self._lock:
            SlideUpgrader.upgrade_slides(
                self.reader, self.writer,
                selected_indices, extractor,
                target_width, progress_callback
            )

    def upgrade_selected_slides(
        self,
        selected_indices: List[int],
        target_width: int = DEFAULT_UPGRADE_TARGET_WIDTH,
        progress_callback: Optional[Callable[[int, int, int], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> None:
        youtube_url = self.get_video_url_from_first_slide()
        if not youtube_url:
            raise ValueError("İlk slaytta video URL'si bulunamadı")
        if status_callback:
            status_callback("Video akış URL'si alınıyor...")
        video_stream_url = resolve_video_url(youtube_url)
        if not video_stream_url:
            raise ValueError("Video akış URL'si alınamadı")
        extractor = HighResFrameExtractor(video_stream_url)
        self.upgrade_slides(selected_indices, extractor, target_width, progress_callback)

    # ------------------- GIF -------------------
    def replace_slides_with_gif(self, selected_indices: List[int], duration_per_frame: float = 0.5) -> None:
        with self._lock:
            GifAnimator.replace_slides_with_gif(
                self.reader, self.writer,
                selected_indices, duration_per_frame
            )

    # ------------------- URL ve Zaman Damgası -------------------
    def get_video_url_from_first_slide(self) -> Optional[str]:
        first_slide_text = self.reader.get_slide_text(0)
        return self._extract_url_from_text(first_slide_text)

    def _extract_url_from_text(self, text: str) -> Optional[str]:
        match = re.search(r'Video URL:\s*(https?://[^\s]+)', text)
        return match.group(1) if match else None

    def get_slide_interval(self, slide_index: int, total_duration: float = None) -> Tuple[float, float]:
        """
        Bir slaydın kapsadığı video zaman aralığını döndürür.
        (başlangıç, bitiş) = (önceki slaytın zamanı, bu slaytın zamanı)
        """
        count = self.get_slide_count()
        if slide_index < 0 or slide_index >= count:
            raise ValueError("Geçersiz slayt indeksi")

        cur_text = self.reader.get_slide_text(slide_index)
        cur_sec = extract_timestamp_seconds(cur_text)          # <-- YENİ

        if slide_index > 0:
            prev_text = self.reader.get_slide_text(slide_index - 1)
            prev_sec = extract_timestamp_seconds(prev_text)    # <-- YENİ
        else:
            prev_sec = None

        if total_duration is None:
            total_duration = 3600.0  # Varsayılan 1 saat

        if cur_sec is None:
            cur_sec = min(slide_index * 5.0, total_duration - 0.1)
        if prev_sec is None:
            prev_sec = max(0.0, cur_sec - 5.0) if slide_index > 0 else 0.0

        cur_sec = min(cur_sec, total_duration)
        prev_sec = min(prev_sec, total_duration)

        start_sec = prev_sec
        end_sec = cur_sec

        if end_sec <= start_sec:
            end_sec = min(start_sec + 1.0, total_duration)
        if end_sec - start_sec < 0.3:
            end_sec = min(start_sec + 0.5, total_duration)

        return (start_sec, end_sec)

    # ------------------- Frame Carousel -------------------
    def get_video_segment_path(
        self,
        slide_index: int,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> str:
        video_url = self.get_video_url_from_first_slide()
        if not video_url:
            raise ValueError("İlk slaytta video URL'si bulunamadı")

        start_sec, end_sec = self.get_slide_interval(slide_index)

        key = f"{video_url}_{start_sec}_{end_sec}"
        key_hash = hashlib.md5(key.encode()).hexdigest()
        cache_folder = SettingsManager.get_video_storage_folder()
        if not cache_folder or not os.path.isdir(cache_folder):
            cache_folder = tempfile.gettempdir()
        segment_path = os.path.join(cache_folder, f"segment_{key_hash}.mp4")

        if os.path.exists(segment_path):
            if progress_callback:
                progress_callback(100, "Segment önbellekten alındı.")
            return segment_path

        downloader = SegmentDownloader()
        try:
            segment_path = downloader.download_segment(
                video_url, start_sec, end_sec,
                output_path=segment_path,
                progress_callback=progress_callback
            )
            return segment_path
        except Exception as e:
            raise RuntimeError(f"Segment indirilemedi: {e}") from e

    def get_frame_carousel(
        self,
        slide_index: int,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> FrameCarouselService:
        segment_path = self.get_video_segment_path(slide_index, progress_callback)
        start_sec, end_sec = self.get_slide_interval(slide_index)

        carousel = FrameCarouselService(
            video_path=segment_path,
            start_sec=start_sec,
            end_sec=end_sec,
            target_fps=10.0,
            max_frames=200,
            progress_callback=progress_callback
        )
        return carousel

    def replace_slide_with_frame(self, slide_index: int, frame_bgr: np.ndarray) -> None:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        with self._lock:
            self.writer.replace_slide_image(slide_index, pil_img)
            self.reader.update_from_writer(self.writer)