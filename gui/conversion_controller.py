import queue
import threading
from typing import List, Optional
from core.slideshow_generator import SlideshowGenerator
from core.progress_notifier import ProgressNotifier
from config.di_container import create_generator_for_url

class ConversionController:
    def __init__(self, msg_queue: queue.Queue):
        self.msg_queue = msg_queue
        self.notifier = ProgressNotifier(msg_queue)
        self._is_running = False
        self._stop_requested = False
        self._current_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._is_running

    def start(self, url_list: List[str]) -> None:
        with self._lock:
            if self._is_running:
                self.msg_queue.put(('error', None, "Zaten bir dönüştürme işlemi devam ediyor."))
                return
            if not url_list:
                self.msg_queue.put(('error', None, "İşlenecek URL yok."))
                return
            self._is_running = True
            self._stop_requested = False

        self._current_thread = threading.Thread(
            target=self._process_urls,
            args=(url_list,),
            daemon=True
        )
        self._current_thread.start()

    def stop(self) -> None:
        with self._lock:
            self._stop_requested = True

    def _process_urls(self, url_list: List[str]) -> None:
        success_count = 0
        errors = []
        total = len(url_list)

        for idx, url in enumerate(url_list):
            with self._lock:
                if self._stop_requested:
                    self.msg_queue.put(('progress', 0, "İşlem kullanıcı tarafından durduruldu."))
                    break

            percent = int((idx / total) * 100)
            self.msg_queue.put(('progress', percent, f"({idx+1}/{total}) İşleniyor: {url}"))

            try:
                generator = create_generator_for_url(url, observer=self.notifier)
                pptx_path = generator.generate_slideshow()
                self.msg_queue.put(('result', url, pptx_path))
                self.msg_queue.put(('open_ppt_editor', pptx_path, generator.temp_video_path))
                success_count += 1
            except Exception as e:
                error_msg = str(e)
                self.msg_queue.put(('error', url, error_msg))
                errors.append((url, error_msg))

        with self._lock:
            self._is_running = False

        if errors and not self._stop_requested:
            summary = f"{len(errors)} hata oluştu:\n" + "\n".join([f"{u}: {e}" for u, e in errors[:3]])
            self.msg_queue.put(('messagebox', "Uyarı", summary))

        self.msg_queue.put(('finished', success_count, total))