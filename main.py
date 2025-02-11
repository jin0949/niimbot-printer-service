import asyncio
import os
import sys
from setproctitle import setproctitle
from dotenv import load_dotenv

from src.niimbot.niimbot_printer import NiimbotPrint
from src.niimbot.printer_monitor import PrinterMonitor
from src.niimbot.serial_transport import SerialTransport
from src.supa_db.supa_db import SupaDB
from src.supa_realtime.realtime_service import RealtimeService
from src.utils.logger import setup_logger

# User configurations
SERIAL_PORT = "/dev/ttyACM0"
SERVICE_NAME = "printer-service"

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
JWT = os.getenv('JWT')


async def main():
    setproctitle(SERVICE_NAME)
    logger = setup_logger()

    transport = None
    printer_monitor = None

    try:
        transport = SerialTransport(port=SERIAL_PORT)
        printer = NiimbotPrint(transport=transport)

        printer_monitor = PrinterMonitor(printer, transport, logger)
        printer_monitor.start()

        supa_api = SupaDB(DATABASE_URL, JWT)
        service = RealtimeService(DATABASE_URL, JWT, printer, supa_api)
        await service.start_listening()

    except Exception as e:
        logger.error(
            f"CRITICAL: Service initialization failed\n"
            f"Error: {str(e)}"
        )
        sys.exit(1)
    finally:
        if printer_monitor:
            printer_monitor.stop()
        if transport:
            transport.close()


if __name__ == "__main__":
    asyncio.run(main())
