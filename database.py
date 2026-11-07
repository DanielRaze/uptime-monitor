import sqlite3
from contextlib import closing
import os

DB_PATH = os.getenv("DB_PATH")


def init_db():
    with closing(sqlite3.connect(DB_PATH)) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY,
                url TEXT NOT NULL,
                status_code INTEGER,
                duration_ms INTEGER NOT NULL,
                error TEXT,
                checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()


def save_check(result):
    with closing(sqlite3.connect(DB_PATH)) as connection:
        cursor = connection.execute(
            """
            INSERT INTO checks (url, status_code, duration_ms, error)
            VALUES (?, ?, ?, ?)
            """,
            (
                result["url"],
                result["status_code"],
                result["duration_ms"],
                result["error"],
            ),
        )
        connection.commit()
        return cursor.lastrowid


def get_checks(limit):
    with closing(sqlite3.connect(DB_PATH)) as connection:
        connection.row_factory = sqlite3.Row

        cursor = connection.execute(
            """
            SELECT id, url, status_code, duration_ms, error, checked_at
            FROM checks
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )

        return [dict(row) for row in cursor.fetchall()]