from typing import List, Optional, Callable
from PIL import Image
from domain.i_pptx_reader import IPPTXReader
from domain.i_pptx_writer import IPPTXWriter
from domain.i_grid_composer import IGridComposer
from utils.grid_utils import calculate_grid_dimensions
from infrastructure.high_res_frame_extractor import HighResFrameExtractor
from utils.url_resolver import resolve_video_url
import re
import cv2
import numpy as np
import tempfile
import os
from domain.i_frame_extractor import IFrameExtractor

class PPTGridController:
    def __init__(self, reader: IPPTXReader, writer: IPPTXWriter, composer: IGridComposer):
        self.reader = reader
        self.writer = writer
        self.composer = composer

    def get_slide_count(self) -> int:
        return self.reader.get_slide_count()

    def get_slide_preview(self, index: int, max_size: int = 100) -> Optional[Image.Image]:
        return self.reader.get_first_image_thumbnail(index, max_size)

    def delete_slides(self, selected_indices: List[int]) -> None:
        if not selected_indices:
            raise ValueError("Silinecek slayt seçilmedi")
        self.writer.delete_slides(selected_indices)
        self.reader.update_from_writer(self.writer)

    def apply_grid(self, selected_indices: List[int], margin: int = 10) -> None:
        if len(selected_indices) < 2:
            raise ValueError("En az iki slayt seçmelisiniz")
        images = []
        for idx in selected_indices:
            imgs = self.reader.get_slide_images(idx)
            images.extend(imgs)
        if not images:
            raise ValueError("Seçilen slaytlarda hiç resim bulunamadı")
        rows, cols = calculate_grid_dimensions(len(images))
        grid_image = self.composer.compose(images, rows, cols, margin)
        self.writer.rebuild_with_grid(selected_indices, grid_image)
        self.reader.update_from_writer(self.writer)

    def save(self, path: str) -> None:
        self.writer.save(path)

    def close(self):
        self.reader.close()
        self.writer.close()

    def upgrade_slides(self, selected_indices: List[int], extractor: IFrameExtractor, target_width: int = 1920, progress_callback: Optional[Callable[[int, int, int], None]] = None) -> None:
        if not selected_indices:
            raise ValueError("Yükseltilecek slayt seçilmedi")
        # video_url'yi ilk slayttan al, extractor zaten bu URL ile oluşturulmuş olmalı
        total = len(selected_indices)
        for i, idx in enumerate(selected_indices):
            if progress_callback:
                progress_callback(i, total, idx)
            slide_text = self.reader.get_slide_text(idx)
            seconds = self._extract_timestamp_from_text(slide_text)
            if seconds is None:
                continue
            high_res_bgr = extractor.extract_frame(seconds, target_width=target_width)
            if high_res_bgr is None:
                continue
            high_res_rgb = cv2.cvtColor(high_res_bgr, cv2.COLOR_BGR2RGB)
            high_res_pil = Image.fromarray(high_res_rgb)
            self.writer.replace_slide_image(idx, high_res_pil)
        self.reader.update_from_writer(self.writer)

    # ----- Yeni GIF Stratejisi -----
    def replace_slides_with_gif(self, selected_indices: List[int], duration_per_frame: float = 0.5) -> None:
        """
        Seçili slaytlardaki ilk resimleri kullanarak bir GIF animasyonu oluşturur,
        diğer slaytları siler ve GIF'i kalan slayta resim olarak ekler.
        """
        if len(selected_indices) < 2:
            raise ValueError("En az iki slayt seçmelisiniz")

        # 1. Seçili slaytlardaki ilk resimleri topla (PIL Image)
        images = []
        for idx in selected_indices:
            imgs = self.reader.get_slide_images(idx)
            if imgs:
                # İlk resmi al, RGB moduna çevir
                img = imgs[0].convert('RGB')
                images.append(img)
        if not images:
            raise ValueError("Seçilen slaytlarda hiç resim bulunamadı")

        # 2. Geçici GIF dosyası oluştur
        fd, gif_path = tempfile.mkstemp(suffix='.gif')
        os.close(fd)
        try:
            duration_ms = int(duration_per_frame * 1000)
            images[0].save(
                gif_path,
                save_all=True,
                append_images=images[1:],
                duration=duration_ms,
                loop=0,           # sonsuz döngü
                disposal=2
            )

            # 3. Diğer slaytları sil (sadece en küçük indeksli slayt kalacak)
            min_idx = min(selected_indices)
            other_indices = [idx for idx in selected_indices if idx != min_idx]
            if other_indices:
                self.writer.delete_slides(other_indices)

            # 4. Kalan slaytın içeriğini tamamen temizle ve GIF'i ekle
            self.writer.replace_slide_with_image(min_idx, gif_path)

            # 5. Değişiklikleri kaydet
            self.writer.save(self.writer.source_path)
            self.reader.update_from_writer(self.writer)

        finally:
            if os.path.exists(gif_path):
                os.unlink(gif_path)

    # ----- Yardımcı Metodlar -----
    def _extract_url_from_text(self, text: str) -> Optional[str]:
        match = re.search(r'Video URL:\s*(https?://[^\s]+)', text)
        return match.group(1) if match else None

    def _extract_timestamp_from_text(self, text: str) -> Optional[float]:
        match = re.search(r'(\d{2}):(\d{2}):(\d{3})', text)
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            ms = int(match.group(3))
            return minutes * 60 + seconds + ms / 1000.0
        return None
    
    def get_video_url_from_first_slide(self) -> Optional[str]:
        first_slide_text = self.reader.get_slide_text(0)
        return self._extract_url_from_text(first_slide_text)