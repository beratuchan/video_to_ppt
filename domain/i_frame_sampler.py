from abc import ABC, abstractmethod
from typing import Optional
import numpy as np

class IFrameSampler(ABC):
    """
    Video akışından hangi frame'lerin işleneceğine karar veren strateji.
    """
    @abstractmethod
    def should_sample(self, frame_index: int, frame: Optional[np.ndarray], current_time: float) -> bool:
        """
        Belirtilen frame'in işlenmesi gerekip gerekmediğini döndürür.
        - frame_index: kaçıncı frame (0'dan başlar)
        - frame: frame verisi (None olabilir)
        - current_time: videoda geçen saniye
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Yeni video başlangıcında sıfırlama."""
        pass