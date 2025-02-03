import pytest
import json
from PIL import Image
from src.niimbot.niimbot_printer import NiimbotPrint
from src.qr_generator.layout import ImageLayout


@pytest.fixture
def printer():
    return NiimbotPrint()

@pytest.mark.printer
def test_label_print(printer):
    for i in range(2):
        json_data = json.dumps({
            "id": "test_laundry_123",
            "number": i + 1
        })

        # QR 이미지 생성
        image = ImageLayout.create_qr_image(
            json_data,
            f"테스트 {i + 1}"
        )
        # image.save(f'./test{i}.png')

        # 프린터 출력 테스트
        assert isinstance(image, Image.Image), "이미지가 올바르게 생성되지 않았습니다"
        printer.print_image(image)
