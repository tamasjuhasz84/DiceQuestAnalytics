"""Event logging helpers for SQLite analytics storage."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.models.database import get_connection


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_session_log(session_id: str, language: str = "hu") -> None:
    """Insert a game session row for analytics."""
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO sessions (id, language, created_at)
            VALUES (?, ?, ?)
            """,
            (session_id, language, _now_iso()),
        )
        connection.commit()


def log_event(
    session_id: str,
    event_type: str,
    scene_id: str | None = None,
    data: dict[str, Any] | None = None,
) -> None:
    """Insert an event row for analytics."""
    payload = json.dumps(data or {}, ensure_ascii=False)

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO events (session_id, event_type, scene_id, data_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, event_type, scene_id, payload, _now_iso()),
        )
        connection.commit()
