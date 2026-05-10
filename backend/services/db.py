from __future__ import annotations
import os

from sqlalchemy import create_engine, Engine

_DB_PATH = os.path.join(os.path.dirname(__file__), "../data/feedback.db")
_DB_URL = f"sqlite:///{_DB_PATH}"

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
        _engine = create_engine(_DB_URL, connect_args={"check_same_thread": False})
    return _engine
