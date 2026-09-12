import logging
import threading

from flask import current_app
from flask_mail import Mail, Message

mail = Mail()
logger = logging.getLogger(__name__)


def init_mail(app):
    mail.init_app(app)


def _send_async(app, message):
    try:
        with app.app_context():
            mail.send(message)
        logger.info("Email sent", extra={"subject": message.subject, "recipients": message.recipients})
    except Exception as exc:
        logger.error("Email send failed: %s", str(exc), exc_info=True)


def send_email(subject, recipients, text_body, html_body=None, reply_to=None):
    smtp_server = (current_app.config.get("MAIL_SERVER") or "").strip()
    smtp_username = (current_app.config.get("MAIL_USERNAME") or "").strip()
    smtp_password = (current_app.config.get("MAIL_PASSWORD") or "").strip()
    sender = (current_app.config.get("MAIL_DEFAULT_SENDER") or smtp_username).strip()

    if not smtp_server or not smtp_username or not smtp_password:
        return False, "Email is not configured on the server."
    if not recipients:
        return False, "No recipient email addresses configured."
    if not sender:
        return False, "No sender email address configured."

    try:
        message = Message(subject=subject, sender=sender, recipients=recipients, reply_to=reply_to)
        message.body = text_body
        if html_body:
            message.html = html_body

        if current_app.config.get("MAIL_SEND_SYNC", False):
            mail.send(message)
        else:
            app_obj = current_app._get_current_object()
            thread = threading.Thread(target=_send_async, args=(app_obj, message), daemon=True)
            thread.start()

        return True, ""
    except Exception as exc:
        logger.error("Email send failed: %s", str(exc), exc_info=True)
        return False, "Unable to send email right now."
