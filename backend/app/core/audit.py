"""Structured audit logging for security-relevant events.

Emits one JSON line per event via the standard `logging` module (so it
flows through whatever log aggregation the deployment already has, e.g.
Render's log stream). Deliberately takes keyword fields rather than a
free-form message so callers can't accidentally interpolate a secret into
a string.

NEVER pass passwords, raw tokens, token hashes, or full JWTs as fields —
only IDs, emails, booleans, and short reason codes.
"""
import json
import logging
import time

audit_logger = logging.getLogger("auth.audit")


def log_event(event_type: str, **fields) -> None:
    record = {"event": event_type, "ts": round(time.time(), 3), **fields}
    audit_logger.info(json.dumps(record, default=str, sort_keys=True))
