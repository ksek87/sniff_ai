"""
Unit tests for the feedback persistence layer.

Each test gets a fresh SQLite database in a temp directory so tests are
fully isolated and don't touch the real data/feedback.db file.
"""
import pytest


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    """Point the shared db module at a fresh temp SQLite for each test."""
    import services.db as _db
    import services.feedback as _fb
    db_path = tmp_path / "test_feedback.db"
    monkeypatch.setattr(_db, "_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setattr(_db, "_engine", None)
    monkeypatch.setattr(_fb, "_initialized", False)


def test_metrics_empty_database():
    from services.feedback import get_metrics
    metrics = get_metrics()
    assert metrics["total_feedback"] == 0
    assert metrics["average_rating"] is None
    assert all(v == 0 for v in metrics["rating_distribution"].values())


def test_save_and_count_feedback():
    from services.feedback import save_feedback, get_metrics
    save_feedback(
        session_id="s1",
        input_description="pine forest",
        composition={"name": "Forest Accord"},
        rating=4,
        comment="Lovely",
    )
    metrics = get_metrics()
    assert metrics["total_feedback"] == 1
    assert metrics["average_rating"] == 4.0


def test_average_rating_multiple_entries():
    from services.feedback import save_feedback, get_metrics
    for rating in [2, 4, 5]:
        save_feedback("s1", "desc", {}, rating)
    metrics = get_metrics()
    assert metrics["total_feedback"] == 3
    assert abs(metrics["average_rating"] - round((2 + 4 + 5) / 3, 2)) < 0.01


def test_rating_distribution():
    from services.feedback import save_feedback, get_metrics
    for rating in [1, 3, 3, 5]:
        save_feedback("s1", "desc", {}, rating)
    dist = get_metrics()["rating_distribution"]
    assert dist["1"] == 1
    assert dist["2"] == 0
    assert dist["3"] == 2
    assert dist["4"] == 0
    assert dist["5"] == 1


def test_composition_serialised_as_json():
    from services.feedback import save_feedback, get_metrics
    save_feedback("s1", "desc", {"name": "Test", "notes": ["Rose"]}, rating=3)
    # If composition serialisation fails, save_feedback raises; success = no error
    assert get_metrics()["total_feedback"] == 1


def test_empty_comment_is_optional():
    from services.feedback import save_feedback, get_metrics
    save_feedback("s1", "desc", {}, rating=5)  # no comment arg
    assert get_metrics()["total_feedback"] == 1
