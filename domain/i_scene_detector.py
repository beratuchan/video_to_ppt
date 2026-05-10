from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np

class ISceneDetector(ABC):
    """Sahne geçişi tespit stratejileri için arayüz."""

    @abstractmethod
    def is_scene_change(self, prev_frame: Optional[np.ndarray], curr_frame: np.ndarray) -> bool:
        """
        İki frame arasında anlamlı bir sahne değişimi olup olmadığını döndürür.
        prev_frame = None ise ilk frame olarak kabul edilir (genellikle True döndürülür).
        """
        pass

    @abstractmethod
    def set_threshold(self, value: float) -> None:
        """Duyarlılık eşik değerini ayarlar (0-1 arası, varsayılan 0.3 gibi)."""
        pass