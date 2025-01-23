from PIL import Image

from src.qr_generator.config import ImageConfig
from src.qr_generator.qr_drawer import QRDrawer
from src.qr_generator.text_drawer import TextDrawer


class ImageLayout:
    @staticmethod
    def create_qr_image(data: str, text: str) -> Image.Image:
        background = Image.new('RGB', (ImageConfig.WIDTH, ImageConfig.HEIGHT), 'white')
        qr_image = QRDrawer(data).draw()
        text_image = TextDrawer(text).draw()

        x = (ImageConfig.WIDTH - qr_image.width) // 2
        background.paste(qr_image, (x, 0))
        background.paste(text_image, (0, -20), text_image)

        return background

    @staticmethod
    def save_qr_image(data: str, username: str, save_path: str):
        image = ImageLayout.create_qr_image(data, username)
        image.save(save_path)

