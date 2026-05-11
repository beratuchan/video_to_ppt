import os
import subprocess as sp
import tempfile
from typing import Optional, Callable
from utils.ffmpeg_utils import get_ffmpeg_path

class SegmentDownloader:
    """
    Videonun sadece belirli bir zaman aralığını (segment) indirir.
    yt-dlp'nin --download-sections özelliğini kullanır.
    """

    def __init__(self):
        self.ffmpeg_path = get_ffmpeg_path()

    def download_segment(
        self,
        url: str,
        start_sec: float,
        end_sec: float,
        output_path: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> str:
        """
        Belirtilen URL'deki videonun [start_sec, end_sec) aralığını indirir.
        output_path verilmezse geçici dosya oluşturur.
        Dönen değer: indirilen dosyanın yolu.
        """
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix='.mp4')
            os.close(fd)

        # Zaman formatını HH:MM:SS.xxx'e çevir
        def format_time(sec: float) -> str:
            hours = int(sec // 3600)
            minutes = int((sec % 3600) // 60)
            seconds = sec % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"

        start_str = format_time(start_sec)
        end_str = format_time(end_sec)
        section = f"{start_str}-{end_str}"

        # yt-dlp komutu: sadece belirtilen bölümü indir, sesi dahil et (isteğe bağlı)
        # --force-keyframes-at-cuts: kesme noktalarında doğru kareyi yakalamak için
        cmd = [
            'yt-dlp',
            '-f', 'best[ext=mp4]',  # en iyi mp4 formatı
            '--download-sections', f'*{section}',
            '--force-keyframes-at-cuts',
            '-o', output_path,
            url
        ]

        if progress_callback:
            progress_callback(0, f"Segment indiriliyor ({start_sec:.1f}-{end_sec:.1f} sn)...")

        try:
            # progress hook için ayrı bir mekanizma kurmak zor, basitçe sp.run kullanıyoruz
            sp.run(cmd, check=True, capture_output=True, text=True)
            if progress_callback:
                progress_callback(100, "Segment indirme tamamlandı.")
            return output_path
        except sp.CalledProcessError as e:
            raise RuntimeError(f"Segment indirme hatası: {e.stderr}") from e