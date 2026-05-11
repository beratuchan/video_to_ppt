from abc import ABC, abstractmethod
from typing import Optional

class IProgressReporter(ABC):
    @abstractmethod
    def on_progress(self, percent: float, message: str) -> None:
        pass

    @abstractmethod
    def on_error(self, url: Optional[str], error_msg: str) -> None:
        """Hata durumunda çağrılır. url None olabilir."""
        pass