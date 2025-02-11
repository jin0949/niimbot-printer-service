from src.niimbot.niimbot_printer import NiimbotPrint
from PIL import Image


def print_test_page(printer: NiimbotPrint):
    image = Image.open('./sample.png')
    printer.print_image(image)
    image.close()