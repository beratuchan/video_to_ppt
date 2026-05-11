import cv2
import numpy as np
from typing import Optional, Dict
from domain.i_video_stream import IVideoStream
from config.settings import MIN_FRAME_INTERVAL

class LocalVideoStream(IVideoStream):
    def __init__(self, file_path: str, target_fps: int = 1, target_width: int = 640):
        self.file_path = file_path
        self.target_fps = target_fps
        self.target_width = target_width
        self.cap = cv2.VideoCapture(file_path)
        if not self.cap.isOpened():
            raise IOError(f"Video açılamadı: {file_path}")
        self._orig_fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self._orig_fps <= 0:
            raise IOError("Video FPS bilgisi alınamadı")
        self._frame_interval = max(MIN_FRAME_INTERVAL, int(round(self._orig_fps / target_fps)))
        self._frame_index = 0
        self._total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Efektif FPS = orijinal FPS / frame_interval
        self._effective_fps = self._orig_fps / self._frame_interval

        # İlk frame'i okuyarak gerçek yüksekliği hesapla (target_width'e göre ölçeklenmiş)
        ret, first_frame = self.cap.read()
        if ret:
            orig_height = first_frame.shape[0]
            orig_width = first_frame.shape[1]
            if self.target_width and orig_width > self.target_width:
                ratio = self.target_width / orig_width
                self._actual_height = int(orig_height * ratio)
            else:
                self._actual_height = orig_height
        else:
            self._actual_height = 0
        # Okuma pozisyonunu başa al
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def get_frame(self) -> Optional[np.ndarray]:
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self._frame_index)
        ret, frame = self.cap.read()
        if not ret:
            return None
        self._frame_index += self._frame_interval
        if self.target_width and frame.shape[1] > self.target_width:
            ratio = self.target_width / frame.shape[1]
            new_h = int(frame.shape[0] * ratio)
            frame = cv2.resize(frame, (self.target_width, new_h), interpolation=cv2.INTER_LANCZOS4)
        return frame

    def get_info(self) -> Dict:
        duration = self._total_frames / self._orig_fps if self._orig_fps > 0 else 0
        return {
            'title': 'Video',
            'duration_seconds': duration,
            'width': self.target_width,
            'height': self._actual_height,
            'fps': self._effective_fps,      # DÜZELTİLDİ: efektif FPS döndürülüyor
        }

    def close(self):
        if self.cap:
            self.cap.release()