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
    def __init__(self, density=5, label_type=1, port="auto"):
        self._transport = SerialTransport(port)
        self._packetbuf = bytearray()

        assert 1 <= density <= 5, "Density must be between 1 and 5"
        assert 1 <= label_type <= 3, "Label type must be between 1 and 3"

        self.set_label_density(density)
        self.set_label_type(label_type)

        logging.info("Printer initialized successfully")

    def check_printer_connection(self):
        """Check printer connection status and attempt reconnection if necessary."""
        logging.info("Initiating printer connection check")

        try:
            status = self.heartbeat()

            if status is None:
                logging.warning("Printer connection lost, attempting reconnection")

                # Attempt reconnection
                self._transport.reconnect()
                logging.info("Waiting for printer to initialize after reconnection")
                time.sleep(1)

                # Verify reconnection
                status = self.heartbeat()
                if status is None:
                    logging.error("Printer reconnection failed - No response received")
                    raise Exception("Printer connection failed after reconnection attempt")

                logging.info("Printer reconnection successful")
                return True

            logging.debug("Printer connection check: OK")
            return True

        except Exception as e:
            error_msg = str(e)
            logging.error(f"Printer communication error: {error_msg}")
            raise Exception(f"Printer communication error: {error_msg}")

    def check_printer_status(self):
        """Check printer status and raise exceptions for any detected issues."""
        logging.info("Starting comprehensive printer status check")

        try:
            # Check connection first
            logging.debug("Verifying printer connection")
            self.check_printer_connection()

            # Get status information
            logging.debug("Retrieving printer heartbeat and status")
            heartbeat = self.heartbeat()
            print_status = self.get_print_status()

            # Check cover status
            if heartbeat['closingstate'] != 0:
                logging.error("Printer error: Cover is open")
                raise Exception("Printer cover is open")

            # Check battery level
            if heartbeat['powerlevel'] is not None and heartbeat['powerlevel'] < 1:
                logging.error(f"Printer error: Low battery (Level: {heartbeat['powerlevel']})")
                raise Exception("Printer battery is too low")

            # Check print status for paper jam or other issues
            if print_status and not print_status['isEnabled']:
                logging.error("Printer error: Device is disabled (paper jam or other error)")
                raise Exception("Printer is in an unusable state (paper jam or other error)")

            logging.info("Printer status check completed successfully")
            return True

        except Exception as e:
            error_msg = str(e)
            logging.error(f"Printer status check failed: {error_msg}")
            raise Exception(f"Printer status error: {error_msg}")

    def print_image(self, image: Image.Image):
        """Print the provided image using the thermal printer."""
        logging.info("Starting new print job")

        try:
            # Comprehensive printer status check
            logging.debug("Performing initial printer status check")
            self.check_printer_status()

            # Initialize print sequence
            logging.debug("Initializing print sequence")
            self.start_print()
            self.allow_print_clear()
            self.start_page_print()

            # Configure and send image
            logging.debug(f"Setting image dimensions - Height: {image.height}, Width: {image.width}")
            self.set_dimension(image.height, image.width)

            logging.debug("Sending image data to printer")
            self.receive_image(image)

            logging.debug("Finalizing page print")
            self.end_page_print()

            # Monitor print progress
            timeout = time.time() + 30  # 30-second timeout
            logging.info("Monitoring print progress")

            while (status := self.get_print_status()) and status['progress1'] != 100:
                if time.time() > timeout:
                    logging.error("Print job timed out after 30 seconds")
                    raise Exception("Print job timeout")

                if status and not status['isEnabled']:
                    logging.error("Printer became disabled during print job")
                    raise Exception("Printer entered unusable state during printing")

                time.sleep(0.01)

            logging.debug("Completing print job")
            self.end_print()

            logging.info("Print job completed successfully")

        except Exception as e:
            error_msg = str(e)
            logging.error(f"Print job failed: {error_msg}")

            try:
                logging.debug("Attempting to clean up failed print job")
                self.end_print()
            except Exception as cleanup_error:
                logging.warning(f"Failed to clean up print job: {str(cleanup_error)}")

            raise Exception(f"Print job failed: {error_msg}")

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

    def receive_image(self, image: Image):
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
