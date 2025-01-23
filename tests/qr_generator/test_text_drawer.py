import pytest
from PIL import Image
import os
from src.text_drawer import TextDrawer
from src.config import ImageConfig


@pytest.fixture
def text_drawer():
    return TextDrawer("테스트 텍스트")


def test_draw_returns_image(text_drawer):
    # 텍스트 이미지 생성 테스트
    result = text_drawer.draw()
    assert isinstance(result, Image.Image)
    assert result.size == (ImageConfig.WIDTH, ImageConfig.HEIGHT)


def test_save_image(text_drawer):
    # 이미지 저장 테스트
    save_path = "img/text_test.png"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    image = text_drawer.draw()
    image.save(save_path)

    assert os.path.exists(save_path)
