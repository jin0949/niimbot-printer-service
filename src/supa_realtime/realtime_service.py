import asyncio
import logging
import json

from realtime import AsyncRealtimeClient
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
        try:
            # 기본 데이터 추출
            record = payload['data']['record']
            laundry_id = record['id']
            amount = record['amount']
            requested_by = record['requested_by']
            user_name = self.supa_api.get_user_name(requested_by)
            logging.info(f"Print request received - User: {user_name}, Amount: {amount}")

            # 프린트 작업 수행
            for i in range(amount):
                try:
                    self.printer.check_printer_status()
                    number = i + 1
                    data = {"id": laundry_id, "number": number}
                    json_data = json.dumps(data)
                    image = ImageLayout.create_qr_image(json_data, f"{user_name} {number}")
                    self.printer.print_image(image)
                    logging.info(f"Print success - User: {user_name}, Number: {number}/{amount}")

                except Exception as e:
                    error_msg = str(e)
                    logging.error(f"Print failed - Error: {error_msg}")
                    if "프린터 커버가 열려있습니다" in error_msg:
                        raise Exception("프린터 커버가 열려있어 인쇄할 수 없습니다")
                    if "프린터 배터리가 부족합니다" in error_msg:
                        raise Exception("프린터 배터리가 부족하여 인쇄할 수 없습니다")
                    if "용지 걸림" in error_msg or "사용 불가능한 상태" in error_msg:
                        raise Exception("프린터가 사용 불가능한 상태입니다")
                    raise Exception(f"알 수 없는 프린터 오류가 발생했습니다: {error_msg}")

            logging.info(f"All prints completed - User: {user_name}, Total Amount: {amount}")

        except Exception as e:
            logging.error(f"Print job failed - Error: {str(e)}")
            raise

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
