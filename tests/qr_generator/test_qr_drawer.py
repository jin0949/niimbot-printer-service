import pytest
from PIL import Image
import os
from src.qr_drawer import QRDrawer
from src.config import ImageConfig


@pytest.fixture
def qr_drawer():
    return QRDrawer("https://test.com")


def test_draw_returns_image(qr_drawer):
    # QR 코드 이미지가 정상적으로 생성되는지 테스트
    result = qr_drawer.draw()
    assert isinstance(result, Image.Image)
    # 이미지 크기 확인
    expected_height = ImageConfig.get_qr_height()
    assert result.size == (expected_height, expected_height)
    # 이미지에 실제 내용이 있는지 확인
    extrema = result.convert('L').getextrema()
    assert extrema[0] < extrema[1]


def test_save_image(qr_drawer):
    # 이미지 저장 테스트
    save_path = "img/test.png"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # 이미지 생성 및 저장
    image = qr_drawer.draw()
    image.save(save_path)

    # 파일이 정상적으로 저장되었는지 확인
    assert os.path.exists(save_path)
    loaded_image = Image.open(save_path)
    assert isinstance(loaded_image, Image.Image)
