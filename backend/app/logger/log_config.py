import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent

def configure_logging(level=logging.INFO, log_file_prefix='app'):
    os.makedirs(os.path.dirname(BASE_DIR / 'logs'), exist_ok=True)

    watchfiles_logger = logging.getLogger('watchfiles.main')
    watchfiles_logger.setLevel(logging.WARNING)

    formatter = logging.Formatter(
        fmt='[%(asctime)s] %(name)s:%(lineno)d %(levelname)-7s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    current_date = datetime.now().strftime("%Y-%m-%d")
    log_file_name = BASE_DIR / f'{log_file_prefix}_{current_date}.log'

    file_handler = RotatingFileHandler(log_file_name, mode='a', maxBytes=5 * 1024 * 1024, backupCount=3)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    root_logger.handlers.clear()
    
    root_logger.addHandler(file_handler)
