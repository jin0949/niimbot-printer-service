from PIL import Image, ImageFont, ImageDraw
import os


def create_test_print():
    # 이미지 생성
    image = Image.new('RGB', (320, 240), 'white')
    draw = ImageDraw.Draw(image)

    # 폰트 설정
    font_path = os.path.join(os.path.dirname(__file__), './assets/NanumGothic.ttf')
    title_font = ImageFont.truetype(font_path, 30) if os.path.exists(font_path) else ImageFont.load_default()
    body_font = ImageFont.truetype(font_path, 20) if os.path.exists(font_path) else ImageFont.load_default()

    # 텍스트 추가
    title = "테스트 출력물"
    subtitle = "프린터 정상 작동 확인용"
    notice = "* 본 출력물은 폐기해 주세요 *"

    # 텍스트 위치 계산 및 그리기
    draw.text((160, 80), title, font=title_font, fill='black', anchor="mm")
    draw.text((160, 120), subtitle, font=body_font, fill='black', anchor="mm")
    draw.text((160, 180), notice, font=body_font, fill='black', anchor="mm")

    # 테두리 그리기
    draw.rectangle([(10, 10), (310, 230)], outline='black', width=2)
    image.save('./sample.png')
    return image