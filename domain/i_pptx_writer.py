from abc import ABC, abstractmethod
from typing import List
from PIL import Image

class IPPTXWriter(ABC):
    @abstractmethod
    def delete_slides(self, indices: List[int]) -> None:
        pass

    @abstractmethod
    def rebuild_with_grid(self, selected_indices: List[int], grid_image: Image.Image) -> None:
        pass

    @abstractmethod
    def replace_slide_image(self, slide_index: int, new_image: Image.Image) -> None:
        """Belirtilen slayttaki ilk resmi yenisiyle değiştirir."""
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        pass

    @abstractmethod
    def close(self):
        pass