from typing import Optional, Union
import os
from core.slideshow_generator import SlideshowGenerator
from domain.i_generator_factory import IGeneratorFactory
from domain.i_progress_reporter import IProgressReporter
from infrastructure.video_downloader import VideoDownloader
from infrastructure.local_video_stream import LocalVideoStream
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
        
        # Başlık önceden belirlenebilir
        title = None
        
        # Yerel dosya kontrolü
        if os.path.exists(source_str) and os.path.isfile(source_str):
            video_path = source_str
            title = os.path.splitext(os.path.basename(video_path))[0]
            downloader = None
        else:
            # URL ise indir
            downloader = VideoDownloader()
            try:
                # Observer varsa progress callback'ini downloader'a ilet
                if observer:
                    def progress_callback(percent, message):
                        if percent is not None:
                            observer.on_progress(min(100.0, max(0.0, percent)), message)
                        else:
                            observer.on_progress(-1, message)
                else:
                    progress_callback = None

                # Kalıcı kayıt mı?
                permanent_path = None
                if keep_video:
                    # Başlığı geçici olarak URL'den çıkar (daha sonra kesin başlık atanacak)
                    temp_title = self._extract_title_from_url(source_str)
                    safe_title = "".join(c for c in temp_title if c.isalnum() or c in "._- ").strip()
                    if not safe_title:
                        safe_title = "video"
                    video_folder = SettingsManager.get_video_storage_folder()
                    if video_folder:
                        os.makedirs(video_folder, exist_ok=True)
                        permanent_path = os.path.join(video_folder, f"{safe_title}.mp4")
                
                video_path = downloader.download(source_str, progress_callback=progress_callback, permanent_path=permanent_path)
            except Exception as e:
                raise RuntimeError(f"Video indirilemedi: {e}") from e
            
            # URL'den başlık çıkar (eğer daha önce atanmadıysa)
            if title is None:
                title = self._extract_title_from_url(source_str)
        
        # Video akışı oluştur
        video_stream = LocalVideoStream(video_path, target_fps=DEFAULT_FPS, target_width=DEFAULT_TARGET_WIDTH)
        
        scene_detector = RobustDiffStrategy(
            hist_threshold=DEFAULT_HIST_THRESHOLD,
            pixel_threshold=DEFAULT_PIXEL_THRESHOLD,
        )
        
        output_path = os.path.join(output_dir, f"{title}.pptx")
        slide_builder = PptxSlideBuilder(output_path, video_title=title, video_url=source_str)
        
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
            downloader=downloader,
            video_url=source_str
        )
        return generator

    def _extract_title_from_url(self, url: str) -> str:
        """URL'den okunabilir bir başlık çıkarır."""
        if 'v=' in url:
            return url.split('v=')[-1][:20]
        # Diğer durumlar için basit temizlik
        return "video"