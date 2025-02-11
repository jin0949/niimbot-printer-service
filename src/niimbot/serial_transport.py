import time

import serial
from serial.tools.list_ports import comports


def detect_port():
    all_ports = list(comports())
    if len(all_ports) == 0:
        raise RuntimeError("No serial ports detected")
    if len(all_ports) > 1:
        msg = "Too many serial ports, please select specific one:"
        for port, desc, hwid in all_ports:
            msg += f"\n- {port} : {desc} [{hwid}]"
        raise RuntimeError(msg)
    return all_ports[0][0]


class SerialTransport:
    def __init__(self, port: str = "auto"):
        self.port = port if port != "auto" else detect_port()
        self._serial = serial.Serial(port=self.port, baudrate=115200, timeout=0.5)

    def read(self, length: int) -> bytes:
        return self._serial.read(length)

    def write(self, data: bytes):
        return self._serial.write(data)

    def close(self):
        if self._serial and self._serial.is_open:
            self._serial.close()

    def open(self):
        if self._serial and not self._serial.is_open:
            self._serial.open()

    def reconnect(self):
        """시리얼 연결을 재시도합니다."""
        try:
            self.close()
            time.sleep(1)  # 포트가 완전히 닫힐 때까지 대기

            # 포트 재탐색 (auto 모드일 경우)
            if self.port == "auto":
                self.port = detect_port()

            self._serial = serial.Serial(port=self.port, baudrate=115200, timeout=0.5)
            return True
        except Exception as e:
            raise Exception(f"프린터 재연결 실패: {str(e)}")
