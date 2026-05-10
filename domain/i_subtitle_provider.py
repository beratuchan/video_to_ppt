from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class ISubtitleProvider(ABC):
    """
    Altyazı sağlayıcısı arayüzü.
    Bu sürümde kullanılmayacak, ancak Open/Closed prensibi gereği hazır tutulmaktadır.
    Gelecekteki sürümlerde implemente edilebilir.
    """

    @abstractmethod
    def fetch_subtitles(self, video_url: str, lang: str = "tr") -> Optional[List[Dict]]:
        """
        Video URL'sine ait altyazıları getirir.
        Dönen liste: [{"start": float, "end": float, "text": str}, ...]
        Başarısızsa None döner.
        """
        pass

    @abstractmethod
    def has_subtitles(self, video_url: str) -> bool:
        """Videoda istenen dilde altyazı olup olmadığını kontrol eder."""
        pass