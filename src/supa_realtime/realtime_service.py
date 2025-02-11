import asyncio
import logging

from realtime import AsyncRealtimeClient
import json

from src.niimbot.niimbot_printer import NiimbotPrint
from src.qr_generator.layout import ImageLayout
from src.supa_db.supa_db import SupaDB


class RealtimeService:
    def __init__(self, url: str, jwt: str, printer: NiimbotPrint, supa_api: SupaDB):
        self.url = url
        self.jwt = jwt
        self._socket = None
        self.printer = printer
        self.supa_api = supa_api

    def _callback_wrapper(self, payload):
        asyncio.create_task(self._handle_print_request(payload))

    async def _handle_print_request(self, payload):
        record = payload['data']['record']
        laundry_id = record['id']
        amount = record['amount']
        requested_by = record['requested_by']
        user_name = self.supa_api.get_user_name(requested_by)

        logging.info(f"Print request received - User: {user_name}, Amount: {amount}")

        for i in range(amount):
            number = i + 1
            data = {
                "id": laundry_id,
                "number": number
            }
            json_data = json.dumps(data)
            image = ImageLayout.create_qr_image(json_data, f"{user_name} {number}")
            self.printer.print_image(image)

        logging.info(f"Print completed - User: {user_name}, Amount: {amount}")

    async def start_listening(self):
        self._socket = AsyncRealtimeClient(f"{self.url}/realtime/v1", self.jwt, auto_reconnect=True)
        await self._socket.connect()
        channel = self._socket.channel("realtime:public:laundry")

        await channel.on_postgres_changes(
            event="INSERT",
            schema="public",
            table="laundry",
            callback=self._callback_wrapper
        ).subscribe()

        logging.info("Realtime service started successfully")
        await self._socket.listen()

    async def test_connection(self):
        self._socket = AsyncRealtimeClient(f"{self.url}/realtime/v1", self.jwt, auto_reconnect=True)
        await self._socket.connect()
        await self._socket.close()
