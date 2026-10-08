"""Centralized, env-driven configuration.

Keeping these reads in one place (instead of scattered `os.getenv()` calls)
makes the defaults easy to audit and avoids subtly different fallbacks in
different modules.
"""
import os

from dotenv import load_dotenv

load_dotenv()


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError:
        return default


FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Whether an account must click the emailed verification link before it can
# log in. Flip to false only for environments where that friction is
# unacceptable (e.g. some internal tools) — see README for the trade-off.
REQUIRE_EMAIL_VERIFICATION = _bool_env("REQUIRE_EMAIL_VERIFICATION", True)

# Opt-in Have I Been Pwned (k-anonymity) check on signup/reset passwords.
# Off by default: it's an external network call on the request path, and
# some environments (offline dev, restricted egress) can't reach it.
CHECK_PASSWORD_PWNED = _bool_env("CHECK_PASSWORD_PWNED", False)

# Per-account lockout (in addition to the existing per-IP rate limiting).
ACCOUNT_LOCKOUT_MAX_ATTEMPTS = _int_env("ACCOUNT_LOCKOUT_MAX_ATTEMPTS", 5)
ACCOUNT_LOCKOUT_DURATION_MINUTES = _int_env("ACCOUNT_LOCKOUT_DURATION_MINUTES", 15)

PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = _int_env(
    "PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", 15
)
EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES = _int_env(
    "EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES", 60 * 24
)

# Dev/test convenience: auto-create tables on startup via
# Base.metadata.create_all(). Production schema changes should go through
# Alembic instead (see migrations/) — set this to "false" once Alembic owns
# the schema (already done in render.yaml).
DB_AUTO_CREATE_TABLES = _bool_env("DB_AUTO_CREATE_TABLES", True)

# Backing store for slowapi's rate limiter. Empty/unset -> in-memory,
# correct only for a single backend process. Set to a Redis URL
# (e.g. "redis://localhost:6379") once running more than one instance
# behind a load balancer, so limits are shared across processes instead
# of each one tracking its own separate counts.
RATE_LIMIT_STORAGE_URI = os.getenv("RATE_LIMIT_STORAGE_URI", "").strip() or None