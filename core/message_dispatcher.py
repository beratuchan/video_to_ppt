import queue
from typing import Any

class MessageDispatcher:
    def __init__(self, msg_queue: queue.Queue):
        self._queue = msg_queue

    def progress(self, percent: float, message: str):
        self._queue.put(('progress', percent, message))

    def error(self, url: str, error_msg: str):
        self._queue.put(('error', url, error_msg))

    def result(self, url: str, pptx_path: str):
        self._queue.put(('result', url, pptx_path))

    def open_editor(self, pptx_path: str, video_path: str):
        self._queue.put(('open_ppt_editor', pptx_path, video_path))

    def messagebox(self, title: str, text: str):
        self._queue.put(('messagebox', title, text))

    def finished(self, success_count: int, total_count: int):
        self._queue.put(('finished', success_count, total_count))