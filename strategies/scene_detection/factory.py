
from domain.i_scene_detector import ISceneDetector
from .abs_diff_strategy import AbsDiffStrategy

class SceneDetectorFactory:
    @staticmethod
    def create(strategy_name: str = "absdiff", threshold: float = 0.3) -> ISceneDetector:
        if strategy_name == "absdiff":
            return AbsDiffStrategy(threshold)
        # İleride yeni stratejiler eklenebilir
        raise ValueError(f"Bilinmeyen strateji: {strategy_name}")