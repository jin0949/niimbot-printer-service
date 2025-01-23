import pytest
from PIL import Image
import os
from src.config import ImageConfig
from src.layout import ImageLayout


@pytest.fixture
def test_data():
    return {
        "url": "https://test.com",
        "username": "테스트유저",
    }


def test_create_qr_image(test_data):
    # QR 코드와 텍스트가 포함된 이미지 생성 테스트
    result = ImageLayout.create_qr_image(test_data["url"], test_data["username"])
    assert isinstance(result, Image.Image)
    assert result.size == (ImageConfig.WIDTH, ImageConfig.HEIGHT)
    assert result.mode == 'RGB'


def test_save_qr_image(test_data):
    # 완성된 이미지 저장 테스트
    save_path = "img/complete_test.png"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    ImageLayout.save_qr_image(test_data["url"], test_data["username"], save_path)

    assert os.path.exists(save_path)
    saved_image = Image.open(save_path)
    assert isinstance(saved_image, Image.Image)
