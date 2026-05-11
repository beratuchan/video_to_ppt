from abc import ABC, abstractmethod
from typing import Optional
import numpy as np

class IFrameExtractor(ABC):
    @abstractmethod
    def extract_frame(self, seconds: float, target_width: int = 1920) -> Optional[np.ndarray]:
        """Belirtilen saniyedeki kareyi yüksek çözünürlükte döndürür (BGR formatında)."""
        pass