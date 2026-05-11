from typing import List
from PIL import Image
from domain.i_pptx_reader import IPPTXReader
from domain.i_pptx_writer import IPPTXWriter
from domain.i_grid_composer import IGridComposer
from utils.grid_utils import calculate_grid_dimensions
from config.settings import DEFAULT_GRID_MARGIN_PX

class GridComposerService:
    def __init__(self, reader: IPPTXReader, writer: IPPTXWriter, composer: IGridComposer):
        self.reader = reader
        self.writer = writer
        self.composer = composer

    def apply_grid(self, selected_indices: List[int], margin: int = DEFAULT_GRID_MARGIN_PX) -> None:
        if len(selected_indices) < 2:
            raise ValueError("En az iki slayt seçmelisiniz")
        images = []
        for idx in selected_indices:
            imgs = self.reader.get_slide_images(idx)
            images.extend(imgs)
        if not images:
            raise ValueError("Seçilen slaytlarda hiç resim bulunamadı")
        rows, cols = calculate_grid_dimensions(len(images))
        grid_image = self.composer.compose(images, rows, cols, margin)
        self.writer.rebuild_with_grid(selected_indices, grid_image)
        self.reader.update_from_writer(self.writer)