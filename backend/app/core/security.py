from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import secrets


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        password_hasher.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False