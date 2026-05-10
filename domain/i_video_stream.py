from abc import ABC, abstractmethod
from typing import Optional, Dict
import numpy as np

class IVideoStream(ABC):
    """Video akışından frame okuma ve meta bilgi alma arayüzü."""

    @abstractmethod
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Bir sonraki frame'i (numpy array, BGR formatında) döndürür.
        Akış sona erdiyse None döner.
        """
        pass

    @abstractmethod
    def get_info(self) -> Dict:
        """
        Video bilgilerini içeren sözlük döndürür.
        Anahtarlar: 'title', 'duration_seconds', 'width', 'height', 'fps'
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Akışla ilişkili kaynakları serbest bırakır."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()