from app.config.log_config import logger
from pika import BlockingConnection
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import BasicProperties

class Publisher:

    def __init__(self,connection: BlockingConnection) -> None:
        logger.info('Consumer: init publisher')
        self._connection: BlockingConnection = connection
        self._channel: BlockingChannel = self._connection.channel()


    def publish_message(self,exchange_name: str,routing_key: str,body: bytes):
        self._channel.basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=body,
            properties=BasicProperties(delivery_mode=2)
        )

        logger.info('Publisher: sent %s to %s exchange',body.decode(),exchange_name)