from __future__ import annotations
import json
import os

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
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    input_description TEXT NOT NULL,
                    composition_json TEXT NOT NULL,
                    rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                    comment TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
    return _engine


def save_feedback(
    session_id: str,
    input_description: str,
    composition: dict,
    rating: int,
    comment: str = "",
) -> None:
    engine = _get_engine()
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO feedback (session_id, input_description, composition_json, rating, comment)
                VALUES (:session_id, :description, :composition, :rating, :comment)
            """),
            {
                "session_id": session_id,
                "description": input_description,
                "composition": json.dumps(composition),
                "rating": rating,
                "comment": comment,
            },
        )
        conn.commit()


def get_metrics() -> dict:
    engine = _get_engine()
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM feedback")).scalar() or 0
        avg_rating = conn.execute(text("SELECT AVG(rating) FROM feedback")).scalar()
        distribution = {
            str(i): conn.execute(
                text("SELECT COUNT(*) FROM feedback WHERE rating = :r"), {"r": i}
            ).scalar() or 0
            for i in range(1, 6)
        }
    return {
        "total_feedback": total,
        "average_rating": round(float(avg_rating), 2) if avg_rating else None,
        "rating_distribution": distribution,
    }
