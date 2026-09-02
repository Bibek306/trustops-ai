from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from app.governance import is_currently_valid, version_key


def test_version_ordering():
    assert version_key("v10") > version_key("v2")
    assert version_key("3.2") > version_key("3.1")


def test_expired_evidence_is_not_valid():
    doc = SimpleNamespace(status="approved", effective_at=None, expires_at=datetime.now(timezone.utc) - timedelta(days=1))
    assert is_currently_valid(doc) is False


def test_future_evidence_is_not_valid():
    doc = SimpleNamespace(status="approved", effective_at=datetime.now(timezone.utc) + timedelta(days=1), expires_at=None)
    assert is_currently_valid(doc) is False
