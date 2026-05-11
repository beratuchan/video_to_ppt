from abc import ABC, abstractmethod
from typing import Any, Optional
import numpy as np

class ISlideBuilder(ABC):
    @abstractmethod
    def create_new_slide(self) -> None:
        pass

    @abstractmethod
    def add_image(self, image: np.ndarray, max_width: int = 1024, quality: int = 85, vertical_align: str = "top") -> None:
        pass

    @abstractmethod
    def add_text(self, text: str, font_size: int = 18, bold: bool = False) -> None:
        pass

    @abstractmethod
    def add_timestamp(self, seconds: float, video_title: str = "") -> None:
        pass

    @abstractmethod
    def build(self) -> Any:
        pass