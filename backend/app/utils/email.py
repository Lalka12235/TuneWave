from fastapi import HTTPException
import smtplib
from app.config.settings import settings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.logger.log_config import logger


async def send_email(
        reciepint_email: str,
        subject: str,
        body: str,
) -> bool:
    """
    Отправляет электронное письмо указанному получателю.

    Args:
        reciepint_email (str): Адрес электронной почты получателя.
        subject (str): Тема письма.
        body (str): Тело письма (может быть HTML или обычным текстом).

    Returns:
        bool: True, если письмо отправлено успешно, False в противном случае.
    """
    msg = MIMEMultipart()
    msg['From'] = settings.SMTP_FROM_EMAIL
    msg['To'] = reciepint_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body,'plain'))

    try:
        server = smtplib.SMTP(settings.SMTP_HOST,settings.SMTP_PORT)
        server.starttls()
        cleaned_password = settings.SMTP_PASSWORD.replace(" ", "") 
        server.login(settings.SMTP_USER,cleaned_password)
        server.send_message(msg)
        server.quit()
    except smtplib.SMTPException as e:
        logger.error(f'Не получилось отправить сообщение на почту {reciepint_email}.{e}')
        raise HTTPException(
            status_code=500,
            detail=f'Ошибка отправки email.'
        )