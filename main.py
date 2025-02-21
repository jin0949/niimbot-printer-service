import asyncio
import logging
import os
import argparse
import sys

from setproctitle import setproctitle
from dotenv import load_dotenv

from src.niimbot.niimbot_printer import NiimbotPrint
from src.supa_db.supa_db import SupaDB
from src.supa_realtime.realtime_service import RealtimeService
from src.utils.logger import setup_logger
from src.utils.print_test_page import print_test_page

# User configurations
SERIAL_PORT = "/dev/ttyACM0"
# SERIAL_PORT = "COM4"
SERVICE_NAME = "printer-service"


def parse_arguments():
    parser = argparse.ArgumentParser(description='Printer Service')
    parser.add_argument('--port', default=SERIAL_PORT, help='Serial port for printer connection')
    parser.add_argument('--log-level',
                        default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set the logging level')
    parser.add_argument('--log-dir',
                        default='logs',
                        help='Directory for log files')
    return parser.parse_args()


async def main():
    try:
        args = parse_arguments()

        setup_logger(args.log_dir, logging.getLevelName(args.log_level))
        setproctitle(SERVICE_NAME)
        load_dotenv()

        database_url = os.getenv('DATABASE_URL')
        jwt = os.getenv('JWT')

        if not all([database_url, jwt]):
            raise Exception("Required environment variables are missing")

        logging.info(f"Starting {SERVICE_NAME} with port {args.port}")

        printer = NiimbotPrint(port=args.port)
        # 첫 출력 공백문제 때문에 테스트 페이지 출력
        print_test_page(printer)

        supa_api = SupaDB(database_url, jwt)
        service = RealtimeService(database_url, jwt, printer, supa_api)

        await service.start_listening()

    except (KeyboardInterrupt, asyncio.CancelledError):
        logging.info("Service shutting down gracefully...")
        if 'service' in locals():
            await service.stop_listening()
    except Exception as e:
        logging.critical(f"Service error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
