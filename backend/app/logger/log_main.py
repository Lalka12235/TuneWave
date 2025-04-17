import logging

from app.logger.log_config import configure_logging


def main():
    configure_logging(level=logging.INFO)