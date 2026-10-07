import logging
import smtplib
from email.message import EmailMessage
from app.core.config import settings

log = logging.getLogger("jeevanai.notify")


def send_email(to: str, subject: str, body: str) -> bool:
    """Sends an email if SMTP_HOST is configured. Never raises."""
    if not settings.smtp_host or not to:
        return False
    try:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = settings.smtp_from or settings.smtp_user, to, subject
        msg.set_content(body)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as s:
            s.starttls()
            if settings.smtp_user:
                s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)
        return True
    except Exception as e:  # noqa: BLE001
        log.warning("Email failed: %s", e)
        return False
