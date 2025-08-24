from celery import Celery
from app.config.settings import settings 
from app.logger.log_config import logger 

# Создаем экземпляр Celery-приложения
celery_app = Celery(
    'tunewave_tasks', # Имя твоего приложения Celery
    broker=settings.RABBITMQ_BROKER_URL, # Указываем, где находится RabbitMQ
    backend='rpc://', 
    include=['app.tasks'] # Указываем Celery, где искать твои задачи (файл app/tasks.py)
)

# Дополнительные настройки Celery
celery_app.conf.update(
    task_always_eager=False,     # Установи в True для синхронного выполнения задач (полезно для тестирования)
    task_acks_late=True,         # Подтверждение выполнения задачи после её обработки, не до
    worker_prefetch_multiplier=1, # Количество задач, которые воркер может взять за раз
    task_track_started=True,     # Отслеживать статус задачи 'STARTED'
    result_expires=3600,         # Результаты задач хранятся в бэкэнде 1 час
    timezone='UTC',              # Установи свой часовой пояс
    enable_utc=True,
    broker_connection_retry_on_startup=True, # Повторять попытки подключения к брокеру при запуске
)

logger.info(f"Celery: Приложение Celery '{celery_app.main}' инициализировано.")
logger.info(f"Celery: Брокер сообщений: {celery_app.broker_connection}")
logger.info(f"Celery: Бэкэнд результатов: {celery_app.backend}")
