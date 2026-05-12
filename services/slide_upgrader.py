from typing import List, Optional, Callable
from PIL import Image
from domain.i_pptx_reader import IPPTXReader
from domain.i_pptx_writer import IPPTXWriter
from domain.i_frame_extractor import IFrameExtractor
import cv2
from utils.time_utils import extract_timestamp_seconds   # YENİ

class SlideUpgrader:
    @staticmethod
    def upgrade_slides(
        reader: IPPTXReader,
        writer: IPPTXWriter,
        selected_indices: List[int],
        extractor: IFrameExtractor,
        target_width: int = 1920,
        progress_callback: Optional[Callable[[int, int, int], None]] = None
    ) -> None:
        if not selected_indices:
            raise ValueError("Yükseltilecek slayt seçilmedi")
        total = len(selected_indices)
        for i, idx in enumerate(selected_indices):
            if progress_callback:
                progress_callback(i, total, idx)
            slide_text = reader.get_slide_text(idx)
            seconds = extract_timestamp_seconds(slide_text)   # DEĞİŞTİ
            if seconds is None:
                continue
            high_res_bgr = extractor.extract_frame(seconds, target_width=target_width)
            if high_res_bgr is None:
                continue
            high_res_rgb = cv2.cvtColor(high_res_bgr, cv2.COLOR_BGR2RGB)
            high_res_pil = Image.fromarray(high_res_rgb)
            writer.replace_slide_image(idx, high_res_pil)
        reader.update_from_writer(writer)

