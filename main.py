import asyncio
import logging

from src.supa_realtime.config import DATABASE_URL, JWT
from src.supa_realtime.realtime_service import RealtimeService


async def handle_change(payload):
    logging.info(f"Database change detected: {payload}")

async def main():
    logging.basicConfig(level=logging.INFO)
    service = RealtimeService(DATABASE_URL, JWT, handle_change)
    await service.start_listening()

if __name__ == "__main__":
    asyncio.run(main())
