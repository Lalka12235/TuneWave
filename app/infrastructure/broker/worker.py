import json
import time
from pika import BlockingConnection,URLParameters
from app.config.log_config import logger
from app.config.settings import settings
from app.infrastructure.broker.init_broker import InitBroker
from app.infrastructure.broker.consumer import Consumer
from app.infrastructure.celery.email import EmailService


def callback_send_email(email_service: EmailService):

    def callback(body: bytes):
        try:
            message_data = json.loads(body.decode('utf-8'))

            recipient = message_data.get('email')
            username = message_data.get('username')

            if not recipient and not username:
                raise ValueError()

            email_service.send_email(recipient,username)
            logger.info(f"Task Handler: Successfully processed email for {recipient}.")

        except json.JSONDecodeError:
            logger.error(f"Task Handler: Failed to decode JSON from message body: {body}")
            raise

        except Exception as e:
            logger.error(f"Task Handler: Error during email processing: {e}")
            raise


    return callback


def run_email_send(retries: int = 5,):
    _connection = None
    max_retries = retries
    email_service = EmailService()


    for attempt in range(5):
        try:
            _connection = BlockingConnection(URLParameters(settings.rabbit.RABBITMQ_BROKER_URL))

            _channel = _connection.channel()
            init_broker = InitBroker(_channel)
            init_broker.declare_inf()

            consumer = Consumer(_connection)

            consumer.start_consuming(
                queue_name=settings.rabbit.QUEUES[0].name,
                exchange_name=settings.rabbit.QUEUES[0].exchange_name,
                processing_callback=callback_send_email(email_service),
                routing_key=settings.rabbit.QUEUES[0].routing_key,
                durable=True
            )
            break
        except Exception as e:
            logger.error(f"Worker: Connection error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                logger.error("Worker: Maximum connection retries reached. Exiting.")
                return