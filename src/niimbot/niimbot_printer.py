import logging
import math
import struct
import time

from PIL import Image, ImageOps

from src.niimbot.enum import RequestCodeEnum, InfoEnum
from src.niimbot.packet import NiimbotPacket
from src.niimbot.serial_transport import SerialTransport


def packet_to_int(x):
    return int.from_bytes(x.data, "big")


def _encode_image(image: Image):
    img = ImageOps.invert(image.convert("L")).convert("1")
    for y in range(img.height):
        line_data = [img.getpixel((x, y)) for x in range(img.width)]
        line_data = "".join("0" if pix == 0 else "1" for pix in line_data)
        line_data = int(line_data, 2).to_bytes(math.ceil(img.width / 8), "big")
        counts = (0, 0, 0)  # It seems like you can always send zeros
        header = struct.pack(">H3BB", y, *counts, 1)
        pkt = NiimbotPacket(0x85, header + line_data)
        yield pkt


def log_buffer(prefix: str, buff: bytes):
    msg = ":".join(f"{i:#04x}"[-2:] for i in buff)
    logging.debug(f"{prefix}: {msg}")


class NiimbotPrint:
    def __init__(self, density=5, label_type=1):
        try:
            self._transport = SerialTransport(port="auto")
            self._packetbuf = bytearray()

            assert 1 <= density <= 5, "Density must be between 1 and 5"
            assert 1 <= label_type <= 3, "Label type must be between 1 and 3"

            assert self.set_label_density(density), "Failed to set label density"
            assert self.set_label_type(label_type), "Failed to set label type"

            logging.info("Printer initialized successfully")

        except Exception as e:
            logging.error(f"Failed to initialize printer: {str(e)}")
            raise RuntimeError(f"Printer initialization failed: {str(e)}") from e

    def print_image(self, image: Image):
        self.start_print()
        # self.allow_print_clear()  # Something unsupported in protocol decoding (B21)
        self.start_page_print()
        self.set_dimension(image.height, image.width)
        self.send_image(image)

        self.end_page_print()
        time.sleep(0.3)  # FIXME: Check get_print_status()
        while not self.end_print():
            time.sleep(0.1)

    def _recv(self):
        packets = []
        self._packetbuf.extend(self._transport.read(1024))
        while len(self._packetbuf) > 4:
            pkt_len = self._packetbuf[3] + 7
            if len(self._packetbuf) >= pkt_len:
                packet = NiimbotPacket.from_bytes(self._packetbuf[:pkt_len])
                log_buffer("recv", packet.to_bytes())
                packets.append(packet)
                del self._packetbuf[:pkt_len]
        return packets

    def _send(self, packet):
        self._transport.write(packet.to_bytes())

    def _transceiver(self, reqcode, data, respoffset=1):
        respcode = respoffset + reqcode
        packet = NiimbotPacket(reqcode, data)
        log_buffer("send", packet.to_bytes())
        self._send(packet)
        resp = None
        for _ in range(6):
            for packet in self._recv():
                if packet.type == 219:
                    raise ValueError
                elif packet.type == 0:
                    raise NotImplementedError
                elif packet.type == respcode:
                    resp = packet
            if resp:
                return resp
            time.sleep(0.1)
        return resp

    def get_info(self, key):
        if packet := self._transceiver(RequestCodeEnum.GET_INFO, bytes((key,)), key):
            match key:
                case InfoEnum.DEVICESERIAL:
                    return packet.data.hex()
                case InfoEnum.SOFTVERSION:
                    return packet_to_int(packet) / 100
                case InfoEnum.HARDVERSION:
                    return packet_to_int(packet) / 100
                case _:
                    return packet_to_int(packet)
        else:
            return None

    def get_rfid(self):
        packet = self._transceiver(RequestCodeEnum.GET_RFID, b"\x01")
        data = packet.data

        if len(data) < 1:
            raise RuntimeError("Invalid RFID data: empty response")

        if data[0] == 0:
            return None
        uuid = data[0:8].hex()
        idx = 8

        barcode_len = data[idx]
        idx += 1
        barcode = data[idx: idx + barcode_len].decode()

        idx += barcode_len
        serial_len = data[idx]
        idx += 1
        serial = data[idx: idx + serial_len].decode()

        idx += serial_len
        total_len, used_len, type_ = struct.unpack(">HHB", data[idx:])
        return {
            "uuid": uuid,
            "barcode": barcode,
            "serial": serial,
            "used_len": used_len,
            "total_len": total_len,
            "type": type_,
        }

    def heartbeat(self):
        packet = self._transceiver(RequestCodeEnum.HEARTBEAT, b"\x01")
        closingstate = None
        powerlevel = None
        paperstate = None
        rfidreadstate = None

        match len(packet.data):
            case 20:
                paperstate = packet.data[18]
                rfidreadstate = packet.data[19]
            case 13:
                closingstate = packet.data[9]
                powerlevel = packet.data[10]
                paperstate = packet.data[11]
                rfidreadstate = packet.data[12]
            case 19:
                closingstate = packet.data[15]
                powerlevel = packet.data[16]
                paperstate = packet.data[17]
                rfidreadstate = packet.data[18]
            case 10:
                closingstate = packet.data[8]
                powerlevel = packet.data[9]
                rfidreadstate = packet.data[8]
            case 9:
                closingstate = packet.data[8]

        return {
            "closingstate": closingstate,
            "powerlevel": powerlevel,
            "paperstate": paperstate,
            "rfidreadstate": rfidreadstate,
        }

    def send_image(self, image: Image):
        for pkt in _encode_image(image):
            self._send(pkt)

    def set_label_type(self, n):
        assert 1 <= n <= 3
        packet = self._transceiver(RequestCodeEnum.SET_LABEL_TYPE, bytes((n,)), 16)
        return bool(packet.data[0])

    def set_label_density(self, n):
        assert 1 <= n <= 5  # B21 has 5 levels, not sure for D11
        packet = self._transceiver(RequestCodeEnum.SET_LABEL_DENSITY, bytes((n,)), 16)
        return bool(packet.data[0])

    def start_print(self):
        packet = self._transceiver(RequestCodeEnum.START_PRINT, b"\x01")
        return bool(packet.data[0])

    def end_print(self):
        packet = self._transceiver(RequestCodeEnum.END_PRINT, b"\x01")
        return bool(packet.data[0])

    def start_page_print(self):
        packet = self._transceiver(RequestCodeEnum.START_PAGE_PRINT, b"\x01")
        return bool(packet.data[0])

    def end_page_print(self):
        packet = self._transceiver(RequestCodeEnum.END_PAGE_PRINT, b"\x01")
        return bool(packet.data[0])

    def allow_print_clear(self):
        packet = self._transceiver(RequestCodeEnum.ALLOW_PRINT_CLEAR, b"\x01", 16)
        return bool(packet.data[0])

    def set_dimension(self, h, w):
        packet = self._transceiver(
            RequestCodeEnum.SET_DIMENSION, struct.pack(">HH", h, w)
        )
        return bool(packet.data[0])

    def set_quantity(self, n):
        packet = self._transceiver(RequestCodeEnum.SET_QUANTITY, struct.pack(">H", n))
        return bool(packet.data[0])

    def get_print_status(self):
        try:
            packet = self._transceiver(RequestCodeEnum.GET_PRINT_STATUS, b"\x01", 16)
            if packet and len(packet.data) == 10:
                status = {
                    "page": struct.unpack(">H", packet.data[0:2])[0],
                    "progress1": packet.data[2],
                    "progress2": packet.data[3],
                    "state1": packet.data[4],
                    "state2": packet.data[5],
                    "isEnabled": packet.data[6] == 0,  # 0x00이면 True, 0x01이면 False
                    "reserved": packet.data[7:]
                }
                return status
            return None
        except (struct.error, IndexError):
            return None
