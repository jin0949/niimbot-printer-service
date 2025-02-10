import asyncio
import logging
import json

from setproctitle import setproctitle

from src.niimbot.niimbot_printer import NiimbotPrint
from src.qr_generator.layout import ImageLayout
from src.supa_db.supa_db import SupaDB
from src.supa_realtime.config import DATABASE_URL, JWT
from src.supa_realtime.realtime_service import RealtimeService


class LaundryHandler:
    def __init__(self):
        self.supa_api = SupaDB()
        self.service = RealtimeService(DATABASE_URL, JWT, self.handle_change)
        self.label_printer = NiimbotPrint(port="/dev/ttyACM0")


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
            # printer 출력
            self.label_printer.print_image(image)

    async def start(self):
        await self.service.start_listening()


async def main():
    setproctitle("printer-service")
    logging.basicConfig(level=logging.INFO)
    handler = LaundryHandler()
    await handler.start()


if __name__ == "__main__":
    asyncio.run(main())
