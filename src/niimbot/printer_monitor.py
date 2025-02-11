import logging
import threading
import time

from src.niimbot.niimbot_printer import NiimbotPrint
from src.niimbot.serial_transport import SerialTransport


class PrinterMonitor(threading.Thread):
    def __init__(self, printer: NiimbotPrint, transport: SerialTransport, logger: logging.Logger):
        super().__init__()
        self.printer = printer
        self.transport = transport
        self.logger = logger
        self.running = True
        self.daemon = True
        self.reinit_attempts = 0
        self.MAX_REINIT_ATTEMPTS = 3

    def _handle_critical_failure(self, error):
        self.logger.error(
            f"CRITICAL: Printer failed after {self.MAX_REINIT_ATTEMPTS} reinit attempts\n"
            f"Last error: {str(error)}\n"
            "Shutting down service..."
        )
        exit(1)

    def _attempt_printer_reinit(self):
        try:
            self.reinitialize_printer()
        except Exception as reinit_error:
            self.logger.error(
                f"Printer reinitialization failed (Attempt {self.reinit_attempts}/{self.MAX_REINIT_ATTEMPTS})\n"
                f"Error: {str(reinit_error)}"
            )

    def run(self):
        while self.running:
            try:
                status = self.printer.heartbeat()
                if status is None:
                    raise Exception("Printer not responding to heartbeat")
                self.reinit_attempts = 0

            except Exception as e:
                if self.reinit_attempts >= self.MAX_REINIT_ATTEMPTS:
                    self._handle_critical_failure(e)

                self.reinit_attempts += 1
                self._attempt_printer_reinit()

            time.sleep(5)

    def reinitialize_printer(self):
        self.transport.close()
        time.sleep(2)
        self.transport.open()
        time.sleep(1)
        self.printer = NiimbotPrint(transport=self.transport)

    def stop(self):
        self.running = False