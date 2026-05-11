import time
from typing import Optional
from domain.i_video_stream import IVideoStream
from domain.i_scene_detector import ISceneDetector
from domain.i_slide_builder import ISlideBuilder
from domain.i_progress_reporter import IProgressReporter
from domain.i_frame_sampler import IFrameSampler
from strategies.frame_sampling.every_frame_sampler import EveryFrameSampler
from config.settings import MIN_SLIDE_INTERVAL_SEC

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
        downloader=None
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

    def generate_slideshow(self) -> str:
        video_info = self.video_stream.get_info()
        duration = video_info.get('duration_seconds', 0)
        title = video_info.get('title', 'Video')
        fps = video_info.get('fps', 1)

        self.frame_sampler.reset()
        self._notify(0, "Video işleniyor...")

        if self.add_first_slide_with_link:
            self.slide_builder.create_new_slide()
            video_url = getattr(self.video_stream, 'url', 'Bilinmiyor')
            self.slide_builder.add_text(f"Video URL: {video_url}", font_size=18, bold=False)
            self.slide_builder.add_timestamp(0, title)

        prev_frame = None
        frame_index = 0
        scene_count = 0
        last_slide_time = -self.min_slide_interval
        start_time = time.time()

        while True:
            frame = self.video_stream.get_frame()
            if frame is None:
                break

            current_sec = frame_index / fps
            if self.frame_sampler.should_sample(frame_index, frame, current_sec):
                if self.scene_detector.is_scene_change(prev_frame, frame):
                    if (current_sec - last_slide_time) >= self.min_slide_interval:
                        self.slide_builder.create_new_slide()
                        self.slide_builder.add_image(frame)
                        self.slide_builder.add_timestamp(current_sec, title)
                        scene_count += 1
                        last_slide_time = current_sec
                prev_frame = frame

            frame_index += 1
            if frame_index % 30 == 0 and duration > 0:
                percent = min(100.0, (frame_index / (duration * fps)) * 100.0)
                self._notify(percent, f"İşleniyor... ({scene_count} slayt)")

        elapsed = time.time() - start_time
        self._notify(100, f"Tamamlandı! {scene_count} slayt, {elapsed:.1f} saniye")
        return self.slide_builder.build()

    def _notify(self, percent: float, message: str) -> None:
        if self.observer:
            self.observer.on_progress(percent, message)