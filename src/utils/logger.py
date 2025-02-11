import os
import logging

from logging.handlers import TimedRotatingFileHandler


def setup_logger():
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger('critical_errors')
    logger.setLevel(logging.ERROR)

    error_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, 'critical_errors.log'),
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    formatter = logging.Formatter(
        '\n[%(asctime)s]\nERROR: %(message)s\n' + '-' * 50
    )
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    return logger
