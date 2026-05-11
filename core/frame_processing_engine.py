# core/frame_processing_engine.py
import time
from typing import Optional, Tuple
import numpy as np
from domain.i_video_stream import IVideoStream
from domain.i_scene_detector import ISceneDetector
from domain.i_slide_builder import ISlideBuilder
from domain.i_frame_sampler import IFrameSampler
from strategies.frame_sampling.every_frame_sampler import EveryFrameSampler
from config.settings import MIN_SLIDE_INTERVAL_SEC, PROGRESS_UPDATE_INTERVAL_FRAMES

class FrameProcessingEngine:
    """
    Frame işleme döngüsünü yönetir.
    Sorumluluklar:
    - Frame'leri sırayla okumak (IVideoStream üzerinden)
    - Frame sampler'a danışarak hangi frame'lerin işleneceğine karar vermek
    - Scene detector ile sahne değişimlerini tespit etmek
    - Yeni slayt oluşturulması gerektiğinde slide_builder'ı çağırmak
    - İlerleme yüzdesini dışarıya bildirmek (callback ile)
    """
    def __init__(
        self,
        video_stream: IVideoStream,
        scene_detector: ISceneDetector,
        slide_builder: ISlideBuilder,
        frame_sampler: Optional[IFrameSampler] = None,
        min_slide_interval: float = MIN_SLIDE_INTERVAL_SEC,
        progress_callback=None  # def callback(percent: float, message: str, scene_count: int)
    ):
        self.video_stream = video_stream
        self.scene_detector = scene_detector
        self.slide_builder = slide_builder
        self.frame_sampler = frame_sampler if frame_sampler else EveryFrameSampler()
        self.min_slide_interval = min_slide_interval
        self.progress_callback = progress_callback

    def process(self, duration: float, fps: float, title: str) -> Tuple[int, float]:
        """
        Frame işleme döngüsünü çalıştırır.
        Returns: (scene_count, elapsed_seconds)
        """
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
            if frame_index % PROGRESS_UPDATE_INTERVAL_FRAMES == 0 and duration > 0:
                percent = min(100.0, (frame_index / (duration * fps)) * 100.0)
                if self.progress_callback:
                    self.progress_callback(percent, f"İşleniyor... ({scene_count} slayt)", scene_count)

        elapsed = time.time() - start_time
        return scene_count, elapsed