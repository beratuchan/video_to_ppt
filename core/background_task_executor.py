import threading
from typing import Callable, Optional

class BackgroundTaskExecutor:
    def __init__(self):
        self._is_running = False
        self._stop_requested = False
        self._current_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._is_running

    def start(self, target: Callable, args: tuple = ()):
        with self._lock:
            if self._is_running:
                raise RuntimeError("Zaten bir görev çalışıyor")
            self._is_running = True
            self._stop_requested = False
        self._current_thread = threading.Thread(target=target, args=args, daemon=True)
        self._current_thread.start()

    def stop(self):
        with self._lock:
            self._stop_requested = True

    def should_stop(self) -> bool:
        with self._lock:
            return self._stop_requested

    def finish(self):
        with self._lock:
            self._is_running = False