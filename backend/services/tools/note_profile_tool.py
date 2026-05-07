from __future__ import annotations
import json
import os

from services.config import NOTE_PROFILES_PATH as _PROFILES_PATH

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
        if profile:
            result[note] = {**profile, "found": True}
        else:
            result[note] = {
                "volatility": "middle",
                "family": "unknown",
                "pairs_well_with": [],
                "found": False,
            }
    return result


def get_note_pairings(notes: list[str], limit: int = 10) -> list[str]:
    """Return notes that pair well with ALL of the given notes (intersection)."""
    profiles = _load()
    sets: list[set[str]] = []
    for note in notes:
        profile = profiles.get(note) or profiles.get(note.title()) or profiles.get(note.lower())
        if profile:
            sets.append(set(profile.get("pairs_well_with", [])))
    if not sets:
        return []
    common = sets[0].intersection(*sets[1:]) if len(sets) > 1 else sets[0]
    # Exclude the input notes themselves from suggestions
    common -= set(notes)
    return sorted(common)[:limit]
