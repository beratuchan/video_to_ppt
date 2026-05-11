import queue
from typing import List, Optional
from core.slideshow_generator import SlideshowGenerator
from core.progress_notifier import ProgressNotifier
from core.background_task_executor import BackgroundTaskExecutor
from core.message_dispatcher import MessageDispatcher
from domain.i_generator_factory import IGeneratorFactory
from factories.generator_factory import ConcreteGeneratorFactory

class ConversionController:
    def __init__(self, msg_queue: queue.Queue, factory: Optional[IGeneratorFactory] = None):
        self.msg_queue = msg_queue
        self.dispatcher = MessageDispatcher(msg_queue)
        self.notifier = ProgressNotifier(msg_queue)
        self.executor = BackgroundTaskExecutor()
        self.factory = factory if factory else ConcreteGeneratorFactory()

    @property
    def is_running(self) -> bool:
        return self.executor.is_running

    def start(self, url_list: List[str]) -> None:
        if self.executor.is_running:
            self.dispatcher.error(None, "Zaten bir dönüştürme işlemi devam ediyor.")
            return
        if not url_list:
            self.dispatcher.error(None, "İşlenecek URL yok.")
            return
        self.executor.start(target=self._process_urls, args=(url_list,))

    def stop(self) -> None:
        self.executor.stop()

    def _process_urls(self, url_list: List[str]) -> None:
        success_count = 0
        errors = []
        total = len(url_list)

        for idx, url in enumerate(url_list):
            if self.executor.should_stop():
                self.dispatcher.progress(0, "İşlem kullanıcı tarafından durduruldu.")
                break

            percent = int((idx / total) * 100)
            self.dispatcher.progress(percent, f"({idx+1}/{total}) İşleniyor: {url}")

            try:
                generator = self.factory.create(url, observer=self.notifier)
                pptx_path = generator.generate_slideshow()
                self.dispatcher.result(url, pptx_path)
                self.dispatcher.open_editor(pptx_path, generator.temp_video_path)
                success_count += 1
            except Exception as e:
                self.dispatcher.error(url, str(e))
                errors.append((url, str(e)))

        self.executor.finish()

        if errors and not self.executor.should_stop():
            summary = f"{len(errors)} hata oluştu:\n" + "\n".join([f"{u}: {e}" for u, e in errors[:3]])
            self.dispatcher.messagebox("Uyarı", summary)

        self.dispatcher.finished(success_count, total)