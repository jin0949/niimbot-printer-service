import pytest
import serial

from src.niimbot.serial_transport import SerialTransport


@pytest.mark.serial
def test_serial_transport():
    # Test auto port detection
    transport = SerialTransport(port="auto")
    assert transport._serial.is_open, "Serial port failed to open"

    # Test read/write
    test_data = b"test"
    written = transport.write(test_data)
    assert written == len(test_data), "Failed to write all data"

    # Test invalid port
    with pytest.raises(serial.SerialException):
        SerialTransport(port="INVALID_PORT")
