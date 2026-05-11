import cv2
import numpy as np
from typing import List, Optional, Tuple
from domain.i_video_stream import IVideoStream
from infrastructure.local_video_stream import LocalVideoStream
from infrastructure.high_res_frame_extractor import HighResFrameExtractor
import tempfile
import os

class FrameCarouselService:
    """
    Bir video içinde belirli bir zaman aralığındaki frame'leri almak,
    liste halinde tutmak ve gezinmeyi sağlamak için kullanılır.
    """
    
    def __init__(self, video_path: str, start_sec: float, end_sec: float, max_frames: int = 30):
        """
        :param video_path: Video dosyasının yolu (yerel veya geçici)
        :param start_sec: Başlangıç zamanı (saniye)
        :param end_sec: Bitiş zamanı (saniye)
        :param max_frames: Aralıkta en fazla kaç frame döndürüleceği (çok uzun aralıkları örneklemek için)
        """
        self.video_path = video_path
        self.start_sec = start_sec
        self.end_sec = end_sec
        self.max_frames = max_frames
        
        self.frames: List[np.ndarray] = []
        self.current_index = 0
        self._load_frames()
    
    def _load_frames(self):
        """Video akışını açarak belirtilen aralıktaki frame'leri toplar (örneklemeli)."""
        if not os.path.exists(self.video_path):
            raise FileNotFoundError(f"Video dosyası bulunamadı: {self.video_path}")
        
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise IOError(f"Video açılamadı: {self.video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 1  # fallback
        
        start_frame = int(self.start_sec * fps)
        end_frame = int(self.end_sec * fps)
        total_frames_in_range = end_frame - start_frame
        
        # Örnekleme adımı: max_frames'i geçmemek için
        step = max(1, total_frames_in_range // self.max_frames) if total_frames_in_range > self.max_frames else 1
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        frame_idx = start_frame
        frames_collected = []
        
        while frame_idx < end_frame:
            ret, frame = cap.read()
            if not ret:
                break
            if (frame_idx - start_frame) % step == 0:
                frames_collected.append(frame.copy())
            frame_idx += 1
        
        cap.release()
        self.frames = frames_collected
        self.current_index = 0 if self.frames else -1
    
    def get_frame_count(self) -> int:
        return len(self.frames)
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        if 0 <= self.current_index < len(self.frames):
            return self.frames[self.current_index]
        return None
    
    def next_frame(self) -> Optional[np.ndarray]:
        if self.current_index + 1 < len(self.frames):
            self.current_index += 1
            return self.frames[self.current_index]
        return None
    
    def previous_frame(self) -> Optional[np.ndarray]:
        if self.current_index - 1 >= 0:
            self.current_index -= 1
            return self.frames[self.current_index]
        return None
    
    def select_current_frame(self) -> Optional[np.ndarray]:
        """Şu anki frame'i seçili olarak döndür (dışarıda işlenecek)."""
        return self.get_current_frame()