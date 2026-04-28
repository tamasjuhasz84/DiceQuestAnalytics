"""SQLite helpers for analytics event logging."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path("data/dicequest.db")


def get_connection() -> sqlite3.Connection:
    """Create a connection to the SQLite database file."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def init_db() -> None:
    """Create logging tables if they do not exist yet."""
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                language TEXT,
                created_at TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                scene_id TEXT,
                data_json TEXT,
                created_at TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
            """
        )
        connection.commit()
