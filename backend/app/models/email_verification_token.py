from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from app.database import Base


class EmailVerificationToken(Base):
    """Same shape/pattern as PasswordResetToken — a hashed, single-use,
    expiring token tied to a user, used for the email-verification flow.
    """

    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True)
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

    # "link" (default) sends a clickable verification URL; "otp" sends a
    # 6-digit code instead, stored hashed in otp_hash. token_hash is still
    # populated either way to satisfy the existing NOT NULL/UNIQUE
    # constraint, even though only the "link" flow actually looks it up.
    delivery_method = Column(String(10), nullable=False, default="link")
    otp_hash = Column(String(255), nullable=True)