import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()


def send_reset_email(to_email: str, reset_link: str):
    message = EmailMessage()

    message["Subject"] = "Password Reset"
    message["From"] = os.getenv("SMTP_USERNAME")
    message["To"] = to_email

    message.set_content(
        f"""Hello,

We received a request to reset your password.

Click the link below to reset your password:

{reset_link}

This link will expire in 15 minutes.

If you did not request a password reset, you can ignore this email.

Regards,
AI Auth Team
"""
    )

    with smtplib.SMTP_SSL(
        os.getenv("SMTP_SERVER"),
        int(os.getenv("SMTP_PORT"))
    ) as server:

        server.login(
            os.getenv("SMTP_USERNAME"),
            os.getenv("SMTP_PASSWORD")
        )

        server.send_message(message)