class ImageConfig:
    WIDTH = 320
    HEIGHT = 240
    QR_RATIO = 0.8
    FONT_SIZE = 36

    @classmethod
    def get_qr_height(cls):
        return int(cls.HEIGHT * cls.QR_RATIO)
