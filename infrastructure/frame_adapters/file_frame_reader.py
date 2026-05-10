import cv2
import numpy as np
from typing import Optional
from .i_frame_reader import IFrameReader

class FileFrameReader(IFrameReader):
    """
    OpenCV kullanarak bir video dosyasından (raw veya sıkıştırılmış) frame okur.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.cap = cv2.VideoCapture(file_path)
        if not self.cap.isOpened():
            raise IOError(f"Video dosyası açılamadı: {file_path}")

    def read_frame(self) -> Optional[np.ndarray]:
        if self.cap is None:
            return None
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None