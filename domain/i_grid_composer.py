from abc import ABC, abstractmethod
from typing import List
from PIL import Image

class IGridComposer(ABC):
    @abstractmethod
    def compose(self, images: List[Image.Image], rows: int, cols: int, margin: int = 10) -> Image.Image:
        pass