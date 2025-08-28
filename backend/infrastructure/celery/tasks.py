from backend.infrastructure.celery.celery import celery_app
from app.logger.log_config import logger
from app.utils.email import send_email


@celery_app.task(
    bind=True, # <-- ЭТО ОБЯЗАТЕЛЬНО
    default_retry_delay=300, # 5 минут
    max_retries=5 # Максимум 5 попыток
)
def send_email_task(
    self,
    recipient_email: str,
    subject: str,
    body: str,
) -> bool:
    """
    Отправляет электронное письмо указанному получателю асинхронно через Celery.
    
    Args:
        self: Экземпляр задачи Celery для доступа к контексту (например, повторным попыткам).
        recipient_email (str): Адрес электронной почты получателя.
        subject (str): Тема письма.
        body (str): Тело письма (может быть HTML или обычным текстом).

    Returns:
        bool: True, если письмо отправлено успешно, False в противном случае.
        (Задача Celery может также возвращать другие данные или бросать исключения)

    Raises:
        smtplib.SMTPException: Если возникла ошибка SMTP.
        Exception: Для других непредвиденных ошибок.
    """
    try:
        try_send = send_email(recipient_email, subject, body)
        if try_send:
            logger.info(f"Celery Task: Письмо успешно отправлено получателю: {recipient_email}")
            return True
        else:
            error_message = f"Celery Task: Функция send_email вернула False для {recipient_email}."
            logger.error(error_message)
            raise Exception(error_message) 
    except Exception as e:
        logger.error(
            f'Celery Task: Ошибка при отправке письма на почту {recipient_email}. '
            f'Попытка {self.request.retries + 1}/{self.max_retries}. Ошибка: {e}',
            exc_info=True
        )
        if self.request.retries >= self.max_retries:
            logger.critical(f"Celery Task: Все попытки отправки письма на {recipient_email} исчерпаны.")
        raise self.retry(exc=e) 
