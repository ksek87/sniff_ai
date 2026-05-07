"""
Unit tests for services/nlp/__init__.py — preprocess(), get_all_notes(), get_all_families().
Module-level singletons are patched so no filesystem or model I/O occurs.
"""
from unittest.mock import patch, MagicMock

import pytest

from services.config import CANONICAL_FAMILIES


# ── preprocess() ────────────────────────────────────────────────────────────

def test_preprocess_returns_required_keys():
    with (
        patch("services.nlp._note_extractor") as mock_ne,
        patch("services.nlp._classifier") as mock_clf,
    ):
        mock_ne.extract.return_value = []
        mock_clf.predict.return_value = ("Woody", 0.75)
        from services.nlp import preprocess
        result = preprocess("autumn forest")
    for key in ("description", "detected_notes", "predicted_family", "family_confidence"):
        assert key in result, f"Missing key: {key}"


def test_preprocess_passes_description_through():
    with (
        patch("services.nlp._note_extractor") as mock_ne,
        patch("services.nlp._classifier") as mock_clf,
    ):
        mock_ne.extract.return_value = []
        mock_clf.predict.return_value = ("Floral", 0.9)
        from services.nlp import preprocess
        result = preprocess("fresh rose petals")
    assert result["description"] == "fresh rose petals"


def test_preprocess_includes_detected_notes():
    with (
        patch("services.nlp._note_extractor") as mock_ne,
        patch("services.nlp._classifier") as mock_clf,
    ):
        mock_ne.extract.return_value = ["Rose", "Jasmine"]
        mock_clf.predict.return_value = ("Floral", 0.88)
        from services.nlp import preprocess
        result = preprocess("rose and jasmine")
    assert result["detected_notes"] == ["Rose", "Jasmine"]


def test_preprocess_includes_predicted_family():
    with (
        patch("services.nlp._note_extractor") as mock_ne,
        patch("services.nlp._classifier") as mock_clf,
    ):
        mock_ne.extract.return_value = []
        mock_clf.predict.return_value = ("Oriental", 0.72)
        from services.nlp import preprocess
        result = preprocess("warm spicy amber")
    assert result["predicted_family"] == "Oriental"


def test_preprocess_rounds_family_confidence():
    with (
        patch("services.nlp._note_extractor") as mock_ne,
        patch("services.nlp._classifier") as mock_clf,
    ):
        mock_ne.extract.return_value = []
        mock_clf.predict.return_value = ("Woody", 0.123456)
        from services.nlp import preprocess
        result = preprocess("cedar")
    assert result["family_confidence"] == round(0.123456, 3)


# ── get_all_notes() ─────────────────────────────────────────────────────────

def test_get_all_notes_returns_list():
    with patch("services.nlp._note_extractor") as mock_ne:
        mock_ne.all_notes = ["Bergamot", "Cedar", "Oud"]
        from services.nlp import get_all_notes
        result = get_all_notes()
    assert isinstance(result, list)


def test_get_all_notes_returns_extractor_notes():
    with patch("services.nlp._note_extractor") as mock_ne:
        mock_ne.all_notes = ["Rose", "Vetiver"]
        from services.nlp import get_all_notes
        result = get_all_notes()
    assert result == ["Rose", "Vetiver"]


# ── get_all_families() ──────────────────────────────────────────────────────

def test_get_all_families_returns_canonical_families():
    from services.nlp import get_all_families
    assert get_all_families() == CANONICAL_FAMILIES


def test_get_all_families_contains_expected_values():
    from services.nlp import get_all_families
    families = get_all_families()
    for expected in ("Floral", "Woody", "Oriental", "Fresh/Citrus", "Gourmand"):
        assert expected in families, f"Missing family: {expected}"


def test_get_all_families_returns_list():
    from services.nlp import get_all_families
    assert isinstance(get_all_families(), list)
