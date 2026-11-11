import hmac
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class AdmissionError(ValueError):
    def __init__(self, status):
        self.status = status
        super().__init__(status)


def authenticate(expected: str, supplied: str):
    if not expected or not hmac.compare_digest(expected, supplied):
        raise AdmissionError("unauthorized")


def reserve(path: Path, limit: int, *, day: str | None = None):
    """Atomic reservation, before GPU work. Failures consume a request; no automatic retry."""
    day = day or datetime.now(timezone.utc).date().isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path, timeout=5) as db:
        db.execute("CREATE TABLE IF NOT EXISTS usage (day TEXT PRIMARY KEY, count INTEGER NOT NULL)")
        db.execute("BEGIN IMMEDIATE")
        count = db.execute("SELECT count FROM usage WHERE day = ?", (day,)).fetchone()
        if count and count[0] >= limit:
            raise AdmissionError("quota_exhausted")
        db.execute("INSERT INTO usage VALUES (?, 1) ON CONFLICT(day) DO UPDATE SET count=count+1", (day,))
