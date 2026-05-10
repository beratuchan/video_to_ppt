import yt_dlp
from typing import Optional

def resolve_video_url(youtube_url: str) -> Optional[str]:
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'forcejson': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(youtube_url, download=False)
            formats = info.get('formats', [])
            best = None
            for f in formats:
                if f.get('vcodec') != 'none' and f.get('url'):
                    if best is None or f.get('height', 0) > best.get('height', 0):
                        best = f
            return best['url'] if best else None
        except Exception:
            return None