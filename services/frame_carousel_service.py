# services/frame_carousel_service.py

import cv2
import numpy as np
from typing import List, Optional, Callable

class FrameCarouselService:
    """
    Bir video dosyasından belirli bir zaman aralığındaki kareleri,
    belirli bir FPS veya maksimum kare sayısına göre örnekleyerek alır.
    Zaman aralığı doğrulaması ve otomatik düzeltme içerir.
    """

    def __init__(
        self,
        video_path: str,
        start_sec: float,
        end_sec: float,
        target_fps: float = 10.0,
        max_frames: int = 200,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ):
        """
        Args:
            video_path: Video dosyasının yolu
            start_sec: Başlangıç zamanı (saniye)
            end_sec: Bitiş zamanı (saniye)
            target_fps: Hedef kare hızı (örnekleme sıklığı) - şu an kullanılmıyor, max_frames tercih ediliyor
            max_frames: Maksimum kare sayısı
            progress_callback: İlerleme bildirimi için callback (percent, message)
        """
        # ========== ZAMAN ARALIĞI DOĞRULAMA VE DÜZELTME ==========
        # NaN veya None kontrolü
        if start_sec is None or np.isnan(start_sec):
            start_sec = 0.0
        if end_sec is None or np.isnan(end_sec):
            end_sec = start_sec + 1.0

        # Negatif değer kontrolü
        if start_sec < 0:
            start_sec = 0.0
        if end_sec < 0:
            end_sec = start_sec + 1.0

        # Ters sıra kontrolü
        if end_sec <= start_sec:
            print(f"FrameCarouselService: Zaman aralığı ters, takas ediliyor: {start_sec:.3f} - {end_sec:.3f}")
            start_sec, end_sec = end_sec, start_sec

        # Çok kısa aralık kontrolü (en az 0.3 saniye)
        if end_sec - start_sec < 0.3:
            old_end = end_sec
            end_sec = start_sec + 0.5
            print(f"FrameCarouselService: Aralık çok kısa ({old_end - start_sec:.3f}s), 0.5s'e genişletildi: {start_sec:.3f} - {end_sec:.3f}")

        # Sonsuz veya çok büyük end_sec kontrolü
        if np.isinf(end_sec) or end_sec > 1e9:
            end_sec = start_sec + 0.5
            print(f"FrameCarouselService: end_sec sonsuz/çok büyük, varsayılan aralık ayarlandı: {start_sec:.3f} - {end_sec:.3f}")

        self.video_path = video_path
        self.start_sec = start_sec
        self.end_sec = end_sec
        self.target_fps = target_fps
        self.max_frames = max_frames
        self.progress_callback = progress_callback

        self.frames: List[np.ndarray] = []
        self.current_index = 0
        self._load_frames()

    def _load_frames(self):
        """Video dosyasından belirtilen aralıktaki kareleri yükler."""
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise IOError(f"Video açılamadı: {self.video_path}")

        # Video bilgilerini al
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30  # varsayılan
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0

        # Frame indekslerini hesapla
        start_frame = int(self.start_sec * fps)
        if np.isinf(self.end_sec) or self.end_sec > duration:
            end_frame = total_frames
        else:
            end_frame = int(self.end_sec * fps)

        print(f"FrameCarouselService: Video FPS={fps}, toplam frame={total_frames}, süre={duration:.2f}s")
        print(f"FrameCarouselService: İstenen aralık: {self.start_sec:.3f}s - {self.end_sec:.3f}s -> frame {start_frame} - {end_frame}")

        # Geçerlilik kontrolü ve düzeltme
        if end_frame <= start_frame:
            end_frame = min(start_frame + int(fps * 0.5), total_frames)
            if end_frame <= start_frame:
                end_frame = start_frame + 1
            print(f"FrameCarouselService: end_frame <= start_frame, düzeltildi: start_frame={start_frame}, end_frame={end_frame}")

        if start_frame >= total_frames:
            start_frame = max(0, total_frames - int(fps * 0.5))
            end_frame = total_frames
            print(f"FrameCarouselService: start_frame >= total_frames, düzeltildi: start_frame={start_frame}, end_frame={end_frame}")

        # Aralık geçerli değilse hata fırlat
        if start_frame >= total_frames or end_frame <= start_frame:
            cap.release()
            raise RuntimeError(
                f"Geçersiz frame aralığı: start_frame={start_frame}, end_frame={end_frame}, total_frames={total_frames}"
            )

        total_frames_in_range = end_frame - start_frame
        target_frame_count = min(total_frames_in_range, self.max_frames)
        target_frame_count = max(1, target_frame_count)
        step = max(1, total_frames_in_range // target_frame_count)

        print(f"FrameCarouselService: Aralıkta {total_frames_in_range} frame var, adım={step}, hedef kare sayısı={target_frame_count}")

        if self.progress_callback:
            self.progress_callback(0, f"Kareler yükleniyor (hedef: {target_frame_count})...")

        # Frame'leri topla
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        frames_collected = []
        frame_idx = start_frame
        last_reported = 0

        while frame_idx < end_frame and len(frames_collected) < self.max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            if (frame_idx - start_frame) % step == 0:
                frames_collected.append(frame.copy())
            frame_idx += 1

            # İlerleme raporu (her %10)
            percent = min(100, int((frame_idx - start_frame) / total_frames_in_range * 100)) if total_frames_in_range > 0 else 0
            if percent - last_reported >= 10 and self.progress_callback:
                self.progress_callback(percent, f"Kareler yükleniyor... (%{percent})")
                last_reported = percent

        cap.release()

        if not frames_collected:
            raise RuntimeError(
                f"Hiç kare yakalanamadı!\n"
                f"Video: {self.video_path}\n"
                f"Aralık: {self.start_sec:.3f}s - {self.end_sec:.3f}s\n"
                f"Frame aralığı: {start_frame} - {end_frame}\n"
                f"Video FPS: {fps}, toplam frame: {total_frames}"
            )

        self.frames = frames_collected
        self.current_index = 0
        if self.progress_callback:
            self.progress_callback(100, f"{len(self.frames)} kare yüklendi.")
        print(f"FrameCarouselService: {len(self.frames)} kare başarıyla yüklendi.")

    def get_frame_count(self) -> int:
        """Toplam kare sayısını döndürür."""
        return len(self.frames)

    def get_current_frame(self) -> Optional[np.ndarray]:
        """Mevcut kareyi döndürür (kopya)."""
        if 0 <= self.current_index < len(self.frames):
            return self.frames[self.current_index].copy()
        return None

    def next_frame(self) -> Optional[np.ndarray]:
        """Bir sonraki kareye geçer ve o kareyi döndürür."""
        if self.current_index + 1 < len(self.frames):
            self.current_index += 1
            return self.get_current_frame()
        return None

    def previous_frame(self) -> Optional[np.ndarray]:
        """Bir önceki kareye geçer ve o kareyi döndürür."""
        if self.current_index - 1 >= 0:
            self.current_index -= 1
            return self.get_current_frame()
        return None

    def select_current_frame(self) -> Optional[np.ndarray]:
        """Mevcut kareyi seçili olarak döndürür (kopya)."""
        return self.get_current_frame()

    def set_index(self, index: int):
        """Belirtilen indeksteki kareyi seçer."""
        if 0 <= index < len(self.frames):
            self.current_index = index