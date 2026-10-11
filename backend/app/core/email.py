import logging
import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("uvicorn.error")


def _send_email(to_email: str, subject: str, body: str) -> None:
    """Send a single plain-text email. Never raises — logs and swallows
    failures instead, since these are called from FastAPI BackgroundTasks
    where an uncaught exception would only show up in server logs anyway,
    and callers on the request path have already returned a response by
    the time this runs.
    """
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_server or not smtp_port or not smtp_username:
        logger.error("SMTP is not configured; skipping email send to %s", to_email)
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = smtp_username
    message["To"] = to_email
    message.set_content(body)

    try:
        with smtplib.SMTP_SSL(smtp_server, int(smtp_port)) as server:
            server.login(smtp_username, smtp_password)
            server.send_message(message)
    except Exception:
        logger.exception("Failed to send email to %s", to_email)


def send_reset_email(to_email: str, reset_link: str) -> None:
    body = f"""Hello,

We received a request to reset your password.

Click the link below to reset your password:

{reset_link}

This link will expire in 15 minutes.

If you did not request a password reset, you can ignore this email.

Regards,
AI Auth Team
"""
    _send_email(to_email, "Password Reset", body)


def send_verification_email(to_email: str, verify_link: str) -> None:
    body = f"""Hello,

Thanks for signing up! Please verify your email address by clicking the
link below:

{verify_link}

This link will expire in 24 hours.

If you did not create this account, you can ignore this email.

Regards,
AI Auth Team
"""
    _send_email(to_email, "Verify your email address", body)


def send_reset_otp_email(to_email: str, otp_code: str) -> None:
    body = f"""Hello,

We received a request to reset your password.

Your password reset code is:

{otp_code}

This code will expire in 15 minutes.

If you did not request a password reset, you can ignore this email.

Regards,
AI Auth Team
"""
    _send_email(to_email, "Your password reset code", body)


def send_verification_otp_email(to_email: str, otp_code: str) -> None:
    body = f"""Hello,

Thanks for signing up! Your email verification code is:

{otp_code}

This code will expire in 24 hours.

If you did not create this account, you can ignore this email.

Regards,
AI Auth Team
"""
    _send_email(to_email, "Your verification code", body)