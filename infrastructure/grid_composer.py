from PIL import Image
from typing import List
from domain.i_grid_composer import IGridComposer

class PillowGridComposer(IGridComposer):
    def compose(self, images: List[Image.Image], rows: int, cols: int, margin: int = 10) -> Image.Image:
        if len(images) > rows * cols:
            raise ValueError("Too many images for grid size")
        max_w = max(img.width for img in images)
        max_h = max(img.height for img in images)
        processed = []
        for img in images:
            canvas = Image.new("RGB", (max_w, max_h), (255,255,255))
            ratio = min(max_w/img.width, max_h/img.height)
            new_w = int(img.width * ratio)
            new_h = int(img.height * ratio)
            img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            x = (max_w - new_w) // 2
            y = (max_h - new_h) // 2
            canvas.paste(img_resized, (x, y))
            processed.append(canvas)
        grid_w = cols * max_w + (cols - 1) * margin
        grid_h = rows * max_h + (rows - 1) * margin
        grid = Image.new("RGB", (grid_w, grid_h), (255,255,255))
        for idx, img in enumerate(processed):
            row = idx // cols
            col = idx % cols
            x = col * (max_w + margin)
            y = row * (max_h + margin)
            grid.paste(img, (x, y))
        return grid