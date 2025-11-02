from infrastructure.celery.tasks import EmailService

def get_email_service() -> EmailService:
    return EmailService()