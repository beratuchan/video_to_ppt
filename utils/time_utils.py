"""
Zaman ile ilgili yardımcı fonksiyonlar.
"""

def format_timestamp(seconds: float, include_ms: bool = True) -> str:
    """
    Saniye cinsinden verilen süreyi MM:SS:mmm formatında döndürür.
    Örnek: 125.5 -> "02:05:500"
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    if include_ms:
        return f"{minutes:02d}:{secs:02d}:{ms:03d}"
    else:
        return f"{minutes:02d}:{secs:02d}"