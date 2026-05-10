from abc import ABC, abstractmethod
from typing import List, Optional
from PIL import Image

class IPPTXReader(ABC):
    @abstractmethod
    def get_slide_count(self) -> int:
        pass

    @abstractmethod
    def get_slide_images(self, slide_index: int) -> List[Image.Image]:
        pass

    @abstractmethod
    def get_slide_text(self, slide_index: int) -> str:
        """Slayttaki tüm metinleri döndürür (altbilgi dahil)."""
        pass

    @abstractmethod
    def get_first_image_thumbnail(self, slide_index: int, max_size: int = 100) -> Optional[Image.Image]:
        pass

    @abstractmethod
    def update_from_writer(self, writer) -> None:
        pass

    @abstractmethod
    def close(self):
        pass