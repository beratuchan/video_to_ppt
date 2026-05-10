"""
Uygulama genelinde kullanılan sabitler ve yapılandırma değerleri.
"""

# Video işleme ayarları
DEFAULT_FPS = 1                     # Saniyede 1 kare (çok hızlı)
DEFAULT_TARGET_WIDTH = 640          # Daha küçük çözünürlük (hız ve bellek için)
DEFAULT_IMAGE_QUALITY = 85
MIN_SLIDE_INTERVAL_SEC = 0.5        # Minimum slayt aralığını biraz artır (gereksiz slaytları engeller)

# Sahne tespiti varsayılanları (RobustDiffStrategy)
DEFAULT_HIST_THRESHOLD = 0.999      # Histogram kullanmıyorsan değer önemsiz
DEFAULT_PIXEL_THRESHOLD = 0.02      # Piksel farkı hassasiyeti (0.01 çok hassas, 0.03 daha az)
DEFAULT_USE_HISTOGRAM = False       # Sadece piksel farkı kullan (daha hızlı)

# AbsDiffStrategy için varsayılan
DEFAULT_ABS_DIFF_THRESHOLD = 0.05

# PPTX slayt düzeni sabitleri (inç cinsinden)
SLIDE_IMAGE_LEFT_INCH = 1.0
SLIDE_IMAGE_TOP_INCH = 1.5
SLIDE_TEXT_LEFT_INCH = 1.0
SLIDE_TEXT_TOP_INCH = 6.5
SLIDE_TEXT_WIDTH_INCH = 8.0
SLIDE_TEXT_HEIGHT_INCH = 1.0
SLIDE_FONT_SIZE_TIMESTAMP = 14
SLIDE_FONT_SIZE_TEXT = 18

# Görüntü işleme
JPEG_QUALITY = 85
RESAMPLE_FILTER = "LANCZOS"  # PIL Resampling filter
DPI = 96  # Varsayılan DPI (inç başına piksel)

# FFmpeg
FFMPEG_BUFFER_SIZE = 10 ** 8
FFMPEG_LOGLEVEL = "error"

# Yt-dlp
YTDL_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
    'forcejson': True,
    'compat_opts': ['ejs'],
    'noplaylist': True,
}