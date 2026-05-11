import queue
from typing import Optional
from domain.i_progress_reporter import IProgressReporter
from domain.i_completion_observer import ICompletionObserver

class ProgressNotifier(IProgressReporter, ICompletionObserver):
    def __init__(self, target_queue: queue.Queue):
        self._queue = target_queue

    def on_progress(self, percent: float, message: str):
        self._queue.put(('progress', percent, message))

    def on_error(self, url: Optional[str], error_msg: str):
        self._queue.put(('error', url, error_msg))

    def on_finished(self, success_count: int, total_count: int):
        self._queue.put(('finished', success_count, total_count))