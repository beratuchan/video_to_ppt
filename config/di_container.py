from infrastructure.video_downloader import VideoDownloader
from infrastructure.local_video_stream import LocalVideoStream
from infrastructure.pptx_slide_builder import PptxSlideBuilder
from core.slideshow_generator import SlideshowGenerator
from domain.i_progress_reporter import IProgressReporter
from strategies.frame_sampling.time_based_sampler import TimeBasedSampler
from strategies.scene_detection.robust_diff_strategy import RobustDiffStrategy
from config.settings import *
import os
from typing import Optional

def create_generator_for_url(
    url: str,
    output_dir: str = ".",
    observer: Optional[IProgressReporter] = None
) -> SlideshowGenerator:
    downloader = VideoDownloader()
    try:
        video_path = downloader.download(url)
    except Exception as e:
        # Not: observer IProgressReporter olduğu için on_error metodu yok.
        # Hata bildirimi yapmak için farklı bir mekanizma gerekir.
        # Bu, ilerleyen aşamalarda düzeltilecektir.
        raise

    title = url.split('v=')[-1][:20] if 'v=' in url else 'video'
    video_stream = LocalVideoStream(video_path, target_fps=DEFAULT_FPS, target_width=DEFAULT_TARGET_WIDTH)
    scene_detector = RobustDiffStrategy(
        hist_threshold=DEFAULT_HIST_THRESHOLD,
        pixel_threshold=DEFAULT_PIXEL_THRESHOLD,
    )
    output_path = os.path.join(output_dir, f"{title}.pptx")
    slide_builder = PptxSlideBuilder(output_path, video_title=title, video_url=url)
    frame_sampler = TimeBasedSampler(interval_sec=1.0)
    
    generator = SlideshowGenerator(
        video_stream,
        scene_detector,
        slide_builder,
        observer=observer,
        min_slide_interval=MIN_SLIDE_INTERVAL_SEC,
        frame_sampler=frame_sampler,
        frame_queue_size=30,
        add_first_slide_with_link=True,
        temp_video_path=video_path,
        downloader=downloader
    )
    return generator