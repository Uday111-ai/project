import os
import sys

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test.db")

# These must be set *before* anything under app/ is imported, since
# app.core.jwt and app.core.config read the environment at import time.
os.environ.setdefault(
    "JWT_SECRET_KEY", "test-only-secret-key-not-for-production-use-0123456789"
)
# Default to a throwaway SQLite file for fast, dependency-free unit tests.
# Set TEST_DATABASE_URL to point this same suite at a real PostgreSQL
# instance instead, to catch Postgres-specific behavior (case-insensitive
# uniqueness via functional indexes, schema quirks) that SQLite can't
# reproduce. Never reuses the app's own DATABASE_URL, so a mistyped env
# var can't accidentally point tests at real data.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", f"sqlite:///{TEST_DB_PATH}"
)
os.environ["DB_AUTO_CREATE_TABLES"] = "true"
os.environ["REQUIRE_EMAIL_VERIFICATION"] = "true"
os.environ["CHECK_PASSWORD_PWNED"] = "false"
os.environ["ACCOUNT_LOCKOUT_MAX_ATTEMPTS"] = "3"
os.environ["ACCOUNT_LOCKOUT_DURATION_MINUTES"] = "15"
os.environ["FRONTEND_URL"] = "http://localhost:3000"
# SMTP_* deliberately left unset: app/core/email.py no-ops (logs and
# returns) instead of trying to reach a real SMTP server.

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models.email_verification_token import EmailVerificationToken  # noqa: E402
from app.models.password_reset_token import PasswordResetToken  # noqa: E402
from app.models.user import User  # noqa: E402

# Disable per-IP rate limiting for tests — several tests deliberately send
# more requests to one endpoint (e.g. testing lockout) than the production
# limits would allow.
app.state.limiter.enabled = False


@pytest.fixture(autouse=True)
def clean_db():
    yield
    db = SessionLocal()
    try:
        db.query(PasswordResetToken).delete()
        db.query(EmailVerificationToken).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
