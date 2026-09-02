import re
from datetime import datetime, timezone


def version_key(version: str) -> tuple:
    nums = re.findall(r"\d+", version or "")
    return tuple(int(x) for x in nums) if nums else (0,)


def is_currently_valid(doc: object, at: datetime | None = None) -> bool:
    at = at or datetime.now(timezone.utc)

    effective_at = getattr(doc, "effective_at", None)
    expires_at = getattr(doc, "expires_at", None)

    if effective_at and effective_at.tzinfo is None:
        effective_at = effective_at.replace(tzinfo=timezone.utc)

    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if effective_at and effective_at > at:
        return False

    if expires_at and expires_at <= at:
        return False

    return True