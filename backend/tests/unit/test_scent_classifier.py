"""
Unit tests for ScentClassifier.
Only the no-model fallback and the concept mapping are exercised here —
training is slow and requires a dataset file.
"""
import numpy as np
from unittest.mock import MagicMock, patch
from services.nlp.scent_classifier import _concepts_to_family, _DEFAULT_FAMILY


# ── _concepts_to_family helper ────────────────────────────────────────────

def test_known_concept_maps_correctly():
    assert _concepts_to_family("['Floral', 'Rose']") == "Floral"


def test_first_matching_concept_wins():
    assert _concepts_to_family("['Woody', 'Floral']") == "Woody"


def test_unknown_concept_returns_none():
    assert _concepts_to_family("['UnknownTag']") is None


def test_malformed_string_returns_none():
    assert _concepts_to_family("not a list") is None


def test_empty_list_returns_none():
    assert _concepts_to_family("[]") is None


# ── ScentClassifier.predict — no model loaded ─────────────────────────────

def test_predict_returns_default_when_no_model():
    with patch("services.nlp.scent_classifier.ScentClassifier._load"):
        from services.nlp.scent_classifier import ScentClassifier
        clf = ScentClassifier()
        # Both backends absent
        clf._setfit = None
        clf._clf = None
        family, confidence = clf.predict("fresh morning citrus breeze")
        assert family == _DEFAULT_FAMILY
        assert confidence == 0.0


# ── ScentClassifier.predict — legacy pkl path ─────────────────────────────

def test_predict_uses_sklearn_clf_when_available():
    mock_clf = MagicMock()
    mock_clf.predict_proba.return_value = [np.array([0.1, 0.1, 0.8])]
    mock_clf.classes_ = ["Floral", "Woody", "Fresh/Citrus"]

    mock_embedder_instance = MagicMock()
    mock_embedder_instance.encode.return_value = np.zeros(384).tolist()

    with (
        patch("services.nlp.scent_classifier.ScentClassifier._load"),
        patch("services.nlp.embedder.Embedder", return_value=mock_embedder_instance),
    ):
        from services.nlp.scent_classifier import ScentClassifier
        clf = ScentClassifier()
        clf._setfit = None
        clf._clf = mock_clf
        family, confidence = clf.predict("crisp lemon morning")
    assert family == "Fresh/Citrus"
    assert abs(confidence - 0.8) < 0.01


# ── ScentClassifier.predict — SetFit path ────────────────────────────────

def test_predict_uses_setfit_when_available():
    mock_setfit = MagicMock()
    mock_setfit.predict_proba.return_value = [np.array([0.05, 0.85, 0.1])]
    mock_setfit.labels = ["Floral", "Oriental", "Woody"]

    with patch("services.nlp.scent_classifier.ScentClassifier._load"):
        from services.nlp.scent_classifier import ScentClassifier
        clf = ScentClassifier()
        clf._setfit = mock_setfit
        clf._clf = None

    family, confidence = clf.predict("deep amber oud")

    assert family == "Oriental"
    assert abs(confidence - 0.85) < 0.01
