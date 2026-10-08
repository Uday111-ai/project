"""Deletes expired or already-used password-reset and email-verification
tokens.

These tables grow unbounded otherwise — every forgot-password/signup
request adds a row, and nothing ever removed old ones. This is meant to
run on a schedule (a Render Cron Job, or a plain crontab entry) rather
than in the request path. Safe to run repeatedly / concurrently.

Usage:
    python scripts/cleanup_expired_tokens.py
"""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal  # noqa: E402
from app.models.email_verification_token import EmailVerificationToken  # noqa: E402
from app.models.password_reset_token import PasswordResetToken  # noqa: E402


def main() -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db = SessionLocal()
    try:
        deleted_reset = (
            db.query(PasswordResetToken)
            .filter(
                (PasswordResetToken.expires_at < now)
                | (PasswordResetToken.used == True)  # noqa: E712
            )
            .delete(synchronize_session=False)
        )
        deleted_verify = (
            db.query(EmailVerificationToken)
            .filter(
                (EmailVerificationToken.expires_at < now)
                | (EmailVerificationToken.used == True)  # noqa: E712
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        print(
            f"Cleanup complete: removed {deleted_reset} password-reset "
            f"token(s) and {deleted_verify} email-verification token(s)."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
