import time

import pytest
from PIL import Image

from src.niimbot.niimbot_printer import NiimbotPrint
from src.niimbot.enum import InfoEnum


@pytest.fixture
def printer():
    return NiimbotPrint()


@pytest.mark.info
def test_printer_info(printer):
    """프린터 기본 정보 테스트"""
    # 기본 정보 확인
    assert printer.get_rfid() is not None
    assert printer.heartbeat() is not None

    # 디바이스 정보 확인
    assert printer.get_info(InfoEnum.DEVICESERIAL) is not None
    assert printer.get_info(InfoEnum.BATTERY) is not None
    assert printer.get_info(InfoEnum.SOFTVERSION) is not None


@pytest.mark.heartbeat
def test_printer_heartbeat(printer):
    """프린터 하트비트 테스트"""
    heartbeat = printer.heartbeat()
    assert heartbeat is not None
    assert isinstance(heartbeat, dict)

    # 하트비트 응답 필수 키 확인
    assert 'closingstate' in heartbeat
    assert 'powerlevel' in heartbeat
    assert 'paperstate' in heartbeat
    assert 'rfidreadstate' in heartbeat

    # 전원 레벨 확인 (있는 경우)
    if heartbeat['powerlevel'] is not None:
        assert 0 <= heartbeat['powerlevel'] <= 4


@pytest.mark.settings
def test_printer_settings(printer):
    """프린터 설정 테스트"""
    # 라벨 타입 설정
    assert printer.set_label_type(1) is True

    # 라벨 농도 설정
    assert printer.set_label_density(5) is True

    # dimension 설정
    assert printer.set_dimension(100, 200) is True


@pytest.mark.printer
def test_print_status(printer):
    """프린터 상태 확인 테스트"""
    status = printer.get_print_status()
    assert status is not None
    assert 'page' in status
    assert 'isEnabled' in status


@pytest.mark.print
def test_print_flow(printer):
    """기본 인쇄 설정 흐름 테스트"""
    # 1. 라벨 타입 설정
    printer.set_label_type(1)

    # 2. 농도 설정
    printer.set_label_density(5)

    # 3. dimension 설정
    printer.set_dimension(100, 200)

    # 4. quantity 설정
    printer.set_quantity(1)

    # 상태 확인
    status = printer.get_print_status()
    assert status is not None

@pytest.mark.print
def test_print(printer):
    img = Image.open("./img/test_print.png")
    height, width = 240, 320
    percentage = 100

    try:
        assert printer.start_print(), "Failed to start print"
        assert printer.allow_print_clear(), "Failed to allow print clear"
        assert printer.start_page_print(), "Failed to start page print"
        assert printer.set_dimension(height, width), "Failed to set dimensions"
        printer.receive_image(img)
        assert printer.end_page_print(), "Failed to end page print"

        while (status := printer.get_print_status()) and status['progress1'] != percentage:
            time.sleep(0.01)
        assert printer.end_print(), "Failed to end print"

    except Exception as e:
        raise RuntimeError(f"Print test failed: {str(e)}") from e


if __name__ == "__main__":
    pytest.main([__file__])
