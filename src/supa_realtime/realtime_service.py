import asyncio
import logging
import json

from realtime import AsyncRealtimeClient
from src.niimbot.niimbot_printer import NiimbotPrint
from src.qr_generator.layout import ImageLayout
from src.supa_db.supa_db import SupaDB
from src.utils.suppress_log import temporary_log_level


class RealtimeService:
    def __init__(self, url: str, jwt: str, printer: NiimbotPrint, supa_api: SupaDB):
        self.url = url
        self.jwt = jwt
        self.printer = printer
        self.supa_api = supa_api
        self._socket = None
        self._channel = None
        self._heartbeat_task = None
        self._is_running = False
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._reconnect_delay = 5
        logging.info(f"RealtimeService initialized with URL: {url}")

    async def _printer_heartbeat_monitor(self):
        while True:
            try:
                self.printer.check_printer_connection()
                logging.debug("Printer heartbeat check: OK")
            except Exception as e:
                logging.error(f"Printer heartbeat check failed: {str(e)}")
            await asyncio.sleep(300)

    async def _cleanup_channel(self):
        if self._channel:
            try:
                await self._channel.unsubscribe()
                logging.debug("Existing channel unsubscribed")
            except Exception as e:
                logging.warning(f"Error unsubscribing channel: {str(e)}")
            finally:
                self._channel = None

    async def _cleanup_socket(self):
        if self._socket:
            try:
                await self._socket.close()
                logging.debug("Existing socket closed")
            except Exception as e:
                logging.warning(f"Error closing socket: {str(e)}")
            finally:
                self._socket = None

    async def _setup_channel(self):
        try:
            await self._cleanup_channel()
            self._channel = self._socket.channel("realtime:public:laundry")
            await self._channel.on_postgres_changes(
                event="INSERT",
                schema="public",
                table="laundry",
                callback=self._callback_wrapper
            ).subscribe()
            logging.info("Channel subscribed successfully")
            return True
        except Exception as e:
            logging.error(f"Channel setup failed: {str(e)}")
            await self._cleanup_channel()
            return False

    async def _connect_socket(self):
        try:
            await self._cleanup_socket()
            with temporary_log_level(logging.WARNING):
                self._socket = AsyncRealtimeClient(
                    f"{self.url}/realtime/v1",
                    self.jwt,
                    auto_reconnect=False
                )
                await self._socket.connect()
            logging.debug("New socket connected")
            return True
        except Exception as e:
            logging.error(f"Socket connection failed: {str(e)}")
            await self._cleanup_socket()
            return False

    def _callback_wrapper(self, payload):
        asyncio.create_task(self._handle_print_request(payload))

    async def _handle_print_request(self, payload):
        try:
            record = payload['data']['record']
            laundry_id = record['id']
            amount = record['amount']
            requested_by = record['requested_by']
            user_name = self.supa_api.get_user_name(requested_by)
            logging.info(f"Print request received - User: {user_name}, Amount: {amount}")

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

    async def establish_connection(self):
        logging.info("Establishing socket connection...")
        try:
            if not await self._connect_socket():
                logging.warning("Failed to connect socket")
                return False

            if not await self._setup_channel():
                logging.warning("Failed to setup channel")
                await self._cleanup_socket()
                return False

            return True
        except Exception as e:
            logging.error(f"Connection establishment failed: {str(e)}")
            await self._cleanup_socket()
            return False

    async def start_listening(self):
        self._is_running = True
        self._reconnect_attempts = 0
        self._heartbeat_task = asyncio.create_task(self._printer_heartbeat_monitor())

        while self._is_running:
            try:
                if not self._socket or not self._socket.is_connected:
                    if self._reconnect_attempts >= self._max_reconnect_attempts:
                        raise RuntimeError("Failed to establish realtime connection after maximum retries")

                    logging.warning(
                        f"Socket disconnected, attempting to reconnect... (Attempt {self._reconnect_attempts + 1}/{self._max_reconnect_attempts})")
                    success = await self.establish_connection()

                    if not success:
                        self._reconnect_attempts += 1
                        await asyncio.sleep(self._reconnect_delay)
                        continue

                    self._reconnect_attempts = 0
                    logging.info("Successfully reconnected")

                await self._socket.listen()

            except Exception as e:
                if self._is_running:
                    raise RuntimeError(f"Realtime service critical failure: {str(e)}")

    async def stop_listening(self):
        self._is_running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        await self._cleanup_channel()
        await self._cleanup_socket()
        logging.warning("Service stopped and connection closed")
