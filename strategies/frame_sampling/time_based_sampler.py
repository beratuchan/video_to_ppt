from domain.i_frame_sampler import IFrameSampler
import numpy as np
from typing import Optional

class TimeBasedSampler(IFrameSampler):
    def __init__(self, interval_sec: float = 1.0):
        self.interval = interval_sec
        self.last_sampled_time = -interval_sec   # başlangıçta ilk frame'i alabilmek için

    def should_sample(self, frame_index: int, frame: Optional[np.ndarray], current_time: float) -> bool:
        if current_time - self.last_sampled_time >= self.interval:
            self.last_sampled_time = current_time
            return True
        return False

    def reset(self) -> None:
        self.last_sampled_time = -self.interval