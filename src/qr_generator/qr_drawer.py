import qrcode

from PIL import Image

from src.qr_generator.config import ImageConfig
from src.qr_generator.drawable import Drawable


class QRDrawer(Drawable):
    def __init__(self, data: str):
        self.qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        self.data = data

    def draw(self) -> Image.Image:
        self.qr.clear()
        self.qr.add_data(self.data)
        self.qr.make(fit=True)
        qr_image = self.qr.make_image(fill_color="black", back_color="white")
        qr_height = ImageConfig.get_qr_height()
        return qr_image.resize((qr_height, qr_height), Image.Resampling.LANCZOS)
