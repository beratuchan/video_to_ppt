import numpy as np
from typing import Optional
from domain.i_scene_detector import ISceneDetector
from config.settings import DEFAULT_HIST_THRESHOLD, DEFAULT_PIXEL_THRESHOLD, DEFAULT_USE_HISTOGRAM
from utils.image_utils import histogram_similarity, pixel_diff_ratio


class RobustDiffStrategy(ISceneDetector):
    def __init__(
        self,
        hist_threshold: float = DEFAULT_HIST_THRESHOLD,
        pixel_threshold: float = DEFAULT_PIXEL_THRESHOLD,
        use_histogram: bool = DEFAULT_USE_HISTOGRAM
    ):
        self.hist_threshold = hist_threshold
        self.pixel_threshold = pixel_threshold
        self.use_histogram = use_histogram

    def is_scene_change(self, prev_frame: Optional[np.ndarray], curr_frame: np.ndarray) -> bool:
        if prev_frame is None:
            return True
        if self.use_histogram:
            hist_sim = histogram_similarity(prev_frame, curr_frame)
            if hist_sim > self.hist_threshold:
                return False
        diff_ratio = pixel_diff_ratio(prev_frame, curr_frame)
        return diff_ratio > self.pixel_threshold

    def set_threshold(self, value: float) -> None:
        self.pixel_threshold = max(0.0, min(1.0, value))