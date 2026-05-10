from __future__ import annotations
import logging
import os

from sqlalchemy import event, text, create_engine, Engine

logger = logging.getLogger(__name__)

_DB_PATH = os.path.join(os.path.dirname(__file__), "../data/feedback.db")
_DB_URL = f"sqlite:///{_DB_PATH}"

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
        logger.info("SQLite database: %s", _DB_PATH)
        engine = create_engine(_DB_URL, connect_args={"check_same_thread": False})

        @event.listens_for(engine, "connect")
        def _set_pragmas(dbapi_conn, _record):
            cursor = dbapi_conn.cursor()
            # WAL mode: readers don't block writers; one writer at a time queues
            cursor.execute("PRAGMA journal_mode=WAL")
            # 30 s busy timeout: retry on lock instead of immediately failing
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.close()

        _engine = engine
    return _engine
