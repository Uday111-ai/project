import hashlib
import logging
import secrets
import httpx
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

logger = logging.getLogger("uvicorn.error")


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


password_hasher = PasswordHasher()

# A hash of a fixed, never-used password, computed once at import time with
# the same Argon2 parameters as real user hashes. Used on `/login` when the
# identifier doesn't match any account, so an Argon2 verify runs on *every*
# request regardless of whether the user exists — closing the timing side
# channel that would otherwise let an attacker distinguish "no such user"
# (fast) from "wrong password" (slow, real verify) and enumerate accounts.
DUMMY_PASSWORD_HASH = password_hasher.hash(
    "fixed-dummy-value-never-a-real-password-timing-safety-only"
)

def generate_otp_code() -> str:
    """Cryptographically random 6-digit numeric code, zero-padded.

    Uses secrets (not random) since this is a security-sensitive code,
    same rationale as the existing token generation elsewhere in this file.
    """
    return f"{secrets.randbelow(1_000_000):06d}"

def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        password_hasher.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        # Covers InvalidHashError and anything else Argon2 might raise if
        # password_hash is malformed/corrupt/from a different algorithm.
        # Never let a bad hash turn into an unhandled 500 — treat it as a
        # failed verification and log for investigation.
        logger.exception(
            "Password verification raised an unexpected error "
            "(possibly a malformed stored hash)"
        )
        return False


def is_password_pwned(password: str, timeout: float = 2.0) -> bool:
    """Best-effort check against the HaveIBeenPwned breached-password list.

    Uses the k-anonymity range API: only the first 5 characters of the
    SHA-1 hash are sent, never the password itself or its full hash.
    Fails open (returns False) on any network/API error so an outage never
    blocks signup or password reset.
    """
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]

    try:
        response = httpx.get(
            f"https://api.pwnedpasswords.com/range/{prefix}",
            timeout=timeout,
            headers={"Add-Padding": "true"},
        )
        response.raise_for_status()
    except httpx.HTTPError:
        logger.warning("HaveIBeenPwned check unavailable; failing open")
        return False

    for line in response.text.splitlines():
        parts = line.split(":")
        if len(parts) != 2:
            continue
        candidate_suffix, count = parts
        if candidate_suffix.strip() == suffix and count.strip().isdigit():
            if int(count) > 0:
                return True

    return False
