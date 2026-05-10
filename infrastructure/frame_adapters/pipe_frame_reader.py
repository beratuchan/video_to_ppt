import subprocess as sp
import numpy as np
from typing import Optional, Tuple
from .i_frame_reader import IFrameReader
from config.settings import FFMPEG_BUFFER_SIZE, FFMPEG_LOGLEVEL


class PipeFrameReader(IFrameReader):
    def __init__(self, input_source: str, fps: int, resolution: Tuple[int, int], buffer_size: int = FFMPEG_BUFFER_SIZE):
        self.input_source = input_source
        self.fps = fps
        self.width, self.height = resolution
        self.proc = None
        self._frame_size = self.width * self.height * 3
        self._open()

    def _open(self):
        cmd = [
            'ffmpeg',  # Adım 7'de dinamik yol eklenecek
            '-i', self.input_source,
            '-f', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-r', str(self.fps),
            '-s', f'{self.width}x{self.height}',
            '-an',
            '-loglevel', FFMPEG_LOGLEVEL,
            '-'
        ]
        # stderr'i yok sayarak buffer dolmasını engelle
        self.proc = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.DEVNULL, bufsize=self._frame_size * 2)

    def read_frame(self) -> Optional[np.ndarray]:
        if self.proc is None or self.proc.stdout is None:
            return None
        raw = self.proc.stdout.read(self._frame_size)
        if len(raw) != self._frame_size:
            return None
        frame = np.frombuffer(raw, dtype=np.uint8).reshape((self.height, self.width, 3))
        return frame

    def release(self):
        if self.proc:
            self.proc.terminate()
            self.proc = None