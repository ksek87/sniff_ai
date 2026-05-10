from __future__ import annotations
import threading

from .note_extractor import NoteExtractor
from .embedder import Embedder
from .scent_classifier import ScentClassifier
from services.config import CANONICAL_FAMILIES

_lock = threading.Lock()
_note_extractor: NoteExtractor | None = None
_classifier: ScentClassifier | None = None


def _get_note_extractor() -> NoteExtractor:
    global _note_extractor
    if _note_extractor is None:
        with _lock:
            if _note_extractor is None:
                _note_extractor = NoteExtractor()
    return _note_extractor


def _get_classifier() -> ScentClassifier:
    global _classifier
    if _classifier is None:
        with _lock:
            if _classifier is None:
                _classifier = ScentClassifier()
    return _classifier


def preprocess(description: str) -> dict:
    detected_notes = _get_note_extractor().extract(description)
    family, confidence = _get_classifier().predict(description)
    return {
        "description": description,
        "detected_notes": detected_notes,
        "predicted_family": family,
        "family_confidence": round(confidence, 3),
    }


def get_all_notes() -> list:
    return _get_note_extractor().all_notes


def get_all_families() -> list:
    return CANONICAL_FAMILIES
