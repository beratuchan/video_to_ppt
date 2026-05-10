
from abc import ABC, abstractmethod

class IProgressObserver(ABC):
    """GUI'ye ilerleme bildirimi yapmak için Observer arayüzü."""

    @abstractmethod
    def on_progress(self, percent: float, message: str) -> None:
        """
        percent: 0-100 arası ilerleme yüzdesi
        message: Kullanıcıya gösterilecek bilgi metni (örn: "Sahne tespit ediliyor...")
        """
        pass

    @abstractmethod
    def on_error(self, url: str, error_msg: str) -> None:
        """Bir URL işlenirken hata oluştuğunda çağrılır (çoklu URL senaryosu)."""
        pass

    @abstractmethod
    def on_finished(self, success_count: int, total_count: int) -> None:
        """Tüm işlemler bittiğinde çağrılır."""
        pass