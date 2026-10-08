from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    # Stored with whatever casing the user signed up with, so it displays
    # the way they typed it. Uniqueness and lookups are case-insensitive —
    # enforced and indexed via the expression indexes below, not via a
    # plain column-level unique=True.
    username = Column(String(30), nullable=False)
    email = Column(String(255), nullable=False)

    password_hash = Column(String(255), nullable=False)
    token_version = Column(Integer, default=0, nullable=False)

    email_verified = Column(Boolean, default=False, nullable=False)

    # Per-account brute-force lockout (on top of the existing per-IP rate
    # limiting on /login, which alone doesn't stop a distributed attack
    # against one specific account).
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False,
    )


# Case-insensitive uniqueness, enforced at the DB level (not just checked
# in application code) so a race between two concurrent signups with
# different casing of the same name/email still can't both succeed.
Index("ix_users_username_lower", func.lower(User.username), unique=True)
Index("ix_users_email_lower", func.lower(User.email), unique=True)
