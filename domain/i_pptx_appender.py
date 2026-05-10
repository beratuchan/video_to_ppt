from abc import ABC, abstractmethod
from PIL import Image

class IPPTXAppender(ABC):
    @abstractmethod
    def append_image_as_slide(self, image: Image.Image, title: str = "Grid Slayt") -> str:
        """Birleştirilmiş görseli yeni bir PPTX slaytı olarak ekler, dosya yolunu döndürür."""
        pass