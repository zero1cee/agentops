
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent.parent / "agentops.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS trace_events (
                event_id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                duration_ms REAL,
                timestamp TEXT NOT NULL
            )
            """
        )


def insert_event(event):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO trace_events (
                event_id, trace_id, event_type, name,
                status, duration_ms, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.trace_id,
                event.event_type,
                event.name,
                event.status,
                event.duration_ms,
                event.timestamp.isoformat(),
            ),
        )


def get_events(trace_id=None):
    with get_connection() as connection:
        if trace_id is None:
            rows = connection.execute(
                "SELECT * FROM trace_events ORDER BY timestamp"
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT * FROM trace_events
                WHERE trace_id = ?
                ORDER BY timestamp
                """,
                (trace_id,),
            ).fetchall()

    return [dict(row) for row in rows]


def get_event_by_id(event_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM trace_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()

    return dict(row) if row else None
