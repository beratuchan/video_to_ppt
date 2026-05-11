from abc import ABC, abstractmethod
from domain.i_slide_builder import ISlideBuilder
from domain.i_video_stream import IVideoStream

class ISlideInitializer(ABC):
    @abstractmethod
    def init_first_slide(self, builder: ISlideBuilder, video_stream: IVideoStream, title: str) -> None:
        pass