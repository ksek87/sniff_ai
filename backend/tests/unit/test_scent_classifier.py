"""
Unit tests for ScentClassifier.
Only the no-model fallback and the concept mapping are exercised here —
training is slow and requires a dataset file.
"""
import pytest
from unittest.mock import patch
from services.nlp.scent_classifier import _concepts_to_family, _DEFAULT_FAMILY


# ── _concepts_to_family helper ────────────────────────────────────────────

def test_known_concept_maps_correctly():
    assert _concepts_to_family("['Floral', 'Rose']") == "Floral"


def test_first_matching_concept_wins():
    # "Woody" comes first and should win over "Floral"
    assert _concepts_to_family("['Woody', 'Floral']") == "Woody"


def test_unknown_concept_returns_none():
    assert _concepts_to_family("['UnknownTag']") is None


def test_malformed_string_returns_none():
    assert _concepts_to_family("not a list") is None


def test_empty_list_returns_none():
    assert _concepts_to_family("[]") is None


# ── ScentClassifier.predict fallback ─────────────────────────────────────

def test_predict_returns_default_when_no_model():
    with patch("services.nlp.scent_classifier.ScentClassifier._load_or_train"):
        from services.nlp.scent_classifier import ScentClassifier
        clf = ScentClassifier()
        clf._pipeline = None  # force the "no model" branch
        family, confidence = clf.predict("fresh morning citrus breeze")
        assert family == _DEFAULT_FAMILY
        assert confidence == 0.0


def test_predict_uses_pipeline_when_available():
    from unittest.mock import MagicMock
    import numpy as np

    mock_pipeline = MagicMock()
    mock_pipeline.predict_proba.return_value = [np.array([0.1, 0.1, 0.8])]
    mock_pipeline.classes_ = ["Floral", "Woody", "Fresh/Citrus"]

    with patch("services.nlp.scent_classifier.ScentClassifier._load_or_train"):
        from services.nlp.scent_classifier import ScentClassifier
        clf = ScentClassifier()
        clf._pipeline = mock_pipeline

    family, confidence = clf.predict("crisp lemon morning")
    assert family == "Fresh/Citrus"
    assert abs(confidence - 0.8) < 0.01
