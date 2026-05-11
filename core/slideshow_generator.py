# core/slideshow_generator.py
import time
from typing import Optional
from domain.i_video_stream import IVideoStream
from domain.i_scene_detector import ISceneDetector
from domain.i_slide_builder import ISlideBuilder
from domain.i_progress_reporter import IProgressReporter
from domain.i_frame_sampler import IFrameSampler
from strategies.frame_sampling.every_frame_sampler import EveryFrameSampler
from config.settings import MIN_SLIDE_INTERVAL_SEC, PROGRESS_UPDATE_INTERVAL_FRAMES
from core.frame_processing_engine import FrameProcessingEngine   # YENİ

class SlideshowGenerator:
    def __init__(
        self,
        video_stream: IVideoStream,
        scene_detector: ISceneDetector,
        slide_builder: ISlideBuilder,
        observer: Optional[IProgressReporter] = None,
        min_slide_interval: float = MIN_SLIDE_INTERVAL_SEC,
        frame_sampler: Optional[IFrameSampler] = None,
        frame_queue_size: int = 30,
        add_first_slide_with_link: bool = False,
        temp_video_path: str = None,
        downloader=None,
        video_url: Optional[str] = None
    ):
        self.video_stream = video_stream
        self.scene_detector = scene_detector
        self.slide_builder = slide_builder
        self.observer = observer
        self.min_slide_interval = min_slide_interval
        self.frame_sampler = frame_sampler if frame_sampler else EveryFrameSampler()
        self.add_first_slide_with_link = add_first_slide_with_link
        self.temp_video_path = temp_video_path
        self.downloader = downloader
        self.video_url = video_url

    def generate_slideshow(self) -> str:
        try:
            video_info = self.video_stream.get_info()
            duration = video_info.get('duration_seconds', 0)
            title = video_info.get('title', 'Video')
            fps = video_info.get('fps', 1)

            self.frame_sampler.reset()
            self._notify_progress(0, "Video işleniyor...")

            if self.add_first_slide_with_link:
                self._add_first_slide(title)

            # YENİ: FrameProcessingEngine kullan
            engine = FrameProcessingEngine(
                video_stream=self.video_stream,
                scene_detector=self.scene_detector,
                slide_builder=self.slide_builder,
                frame_sampler=self.frame_sampler,
                min_slide_interval=self.min_slide_interval,
                progress_callback=self._progress_callback
            )
            scene_count, elapsed = engine.process(duration, fps, title)

            self._notify_progress(100, f"Tamamlandı! {scene_count} slayt, {elapsed:.1f} saniye")
            return self.slide_builder.build()
        except Exception as e:
            error_msg = str(e)
            self._notify_error(error_msg)
            raise

    def _add_first_slide(self, title: str) -> None:
        self.slide_builder.create_new_slide()
        url = self.video_url if self.video_url else "Bilinmiyor"
        self.slide_builder.add_text(f"Video URL: {url}", font_size=18, bold=False)
        self.slide_builder.add_timestamp(0, title)

    def _progress_callback(self, percent: float, message: str, scene_count: int) -> None:
        """FrameProcessingEngine'den gelen ilerleme bildirimlerini observer'a iletir."""
        self._notify_progress(percent, message)

    def _notify_progress(self, percent: float, message: str) -> None:
        if self.observer:
            self.observer.on_progress(percent, message)

    def _notify_error(self, error_msg: str) -> None:
        if self.observer:
            self.observer.on_error(self.video_url, error_msg)