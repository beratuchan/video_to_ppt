import os
import shutil

def get_ffmpeg_path() -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_ffmpeg = os.path.join(base_dir, "ffmpeg.exe")
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    raise RuntimeError("ffmpeg.exe bulunamadı. Lütfen proje klasörüne ffmpeg.exe koyun veya PATH'e ekleyin.")