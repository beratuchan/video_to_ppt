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
    def replace_slide_with_image(self, slide_index: int, image_path: str, left_inch: float = 1.0, top_inch: float = 1.0, width_inch: float = 8.0, height_inch: float = 6.0) -> None:
        """Belirtilen slayttaki tüm içeriği temizleyip verilen resim dosyasını ekler."""
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        pass

    @abstractmethod
    def close(self):
        pass