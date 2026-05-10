import yt_dlp
from typing import Optional, Tuple, Dict
import numpy as np
from domain.i_video_stream import IVideoStream
from infrastructure.frame_adapters import FallbackFrameReader, IFrameReader
from config.settings import DEFAULT_FPS, DEFAULT_TARGET_WIDTH, YTDL_OPTS


class YtDlpVideoStream(IVideoStream):
    """
    YouTube (ve diğer yt-dlp destekli siteler) videolarını indirmeden,
    frame'lerini sırayla okumayı sağlar.
    """

    def __init__(self, url: str, target_fps: int = DEFAULT_FPS, target_width: int = DEFAULT_TARGET_WIDTH):
        self.url = url
        self.target_fps = target_fps
        self.target_width = target_width
        self._video_info: Optional[Dict] = None
        self._frame_reader: Optional[IFrameReader] = None
        self._current_resolution: Tuple[int, int] = (0, 0)
        self._init_video_info()
        self._open_stream()

    def _init_video_info(self):
        with yt_dlp.YoutubeDL(YTDL_OPTS) as ydl:
            try:
                info = ydl.extract_info(self.url, download=False)
                self._video_info = info
            except Exception as e:
                raise RuntimeError(f"Video bilgisi alınamadı: {e}")

    def _get_best_stream_url(self) -> str:
        formats = self._video_info.get('formats', [])
        if not formats:
            raise RuntimeError("Video için hiç format bulunamadı.")
        best_format = self._select_best_format(formats)
        if best_format:
            return best_format['url']
        direct_url = self._video_info.get('url')
        if direct_url:
            return direct_url
        raise RuntimeError("Hiçbir formattan video akış URL'si alınamadı.")

    def _select_best_format(self, formats: list) -> Optional[Dict]:
        best_format = None
        best_score = -1.0
        for f in formats:
            if f.get('url') is None:
                continue
            if f.get('vcodec', 'none') == 'none':
                continue
            score = self._calculate_format_score(f)
            if score > best_score:
                best_score = score
                best_format = f
        return best_format

    @staticmethod
    def _calculate_format_score(f: Dict) -> float:
        height = f.get('height', 0)
        tbr = f.get('tbr', 0)
        has_audio = 1 if f.get('acodec', 'none') != 'none' else 0
        # Sesli formatlara 1000 puan bonus (çözünürlük ve bitrate ile karşılaştırılabilir)
        audio_bonus = has_audio * 1000
        return height + tbr / 1000 + audio_bonus

    def _calculate_resolution(self) -> Tuple[int, int]:
        width = self._video_info.get('width', 1920)
        height = self._video_info.get('height', 1080)
        if width <= self.target_width:
            return width, height
        ratio = self.target_width / width
        new_width = self.target_width
        new_height = int(height * ratio)
        # FFmpeg için çift sayı yap
        new_height = new_height if new_height % 2 == 0 else new_height + 1
        return new_width, new_height

    def _open_stream(self):
        if self._frame_reader:
            self._frame_reader.release()
        video_url = self._get_best_stream_url()
        width, height = self._calculate_resolution()
        self._current_resolution = (width, height)
        # Doğrudan PipeFrameReader kullan
        from infrastructure.frame_adapters.pipe_frame_reader import PipeFrameReader
        self._frame_reader = PipeFrameReader(video_url, self.target_fps, (width, height))

    def get_frame(self) -> Optional[np.ndarray]:
        if self._frame_reader is None:
            return None
        return self._frame_reader.read_frame()

    def get_info(self) -> Dict:
        if not self._video_info:
            return {}
        return {
            'title': self._video_info.get('title', 'Unknown'),
            'duration_seconds': self._video_info.get('duration', 0),
            'width': self._current_resolution[0],
            'height': self._current_resolution[1],
            'fps': self.target_fps,
        }

    def close(self) -> None:
        if self._frame_reader:
            self._frame_reader.release()
            self._frame_reader = None