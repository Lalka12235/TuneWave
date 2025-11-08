from fastapi import HTTPException
import smtplib
from app.config.settings import settings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.logger.log_config import logger


class EmailService:

    def send_email(
            self,
            recipient_email: str,
            username: str,
    ) -> bool:
        """
        Отправляет электронное письмо указанному получателю.
        
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
        subject = "Добро пожаловать в TuneWave!"
        body = f"""
        Привет, {username}!
        Спасибо за регистрацию в TuneWave. Мы рады видеть тебя в нашем музыкальном сообществе.
        Начни создавать комнаты и делиться музыкой с друзьями!
        С уважением,
        Команда TuneWave
        """
        logger.info(f"Celery Task: Попытка отправить письмо получателю: {recipient_email}")
        msg = MIMEMultipart()
        msg['From'] = settings.smtp.SMTP_FROM_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body,'plain'))

        try:
            server = smtplib.SMTP(settings.smtp.SMTP_HOST,settings.smtp.SMTP_PORT)
            server.starttls()
            cleaned_password = settings.smtp.SMTP_PASSWORD.replace(" ", "") 
            server.login(settings.smtp.SMTP_USER,cleaned_password)
            server.send_message(msg)
            server.quit()
        except smtplib.SMTPException as e:
            logger.error(f'Не получилось отправить сообщение на почту {recipient_email}.{e}')
            raise HTTPException(
                status_code=500,
                detail='Ошибка отправки email.'
            )