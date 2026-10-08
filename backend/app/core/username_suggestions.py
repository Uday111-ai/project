"""Generates candidate username variations for the /check-username
endpoint. Pure string logic — no DB access here; the route does one
batched query against the candidates this returns.
"""
import random
import string

MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 30

_PREFIXES = ["real_", "the_", "im_"]
_SUFFIXES = ["_official", "_real", "_hq"]


def _random_digits(length: int) -> str:
    return "".join(random.choices(string.digits, k=length))


def _valid_or_none(candidate: str) -> str | None:
    if MIN_USERNAME_LENGTH <= len(candidate) <= MAX_USERNAME_LENGTH:
        return candidate
    return None


def generate_candidates(username: str, count: int = 8) -> list[str]:
    """Return up to `count` distinct candidate usernames derived from
    `username`. Each candidate independently satisfies the same 3-30
    character bound signup enforces (a candidate that would violate it —
    e.g. adding a suffix to an already-30-char username — is dropped
    rather than truncated, since a truncated suggestion could collide
    with something unrelated). The original username itself (case-
    insensitively) is never included. Order is shuffled — these are
    offered as alternatives, not a ranked/deterministic sequence.
    """
    candidates: set[str] = set()
    username_lower = username.lower()

    def add(value: str) -> None:
        valid = _valid_or_none(value)
        if valid and valid.lower() != username_lower:
            candidates.add(valid)

    # Append a random 2-4 digit number (a few draws, since collisions
    # between draws are possible and we want variety in the final set).
    for _ in range(3):
        add(f"{username}{_random_digits(random.randint(2, 4))}")

    # Underscore variants.
    add(f"{username}_{_random_digits(random.randint(2, 3))}")
    add(f"{username}_")

    # Short prefix / suffix.
    add(random.choice(_PREFIXES) + username)
    add(username + random.choice(_SUFFIXES))

    # Combine a prefix with digits.
    add(random.choice(_PREFIXES) + username + _random_digits(2))

    result = list(candidates)
    random.shuffle(result)
    return result[:count]
