from celery import Celery
from app.config.settings import settings 
from app.config.log_config import logger


celery_app = Celery(
    'tunewave_tasks',
    broker=settings.rabbit.RABBITMQ_BROKER_URL,
    backend='rpc://', 
    include=['infrastructure.celery.tasks']
)

celery_app.conf.update(
    task_always_eager=False,  
    task_acks_late=True,       
    worker_prefetch_multiplier=1,
    task_track_started=True,    
    result_expires=3600,        
    timezone='UTC',              
    enable_utc=True,
    broker_connection_retry_on_startup=True, 
)

logger.info(f"Celery: Приложение Celery '{celery_app.main}' инициализировано.")
logger.info(f"Celery: Брокер сообщений: {celery_app.broker_connection}")
logger.info(f"Celery: Бэкэнд результатов: {celery_app.backend}")
