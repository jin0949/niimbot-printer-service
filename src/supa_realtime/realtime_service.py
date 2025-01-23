import asyncio
from realtime import AsyncRealtimeClient
import logging
from typing import Callable

class RealtimeService:
    def __init__(self, url: str, jwt: str, callback: Callable):
        self.url = url
        self.jwt = jwt
        self.callback = callback
        self._socket = None

    def _callback_wrapper(self, payload):
        asyncio.create_task(self.callback(payload))

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

        logging.info("데이터베이스 변경 감지 설정 완료")
        await self._socket.listen()

    async def test_connection(self):
        self._socket = AsyncRealtimeClient(f"{self.url}/realtime/v1", self.jwt, auto_reconnect=True)
        await self._socket.connect()
        logging.info("Connection test passed: Socket connection was established")
        await self._socket.close()
        logging.info("Connection closed successfully")
