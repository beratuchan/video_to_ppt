"""
Zaman ile ilgili yardımcı fonksiyonlar.
"""

from typing import Optional
import re

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


def extract_timestamp_seconds(text: str) -> Optional[float]:
    """
    Slayt metninden MM:SS:mmm formatındaki zaman damgasını saniye cinsinden döndürür.
    Örnek: "02:05:500" -> 125.5
    Bulunamazsa None döner.
    """
    match = re.search(r'(\d{2}):(\d{2}):(\d{3})', text)
    if match:
        minutes = int(match.group(1))
        seconds = int(match.group(2))
        ms = int(match.group(3))
        return minutes * 60 + seconds + ms / 1000.0
    return None