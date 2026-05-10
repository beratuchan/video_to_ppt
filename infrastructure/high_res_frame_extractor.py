import subprocess as sp
import io
import cv2
import numpy as np
from PIL import Image
from typing import Optional
from utils.ffmpeg_utils import get_ffmpeg_path

class HighResFrameExtractor:
    def __init__(self, video_url: str):
        self.video_url = video_url
        self.ffmpeg_path = get_ffmpeg_path()
        print(f"[HighResFrameExtractor] URL: {video_url[:100]}...")

    def extract_frame(self, seconds: float, target_width: int = 1920, timeout: int = 30) -> Optional[np.ndarray]:
        print(f"[HighResFrameExtractor] Kare alınıyor: zaman={seconds:.3f} sn, genişlik={target_width}")
        cmd = [
            self.ffmpeg_path,
            '-ss', str(seconds),
            '-i', self.video_url,
            '-frames:v', '1',
            '-f', 'image2pipe',
            '-vcodec', 'png',
            '-vf', f'scale={target_width}:-2',
            '-loglevel', 'error',
            '-'
        ]
        try:
            proc = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
            stdout, stderr = proc.communicate(timeout=timeout)
            if proc.returncode != 0 or len(stdout) == 0:
                raise RuntimeError(f"Frame alınamadı: {stderr.decode()}")
            img = Image.open(io.BytesIO(stdout))
            rgb = np.array(img.convert('RGB'))
            bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            return bgr
        except sp.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            raise RuntimeError(f"FFmpeg işlemi {timeout} saniyede zaman aşımına uğradı: {stderr.decode()[:500]}")