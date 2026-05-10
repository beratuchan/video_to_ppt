"""
Görüntü işleme yardımcı fonksiyonları.
"""

import cv2
import numpy as np
from PIL import Image


def histogram_similarity(frame1: np.ndarray, frame2: np.ndarray) -> float:
    """
    İki frame'in renk histogramı benzerliğini hesaplar (0-1 arası, 1 en benzer).
    """
    hist1 = cv2.calcHist([frame1], [0, 1, 2], None, [16, 16, 16], [0, 256, 0, 256, 0, 256])
    hist2 = cv2.calcHist([frame2], [0, 1, 2], None, [16, 16, 16], [0, 256, 0, 256, 0, 256])
    hist1 = cv2.normalize(hist1, hist1).flatten()
    hist2 = cv2.normalize(hist2, hist2).flatten()
    return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)


def pixel_diff_ratio(frame1: np.ndarray, frame2: np.ndarray) -> float:
    """
    İki frame arasındaki ortalama piksel farkının normalize oranını döndürür (0-1).
    """
    diff = cv2.absdiff(frame1, frame2)
    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    return np.mean(gray_diff) / 255.0


def resize_image_to_max_width(image: np.ndarray, max_width: int) -> np.ndarray:
    """
    Görüntüyü genişliği max_width olacak şekilde yeniden boyutlandırır.
    Oran korunur. Eğer genişlik zaten max_width'ten küçükse aynen döner.
    """
    height, width = image.shape[:2]
    if width <= max_width:
        return image
    new_height = int(height * (max_width / width))
    # OpenCV BGR -> RGB -> PIL -> resize -> BGR
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb_image)
    pil_img = pil_img.resize((max_width, new_height), Image.Resampling.LANCZOS)
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def pil_to_cv2(pil_img: Image.Image) -> np.ndarray:
    rgb = np.array(pil_img.convert('RGB'))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)