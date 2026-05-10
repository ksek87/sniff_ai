from __future__ import annotations
import json

from sqlalchemy import text
from services.db import get_engine

_initialized = False


def _ensure_table() -> None:
    global _initialized
    if _initialized:
        return
    with get_engine().connect() as conn:
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
    _initialized = True


def save_feedback(
    session_id: str,
    input_description: str,
    composition: dict,
    rating: int,
    comment: str = "",
) -> None:
    _ensure_table()
    with get_engine().connect() as conn:
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
    _ensure_table()
    with get_engine().connect() as conn:
        row = conn.execute(
            text("SELECT COUNT(*), AVG(rating) FROM feedback")
        ).one()
        total, avg_rating = row[0] or 0, row[1]

        dist_rows = conn.execute(
            text("SELECT rating, COUNT(*) FROM feedback GROUP BY rating")
        ).fetchall()

    distribution = {str(i): 0 for i in range(1, 6)}
    for rating, count in dist_rows:
        distribution[str(rating)] = count

    return {
        "total_feedback": total,
        "average_rating": round(float(avg_rating), 2) if avg_rating else None,
        "rating_distribution": distribution,
    }
