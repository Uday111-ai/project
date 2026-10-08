from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from app.database import Base


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True)
    # index=True: this is a foreign key, but Postgres does not auto-index
    # FK columns. Without it, lookups filtering by user_id (including the
    # cleanup delete in /delete-account) sequential-scan as the table grows.
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash = Column(String(255), nullable=False, unique=True)

    expires_at = Column(DateTime, nullable=False)

    used = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False,
    )

    # See email_verification_token.py for delivery_method / otp_hash notes.
    delivery_method = Column(String(10), nullable=False, default="link")
    otp_hash = Column(String(255), nullable=True)