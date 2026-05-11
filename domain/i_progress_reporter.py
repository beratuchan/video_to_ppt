from abc import ABC, abstractmethod

class IProgressReporter(ABC):
    @abstractmethod
    def on_progress(self, percent: float, message: str) -> None:
        pass