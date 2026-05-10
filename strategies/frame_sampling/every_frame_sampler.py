from domain.i_frame_sampler import IFrameSampler
import numpy as np
from typing import Optional

class EveryFrameSampler(IFrameSampler):
    def should_sample(self, frame_index: int, frame: Optional[np.ndarray], current_time: float) -> bool:
        return True

    def reset(self) -> None:
        pass