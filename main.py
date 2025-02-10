import asyncio
import logging
import json
from setproctitle import setproctitle

from src.niimbot.niimbot_printer import NiimbotPrint
from src.niimbot.serial_transport import SerialTransport
from src.qr_generator.layout import ImageLayout
from src.supa_db.supa_db import SupaDB
from src.supa_realtime.config import DATABASE_URL, JWT
from src.supa_realtime.realtime_service import RealtimeService


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
    logging.basicConfig(level=logging.INFO)

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


if __name__ == "__main__":
    asyncio.run(main())
