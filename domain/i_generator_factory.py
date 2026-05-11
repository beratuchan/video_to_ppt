from abc import ABC, abstractmethod
from typing import Optional
from core.slideshow_generator import SlideshowGenerator
from domain.i_progress_reporter import IProgressReporter

class IGeneratorFactory(ABC):
    @abstractmethod
    def create(
        self,
        url: str,
        output_dir: str = ".",
        observer: Optional[IProgressReporter] = None
    ) -> SlideshowGenerator:
        pass