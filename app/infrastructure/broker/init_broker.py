from app.config.log_config import logger
from pika.adapters.blocking_connection import BlockingChannel
from app.config.settings import settings


class InitBroker:

    def __init__(self,channel: BlockingChannel):
        logger.info('InitBroker: init channel')
        self._channel: BlockingChannel = channel


    def declare_inf(self):
        dlx_conf = settings.rabbit.DLX_MAIN
        self._channel.exchange_declare(
            exchange=dlx_conf.name,
            exchange_type=dlx_conf.type,
            durable=dlx_conf.durable
        )

        dlq_conf = settings.rabbit.DLQ_MAIN
        self._channel.queue_declare(
            queue=dlq_conf.name,
            durable=dlq_conf.durable
        )

        self._channel.queue_bind(
            queue=dlq_conf.name,
            exchange=dlx_conf.name,
            routing_key=dlq_conf.routing_key
        )
        logger.info('InitBroker: DLX/DLQ topology declared.')

        for exc_detail in settings.rabbit.EXCHANGES:
            self._channel.exchange_declare(
                exchange=exc_detail.name,
                exchange_type=exc_detail.type,
                durable=exc_detail.durable
            )
            logger.info(f"InitBroker: Exchange '{exc_detail.name}' declared.")

        dlx_args = {"x-dead-letter-exchange": settings.rabbit.DLX_MAIN.name}

        for q_detail in settings.rabbit.QUEUES:
            self._channel.queue_declare(
                queue=q_detail.name,
                durable=q_detail.durable,
                arguments=dlx_args
            )

            self._channel.queue_bind(
                queue=q_detail.name,
                exchange=q_detail.exchange_name,
                routing_key=q_detail.routing_key
            )
            logger.info(f"InitBroker: Queue '{q_detail.name}' bound to '{q_detail.exchange_name}'.")

