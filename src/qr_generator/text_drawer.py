import os

from PIL import Image, ImageFont, ImageDraw

from src.qr_generator.config import ImageConfig
from src.qr_generator.drawable import Drawable


class TextDrawer(Drawable):
    def __init__(self, text: str):
        self.text = text
        self.font_path = os.path.join(os.path.dirname(__file__), './assets/NanumGothic.ttf')

    def draw(self) -> Image.Image:
        text_layer = Image.new('RGBA', (ImageConfig.WIDTH, ImageConfig.HEIGHT), (255, 255, 255, 0))
        font = ImageFont.truetype(self.font_path, ImageConfig.FONT_SIZE) if os.path.exists(
            self.font_path) else ImageFont.load_default()

        draw = ImageDraw.Draw(text_layer)
        text_bbox = draw.textbbox((0, 0), self.text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (ImageConfig.WIDTH - text_width) // 2
        text_y = ImageConfig.get_qr_height() + (
                (ImageConfig.HEIGHT - ImageConfig.get_qr_height() - (text_bbox[3] - text_bbox[1])) // 2
        )

        draw.text((text_x, text_y), self.text, font=font, fill='black')
        return text_layer
