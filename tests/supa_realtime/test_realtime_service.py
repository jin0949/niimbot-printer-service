import pytest
import logging

from src.supa_realtime.config import DATABASE_URL, JWT
from src.supa_realtime.realtime_service import RealtimeService


@pytest.mark.asyncio
async def test_realtime_connection():
    logging.basicConfig(level=logging.INFO)
    service = RealtimeService(DATABASE_URL, JWT, None)
    await service.test_connection()

