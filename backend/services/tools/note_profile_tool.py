from __future__ import annotations
import json
import os

_PROFILES_PATH = os.path.join(os.path.dirname(__file__), "../../data/note_profiles.json")

_profiles: dict | None = None


def _load() -> dict:
    global _profiles
    if _profiles is None:
        if os.path.exists(_PROFILES_PATH):
            with open(_PROFILES_PATH) as f:
                _profiles = json.load(f)
        else:
            _profiles = {}
    return _profiles


def get_note_profile(notes: list[str]) -> dict[str, dict]:
    profiles = _load()
    result: dict[str, dict] = {}
    for note in notes:
        profile = profiles.get(note) or profiles.get(note.title()) or profiles.get(note.lower())
        result[note] = profile or {
            "volatility": "middle",
            "family": "unknown",
            "pairs_well_with": [],
        }
    return result
