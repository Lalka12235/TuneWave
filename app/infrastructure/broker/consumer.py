from app.config.log_config import logger
from pika import BlockingConnection
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties
from typing import Callable

class Consumer:

    def __init__(self,connection: BlockingConnection) -> None:
        logger.info('Consumer: init consumer')
        self._connection: BlockingConnection = connection
        self._channel: BlockingChannel = self._connection.channel()
        self._channel.basic_qos(prefetch_count=1)
        self.external_processing_callback = None

    def declare_exchange(self,exchange_name: str,exchange_type: str,durable: bool = True):
        self._channel.exchange_declare(exchange=exchange_name,exchange_type=exchange_type,durable=durable)

    def _message_handler(self, ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes):
        """
        Внутренний обработчик Pika, который управляет ACK/NACK и вызывает внешний обработчик.

        Аргументы:
            ch (BlockingChannel): Объект канала, нужен для ack/nack.
            method (Basic.Deliver): Метаданные сообщения, содержит delivery_tag.
            properties (BasicProperties): Свойства сообщения.
            body (bytes): Тело сообщения.
        """
        if not self.external_processing_callback:
            logger.error("Consumer: External callback not set. Sending NACK.")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        try:
            self.external_processing_callback(body)

            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Message ID {method.delivery_tag} successfully processed and ACKed.")

        except Exception as e:
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            logger.error(f"Message ID {method.delivery_tag} failed processing. Sent NACK. Error: {e}")

    def start_consuming(self,queue_name: str,exchange_name: str,processing_callback: Callable,routing_key: str | None = None,durable: bool = True):
        self.external_processing_callback = processing_callback

        self._channel.queue_declare(queue=queue_name,durable=durable)
        self._channel.queue_bind(queue=queue_name, exchange=exchange_name, routing_key=routing_key)

        self._channel.basic_consume(queue=queue_name,on_message_callback=self._message_handler)

        self._channel.start_consuming()