import subprocess as sp
import tempfile
import os
from typing import Tuple


class RawVideoDumper:
    """
    FFmpeg kullanarak bir videoyu ham BGR24 formatında geçici bir dosyaya yazar.
    """

    def __init__(self, input_source: str, fps: int, resolution: Tuple[int, int]):
        self.input_source = input_source
        self.fps = fps
        self.resolution = resolution
        self.temp_file = None

    def dump(self) -> str:
        """Videoyu ham formata dönüştürür ve geçici dosyanın yolunu döndürür."""
        fd, path = tempfile.mkstemp(suffix='.raw')
        os.close(fd)

        width, height = self.resolution
        cmd = [
            'ffmpeg',
            '-i', self.input_source,
            '-f', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-r', str(self.fps),
            '-s', f'{width}x{height}',
            '-an',
            '-y',
            path
        ]
        try:
            sp.run(cmd, check=True, capture_output=True, text=True)
        except sp.CalledProcessError as e:
            # Hata durumunda geçici dosyayı temizle
            if os.path.exists(path):
                os.unlink(path)
            raise RuntimeError(
                f"FFmpeg ham video dönüştürme hatası (kod {e.returncode}): {e.stderr}"
            ) from e
        except Exception as e:
            if os.path.exists(path):
                os.unlink(path)
            raise RuntimeError(f"Beklenmeyen hata: {e}") from e

        self.temp_file = path
        return path

    def cleanup(self):
        if self.temp_file and os.path.exists(self.temp_file):
            os.unlink(self.temp_file)
            self.temp_file = None