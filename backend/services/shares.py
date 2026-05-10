from __future__ import annotations
import json
import uuid

from sqlalchemy import text
from services.db import get_engine

_initialized = False


def _ensure_table() -> None:
    global _initialized
    if _initialized:
        return
    with get_engine().connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS shared_fragrances (
                token TEXT PRIMARY KEY,
                input_description TEXT NOT NULL,
                composition_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
    _initialized = True


def save_share(input_description: str, composition: dict) -> str:
    _ensure_table()
    token = uuid.uuid4().hex
    with get_engine().connect() as conn:
        conn.execute(
            text("DELETE FROM shared_fragrances WHERE created_at < datetime('now', '-30 days')")
        )
        conn.execute(
            text("""
                INSERT INTO shared_fragrances (token, input_description, composition_json)
                VALUES (:token, :description, :composition)
            """),
            {
                "token": token,
                "description": input_description,
                "composition": json.dumps(composition),
            },
        )
        conn.commit()
    return token


def get_share(token: str) -> dict | None:
    _ensure_table()
    with get_engine().connect() as conn:
        row = conn.execute(
            text("""
                SELECT input_description, composition_json
                FROM shared_fragrances
                WHERE token = :token
            """),
            {"token": token},
        ).one_or_none()
    if row is None:
        return None
    return {
        "input_description": row[0],
        "composition": json.loads(row[1]),
    }
