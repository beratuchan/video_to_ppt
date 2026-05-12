from typing import Optional, Union
import os
from core.slideshow_generator import SlideshowGenerator
from domain.i_generator_factory import IGeneratorFactory
from domain.i_progress_reporter import IProgressReporter
from infrastructure.video_downloader import VideoDownloader
from infrastructure.local_video_stream import LocalVideoStream
from infrastructure.yt_dlp_stream import YtDlpVideoStream   # YENİ
from infrastructure.pptx_slide_builder import PptxSlideBuilder
from strategies.frame_sampling.time_based_sampler import TimeBasedSampler
from strategies.scene_detection.robust_diff_strategy import RobustDiffStrategy
from config.settings import DEFAULT_FPS, DEFAULT_TARGET_WIDTH, MIN_SLIDE_INTERVAL_SEC, DEFAULT_HIST_THRESHOLD, DEFAULT_PIXEL_THRESHOLD
from utils.settings_manager import SettingsManager

class ConcreteGeneratorFactory(IGeneratorFactory):
    def create(
        self,
        url_or_path: Union[str, os.PathLike],
        output_dir: str = ".",
        observer: Optional[IProgressReporter] = None,
        keep_video: bool = False
    ) -> SlideshowGenerator:
        source_str = str(url_or_path)
        title = None
        downloader = None
        temp_video_path = None
        video_stream = None

        # Yerel dosya mı?
        if os.path.exists(source_str) and os.path.isfile(source_str):
            video_path = source_str
            title = os.path.splitext(os.path.basename(video_path))[0]
            video_stream = LocalVideoStream(video_path, target_fps=DEFAULT_FPS, target_width=DEFAULT_TARGET_WIDTH)
            temp_video_path = video_path
        else:
            # URL
            if keep_video:
                # Videoyu kalıcı olarak indir
                downloader = VideoDownloader()
                try:
                    if observer:
                        def progress_callback(percent, message):
                            if percent is not None:
                                observer.on_progress(min(100.0, max(0.0, percent)), message)
                            else:
                                observer.on_progress(-1, message)
                    else:
                        progress_callback = None

                    permanent_path = None
                    temp_title = self._extract_title_from_url(source_str)
                    safe_title = "".join(c for c in temp_title if c.isalnum() or c in "._- ").strip()
                    if not safe_title:
                        safe_title = "video"
                    video_folder = SettingsManager.get_video_storage_folder()
                    if video_folder:
                        os.makedirs(video_folder, exist_ok=True)
                        permanent_path = os.path.join(video_folder, f"{safe_title}.mp4")

                    video_path = downloader.download(source_str, progress_callback=progress_callback, permanent_path=permanent_path)
                    title = safe_title
                except Exception as e:
                    raise RuntimeError(f"Video indirilemedi: {e}") from e
                video_stream = LocalVideoStream(video_path, target_fps=DEFAULT_FPS, target_width=DEFAULT_TARGET_WIDTH)
                temp_video_path = video_path
            else:
                # İndirmeden doğrudan akış - YtDlpVideoStream
                try:
                    video_stream = YtDlpVideoStream(source_str, target_fps=DEFAULT_FPS, target_width=DEFAULT_TARGET_WIDTH)
                    # Başlığı stream'den al
                    info = video_stream.get_info()
                    title = info.get('title', self._extract_title_from_url(source_str))
                    temp_video_path = None
                    downloader = None
                except Exception as e:
                    raise RuntimeError(f"Video akışı başlatılamadı: {e}") from e

        # Eğer title hala None ise (yerel dosyadan gelmediyse ve keep_video=False akıştan alınmışsa)
        if title is None and video_stream:
            info = video_stream.get_info()
            title = info.get('title', 'Video')

        # Video akışı oluşturulmuş olmalı
        if video_stream is None:
            raise RuntimeError("Video akışı oluşturulamadı")

        scene_detector = RobustDiffStrategy(
            hist_threshold=DEFAULT_HIST_THRESHOLD,
            pixel_threshold=DEFAULT_PIXEL_THRESHOLD,
        )
        output_path = os.path.join(output_dir, f"{title}.pptx")
        slide_builder = PptxSlideBuilder(output_path, video_title=title, video_url=source_str)

        frame_sampler = TimeBasedSampler(interval_sec=1.0)

        generator = SlideshowGenerator(
            video_stream=video_stream,
            scene_detector=scene_detector,
            slide_builder=slide_builder,
            observer=observer,
            min_slide_interval=MIN_SLIDE_INTERVAL_SEC,
            frame_sampler=frame_sampler,
            frame_queue_size=30,
            add_first_slide_with_link=True,
            temp_video_path=temp_video_path,
            downloader=downloader,
            video_url=source_str
        )
        return generator

    def _extract_title_from_url(self, url: str) -> str:
        if 'v=' in url:
            return url.split('v=')[-1][:20]
        return "video"