import yt_dlp
import tempfile
import os
import time
from typing import List, Optional, Callable
from domain.i_download_strategy import IDownloadStrategy
from strategies.download import BestMp4Strategy, BestVideoPlusAudioStrategy, BestAnyStrategy
from utils.ffmpeg_utils import get_ffmpeg_path

class VideoDownloader:
    def __init__(self, strategies: Optional[List[IDownloadStrategy]] = None):
        self.temp_file = None
        self.ffmpeg_path = get_ffmpeg_path()
        if strategies is None:
            strategies = [
                BestMp4Strategy(),
                BestVideoPlusAudioStrategy(),
                BestAnyStrategy(),
            ]
        self.strategies = strategies

    def download(self, url: str, progress_callback: Optional[Callable[[Optional[float], str], None]] = None, permanent_path: Optional[str] = None) -> str:
        """
        Videoyu indirir.
        :param progress_callback: (percent, message) -> None. percent None ise sadece mesaj.
        :param permanent_path: Belirtilirse dosya bu yola kaydedilir (geçici değil)
        """
        last_exception = None
        for strategy in self.strategies:
            # Dosya yolunu belirle
            if permanent_path:
                path = permanent_path
                # Eğer dosya zaten varsa üzerine yazmadan önce temizle
                if os.path.exists(path):
                    os.unlink(path)
            else:
                fd, path = tempfile.mkstemp(suffix='.mp4')
                os.close(fd)

            ydl_opts = {
                'format': strategy.get_format_spec(),
                'outtmpl': path,
                'ffmpeg_location': self.ffmpeg_path,
                'quiet': False,
                'no_warnings': False,
                'progress_hooks': [self._make_progress_hook(progress_callback)],
                'retries': 10,
                'fragment_retries': 10,
                'merge_output_format': 'mp4',
                'overwrites': True,
                'continuedl': False,
                'nooverwrites': False,
                'noplaylist': True,      # <-- YENİ: playlist indirmeyi engelle
            }

            try:
                print(f"[Download] Denenen strateji: {strategy.get_name()} ({strategy.get_format_spec()})")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                time.sleep(0.5)
                if os.path.exists(path) and os.path.getsize(path) > 0:
                    print(f"[Download] Başarılı: {path} ({os.path.getsize(path)} bytes)")
                    if not permanent_path:
                        self.temp_file = path
                    return path
                else:
                    raise RuntimeError("Dosya boş oluştu")
            except Exception as e:
                last_exception = e
                print(f"[Download] {strategy.get_name()} başarısız: {e}")
                if os.path.exists(path) and not permanent_path:
                    os.unlink(path)
                continue

        if last_exception:
            raise RuntimeError(f"Video indirilemedi: {last_exception}")
        else:
            raise RuntimeError("Video indirilemedi: Bilinmeyen hata")

    def _make_progress_hook(self, callback: Optional[Callable[[Optional[float], str], None]]):
        def progress_hook(d):
            if d['status'] == 'downloading':
                if d.get('total_bytes'):
                    percent = d['downloaded_bytes'] / d['total_bytes'] * 100
                    msg = f"İndiriliyor: %{percent:.1f}"
                    print(f"\r{msg}", end='')
                    if callback:
                        callback(percent, msg)
                else:
                    downloaded = d.get('downloaded_bytes', 0)
                    msg = f"İndiriliyor: {downloaded // 1024} KB"
                    if callback:
                        callback(None, msg)
            elif d['status'] == 'finished':
                print("\nİndirme tamamlandı, işleniyor...")
                if callback:
                    callback(100, "İndirme tamamlandı, işleniyor...")
        return progress_hook

    def cleanup(self):
        if self.temp_file and os.path.exists(self.temp_file):
            os.unlink(self.temp_file)
            self.temp_file = None