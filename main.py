import asyncio
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import json
from setproctitle import setproctitle

from src.niimbot.niimbot_printer import NiimbotPrint
from src.niimbot.serial_transport import SerialTransport
from src.qr_generator.layout import ImageLayout
from src.supa_db.supa_db import SupaDB
from src.supa_realtime.config import DATABASE_URL, JWT
from src.supa_realtime.realtime_service import RealtimeService


def setup_logger():
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, 'printer-service.log')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


class LaundryHandler:
    def __init__(self, supa_api: SupaDB, service: RealtimeService, label_printer: NiimbotPrint):
        self.supa_api = supa_api
        self.service = service
        self.label_printer = label_printer

        self.service.set_callback(self.handle_change)

    async def handle_change(self, payload):
        logging.info(f"Database change detected: {payload}")
        record = payload['data']['record']
        laundry_id = record['id']
        amount = record['amount']
        requested_by = record['requested_by']
        user_name = self.supa_api.get_user_name(requested_by)

        for i in range(amount):
            number = i + 1
            data = {
                "id": laundry_id,
                "number": number
            }
            json_data = json.dumps(data)
            image = ImageLayout.create_qr_image(json_data, f"{user_name} {number}")
            self.label_printer.print_image(image)

    async def start(self):
        await self.service.start_listening()


async def main():
    setproctitle("printer-service")
    setup_logger()  # 로깅 설정 추가

    try:
        # Initialize components
        port = "/dev/ttyACM0"
        transport = SerialTransport(port=port)
        printer = NiimbotPrint(transport=transport)
        supa_api = SupaDB(DATABASE_URL, JWT)
        service = RealtimeService(DATABASE_URL, JWT)

        handler = LaundryHandler(
            supa_api=supa_api,
            service=service,
            label_printer=printer
        )

        await handler.start()
    except Exception as e:
        logging.error(f"Main process error: {str(e)}")
    finally:
        if transport:
            transport.close()


if __name__ == "__main__":
    asyncio.run(main())
