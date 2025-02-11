import os
import logging
from logging.handlers import TimedRotatingFileHandler

def setup_logger(log_level=logging.INFO):
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 루트 로거 설정
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # 일반 로그 파일 핸들러
    service_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, 'service.log'),
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    service_handler.setLevel(log_level)
    service_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s'
    )
    service_handler.setFormatter(service_formatter)
    logger.addHandler(service_handler)

    # 에러 로그 파일 핸들러
    error_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, 'error.log'),
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)  # 에러 레벨 이상만 기록
    error_formatter = logging.Formatter(
        '\n[%(asctime)s]\nERROR: %(message)s\n' + '-'*50
    )
    error_handler.setFormatter(error_formatter)
    logger.addHandler(error_handler)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(service_formatter)
    logger.addHandler(console_handler)