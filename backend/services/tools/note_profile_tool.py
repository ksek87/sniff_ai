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
                raw = json.load(f)
            # Lowercase-keyed index for O(1) case-insensitive lookup
            _profiles = {k.lower(): v for k, v in raw.items()}
        else:
            _profiles = {}
    return _profiles


def get_note_profile(notes: list[str]) -> dict:
    """Return volatility, family, and pairing data for each note.

    When multiple notes are requested the response also includes
    'shared_pairings' — the intersection of all their pairing sets.
    """
    profiles = _load()
    result: dict = {}
    for note in notes:
        profile = profiles.get(note.lower())
        if profile:
            result[note] = {**profile, "found": True}
        else:
            result[note] = {
                "volatility": "middle",
                "family": "unknown",
                "pairs_well_with": [],
                "found": False,
            }

    if len(notes) >= 2:
        found = [n for n in notes if result[n]["found"]]
        if len(found) >= 2:
            sets = [set(result[n].get("pairs_well_with", [])) for n in found]
            shared = sets[0].intersection(*sets[1:]) - set(notes)
            result["shared_pairings"] = sorted(shared)[:10]

    return result


def get_note_pairings(notes: list[str], limit: int = 10) -> list[str]:
    """Return notes that pair well with ALL of the given notes (intersection)."""
    profiles = _load()
    sets: list[set[str]] = []
    for note in notes:
        profile = profiles.get(note.lower())
        if profile:
            sets.append(set(profile.get("pairs_well_with", [])))
    if not sets:
        return []
    common = sets[0].intersection(*sets[1:]) if len(sets) > 1 else sets[0]
    common -= set(notes)
    return sorted(common)[:limit]
