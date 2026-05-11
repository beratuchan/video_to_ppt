import tempfile
import os
from typing import List
from PIL import Image
from domain.i_pptx_reader import IPPTXReader
from domain.i_pptx_writer import IPPTXWriter
from config.settings import DEFAULT_GIF_DURATION_PER_FRAME_SEC, DEFAULT_GIF_LOOP

class GifAnimator:
    @staticmethod
    def replace_slides_with_gif(
        reader: IPPTXReader,
        writer: IPPTXWriter,
        selected_indices: List[int],
        duration_per_frame: float = DEFAULT_GIF_DURATION_PER_FRAME_SEC
    ) -> None:
        if len(selected_indices) < 2:
            raise ValueError("En az iki slayt seçmelisiniz")

        images = []
        for idx in selected_indices:
            imgs = reader.get_slide_images(idx)
            if imgs:
                img = imgs[0].convert('RGB')
                images.append(img)
        if not images:
            raise ValueError("Seçilen slaytlarda hiç resim bulunamadı")

        fd, gif_path = tempfile.mkstemp(suffix='.gif')
        os.close(fd)
        try:
            duration_ms = int(duration_per_frame * 1000)
            images[0].save(
                gif_path,
                save_all=True,
                append_images=images[1:],
                duration=duration_ms,
                loop=DEFAULT_GIF_LOOP,
                disposal=2  # disposal=2: arka planı temizle (her frame'de önceki silinir)
            )

            min_idx = min(selected_indices)
            other_indices = [idx for idx in selected_indices if idx != min_idx]
            if other_indices:
                writer.delete_slides(other_indices)

            writer.replace_slide_with_image(min_idx, gif_path)
            writer.save(writer.source_path)
            reader.update_from_writer(writer)
        finally:
            if os.path.exists(gif_path):
                os.unlink(gif_path)