from typing import List
from PIL import Image
import tempfile
import os

class GifCreator:
    @staticmethod
    def create_gif_from_images(images: List[Image.Image], duration_per_frame: float = 0.5) -> str:
        """
        Verilen PIL Image listesinden bir GIF dosyası oluşturur ve yolunu döndürür.
        """
        if len(images) < 2:
            raise ValueError("En az iki görüntü gerekir")
        
        # Tüm görüntüleri RGB moduna çevir
        rgb_images = [img.convert('RGB') for img in images]
        
        # Geçici GIF dosyası oluştur
        fd, gif_path = tempfile.mkstemp(suffix='.gif')
        os.close(fd)
        
        duration_ms = int(duration_per_frame * 1000)
        rgb_images[0].save(
            gif_path,
            save_all=True,
            append_images=rgb_images[1:],
            duration=duration_ms,
            loop=0,
            disposal=2
        )
        return gif_path