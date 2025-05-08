import logging
import sys
from logging.handlers import RotatingFileHandler

def configure_logging(level=logging.INFO, log_file='app/logger/logs/app.log'):
    formatter = logging.Formatter(
        fmt='[%(asctime)s] %(name)s:%(lineno)d %(levelname)-7s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    #console_handler = logging.StreamHandler(sys.stdout)
    #console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(log_file) #, maxBytes=5*1024*1024, backupCount=3
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)


    if not root_logger.handlers:
        #root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
