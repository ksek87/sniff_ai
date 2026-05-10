from __future__ import annotations
import json
import os
import uuid

from sqlalchemy import create_engine, text

_DB_PATH = os.path.join(os.path.dirname(__file__), "../data/feedback.db")
_DB_URL = f"sqlite:///{_DB_PATH}"

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
        _engine = create_engine(_DB_URL, connect_args={"check_same_thread": False})
        with _engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS shared_fragrances (
                    token TEXT PRIMARY KEY,
                    input_description TEXT NOT NULL,
                    composition_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
    return _engine


def save_share(input_description: str, composition: dict) -> str:
    token = uuid.uuid4().hex
    engine = _get_engine()
    with engine.connect() as conn:
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
    engine = _get_engine()
    with engine.connect() as conn:
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
