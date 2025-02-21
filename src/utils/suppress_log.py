import contextlib
import logging


@contextlib.contextmanager
def temporary_log_level(temp_level):
    root_logger = logging.getLogger()
    original_level = root_logger.level
    root_logger.setLevel(temp_level)
    try:
        yield
    finally:
        root_logger.setLevel(original_level)