from abc import ABC, abstractmethod

class IDownloadStrategy(ABC):
    @abstractmethod
    def get_format_spec(self) -> str:
        """yt-dlp için format string'ini döndürür."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Stratejinin insan tarafından okunabilir adı (loglama için)."""
        pass