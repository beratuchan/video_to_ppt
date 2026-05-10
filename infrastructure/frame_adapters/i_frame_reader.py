from abc import ABC, abstractmethod
from typing import Optional
import numpy as np

class IFrameReader(ABC):
    """Ham frame okuyucuları için ortak arayüz."""

    @abstractmethod
    def read_frame(self) -> Optional[np.ndarray]:
        """Sonraki frame'i (BGR numpy array) döndürür, bitince None."""
        pass

    @abstractmethod
    def release(self) -> None:
        """Kaynakları serbest bırakır."""
        pass