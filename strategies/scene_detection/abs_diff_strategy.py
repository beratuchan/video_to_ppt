import numpy as np
from typing import Optional
from domain.i_scene_detector import ISceneDetector
from utils.image_utils import pixel_diff_ratio


class AbsDiffStrategy(ISceneDetector):
    def __init__(self, threshold: float = 0.3):
        self.threshold = threshold

    def is_scene_change(self, prev_frame: Optional[np.ndarray], curr_frame: np.ndarray) -> bool:
        if prev_frame is None:
            return True
        if prev_frame.shape != curr_frame.shape:
            return True
        if np.array_equal(prev_frame, curr_frame):
            return False
        mean_diff = pixel_diff_ratio(prev_frame, curr_frame)
        return mean_diff > self.threshold

    def set_threshold(self, value: float) -> None:
        self.threshold = max(0.0, min(1.0, value))