from __future__ import annotations
import os

CANONICAL_FAMILIES: list[str] = [
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

NOTE_PROFILES_PATH: str = os.path.join(os.path.dirname(__file__), "../data/note_profiles.json")
