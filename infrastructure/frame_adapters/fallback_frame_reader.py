# infrastructure/frame_adapters/fallback_frame_reader.py
import sys
from typing import Optional, Tuple, List
import numpy as np
from .i_frame_reader import IFrameReader
from .pipe_frame_reader import PipeFrameReader
from .file_frame_reader import FileFrameReader
from .raw_video_dumper import RawVideoDumper

class FallbackFrameReader(IFrameReader):
    """
    Birden fazla frame okuma stratejisini dener; ilk başarılı olanı kullanır.
    """

    def __init__(self, input_source: str, fps: int, resolution: Tuple[int, int],
                 strategies: Optional[List[type]] = None):
        """
        :param strategies: Denecek strateji sınıflarının listesi (IFrameReader implementasyonu)
                           Varsayılan: [PipeFrameReader, FileFrameReader]
        """
        self.input_source = input_source
        self.fps = fps
        self.resolution = resolution
        self._reader: Optional[IFrameReader] = None
        self._dumper: Optional[RawVideoDumper] = None   # FileFrameReader için gerekli
        self._buffered_frame: Optional[np.ndarray] = None

        if strategies is None:
            strategies = [PipeFrameReader, FileFrameReader]

        self._try_strategies(strategies)

    def _try_strategies(self, strategy_classes: List[type]) -> None:
        for strategy_cls in strategy_classes:
            try:
                if strategy_cls == FileFrameReader:
                    # FileFrameReader önce ham dosyaya dönüştürmeyi gerektirir
                    self._dumper = RawVideoDumper(self.input_source, self.fps, self.resolution)
                    raw_path = self._dumper.dump()
                    self._reader = FileFrameReader(raw_path)
                    self._buffered_frame = None
                else:
                    # PipeFrameReader veya diğer doğrudan stratejiler
                    self._reader = strategy_cls(self.input_source, self.fps, self.resolution)
                    first_frame = self._reader.read_frame()
                    if first_frame is None:
                        raise IOError("İlk frame alınamadı")
                    self._buffered_frame = first_frame
                # Başarılı olduysa döngüden çık
                return
            except Exception as e:
                print(f"Strateji {strategy_cls.__name__} başarısız: {e}", file=sys.stderr)
                self._cleanup()
        # Tüm stratejiler başarısız
        raise RuntimeError("Hiçbir frame okuma stratejisi çalışmadı.")

    def _cleanup(self):
        if self._reader:
            self._reader.release()
            self._reader = None
        if self._dumper:
            self._dumper.cleanup()
            self._dumper = None
        self._buffered_frame = None

    def read_frame(self) -> Optional[np.ndarray]:
        if self._buffered_frame is not None:
            frame = self._buffered_frame
            self._buffered_frame = None
            return frame
        if self._reader is None:
            return None
        return self._reader.read_frame()

    def release(self):
        self._cleanup()