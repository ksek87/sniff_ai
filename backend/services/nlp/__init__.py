from .note_extractor import NoteExtractor
from .embedder import Embedder
from .scent_classifier import ScentClassifier

_note_extractor = NoteExtractor()
_embedder = Embedder()
_classifier = ScentClassifier()

CANONICAL_FAMILIES = [
    "Floral",
    "Oriental",
    "Woody",
    "Fresh/Citrus",
    "Fougère",
    "Chypre",
    "Gourmand",
    "Aquatic/Marine",
    "Earthy/Mossy",
]


def preprocess(description: str) -> dict:
    detected_notes = _note_extractor.extract(description)
    family, confidence = _classifier.predict(description)
    return {
        "description": description,
        "detected_notes": detected_notes,
        "predicted_family": family,
        "family_confidence": round(confidence, 3),
    }


def get_all_notes() -> list:
    return _note_extractor.all_notes


def get_all_families() -> list:
    return CANONICAL_FAMILIES
