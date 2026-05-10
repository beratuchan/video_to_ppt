# Domain katmanı soyutlamaları
from .i_video_stream import IVideoStream
from .i_scene_detector import ISceneDetector
from .i_slide_builder import ISlideBuilder
from .i_progress_observer import IProgressObserver
from .i_subtitle_provider import ISubtitleProvider

__all__ = [
    "IVideoStream",
    "ISceneDetector",
    "ISlideBuilder",
    "IProgressObserver",
    "ISubtitleProvider",
]