from abc import ABC, abstractmethod
from typing import Optional

class ICompletionObserver(ABC):
    @abstractmethod
    def on_error(self, url: Optional[str], error_msg: str) -> None:
        pass

    @abstractmethod
    def on_finished(self, success_count: int, total_count: int) -> None:
        pass