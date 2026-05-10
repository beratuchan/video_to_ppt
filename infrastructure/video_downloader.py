import yt_dlp
import tempfile
import os
import time
import shutil
from utils.ffmpeg_utils import get_ffmpeg_path

class VideoDownloader:
    def __init__(self):
        self.temp_file = None
        self.ffmpeg_path = get_ffmpeg_path()

    def download(self, url: str) -> str:
        # En kararlı format sırası
        format_options = [
            'best[ext=mp4]',           # En iyi mp4
            'bestvideo[ext=mp4]+bestaudio',  # Ayrı video+ses, birleştir
            'best',                    # En iyi herhangi bir format
        ]

        last_exception = None
        for fmt in format_options:
            # Her format için yeni bir geçici dosya oluştur
            fd, path = tempfile.mkstemp(suffix='.mp4')
            os.close(fd)

            ydl_opts = {
                'format': fmt,
                'outtmpl': path,
                'ffmpeg_location': self.ffmpeg_path,
                'quiet': False,
                'no_warnings': False,
                'progress_hooks': [self._progress_hook],
                'retries': 10,
                'fragment_retries': 10,
                'merge_output_format': 'mp4',
                'overwrites': True,      # Var olanı sil
                'continuedl': False,     # Kaldığı yerden devam etme
                'nooverwrites': False,
            }

            try:
                print(f"[Download] Denenen format: {fmt}")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                time.sleep(0.5)
                if os.path.exists(path) and os.path.getsize(path) > 0:
                    print(f"[Download] Başarılı: {path} ({os.path.getsize(path)} bytes)")
                    self.temp_file = path
                    # Diğer format denemelerinden kalan dosyaları temizle (varsa)
                    # Burada sadece başarılı dosyayı döneceğiz
                    return path
                else:
                    raise RuntimeError("Dosya boş oluştu")
            except Exception as e:
                last_exception = e
                print(f"[Download] {fmt} formatı başarısız: {e}")
                # Başarısız dosyayı sil
                if os.path.exists(path):
                    os.unlink(path)
                continue

        if last_exception:
            raise RuntimeError(f"Video indirilemedi: {last_exception}")
        else:
            raise RuntimeError("Video indirilemedi: Bilinmeyen hata")

    def _progress_hook(self, d):
        if d['status'] == 'downloading':
            if d.get('total_bytes'):
                percent = d['downloaded_bytes'] / d['total_bytes'] * 100
                print(f"\rİndirme: %{percent:.1f}", end='')
        elif d['status'] == 'finished':
            print("\nİndirme tamamlandı, işleniyor...")

    def cleanup(self):
        if self.temp_file and os.path.exists(self.temp_file):
            os.unlink(self.temp_file)
            self.temp_file = None