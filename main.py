import asyncio
import os
import sys
import logging

from setproctitle import setproctitle
from dotenv import load_dotenv

from src.niimbot.niimbot_printer import NiimbotPrint
from src.supa_db.supa_db import SupaDB
from src.supa_realtime.realtime_service import RealtimeService
from src.utils.logger import setup_logger
from src.utils.print_test_page import print_test_page

# User configurations
SERIAL_PORT = "/dev/ttyACM0"
SERVICE_NAME = "printer-service"

# Set log Level
LOG_LEVEL = logging.ERROR

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
JWT = os.getenv('JWT')


async def main():
    setproctitle(SERVICE_NAME)
    setup_logger(LOG_LEVEL)

    try:
        printer = NiimbotPrint(port=SERIAL_PORT)
        # 첫 출력 공백문제 때문에 테스트 페이지 출력
        print_test_page(printer)

        supa_api = SupaDB(DATABASE_URL, JWT)
        service = RealtimeService(DATABASE_URL, JWT, printer, supa_api)
        await service.start_listening()

    except Exception as e:
        logging.error(
            f"CRITICAL: Service initialization failed\n"
            f"Error: {str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())