from __future__ import annotations

_VALID_FAMILIES = {
    "Floral", "Oriental", "Woody", "Fresh/Citrus",
    "Fougère", "Chypre", "Gourmand", "Aquatic/Marine", "Earthy/Mossy",
}

_MAX_NOTES_PER_TIER = 6
_MIN_NOTES_PER_TIER = 1


def validate_composition(composition: dict) -> dict:
    errors: list[str] = []

    top = composition.get("top_notes", [])
    middle = composition.get("middle_notes", [])
    base = composition.get("base_notes", [])

    all_notes = top + middle + base
    if not all_notes:
        errors.append("Composition has no notes.")

    total = sum(n.get("percentage", 0) for n in all_notes)
    if abs(total - 100) > 1:
        errors.append(f"Percentages sum to {total}%, expected 100%.")

    for tier_name, tier in [("top", top), ("middle", middle), ("base", base)]:
        count = len(tier)
        if count < _MIN_NOTES_PER_TIER:
            errors.append(f"{tier_name} tier has no notes.")
        if count > _MAX_NOTES_PER_TIER:
            errors.append(f"{tier_name} tier has {count} notes (max {_MAX_NOTES_PER_TIER}).")

    family = composition.get("scent_family", "")
    if family and family not in _VALID_FAMILIES:
        errors.append(f"Unknown scent family: {family!r}.")

    similar = composition.get("similar_fragrances", [])
    if len(similar) > 5:
        errors.append(f"Too many similar fragrances: {len(similar)} (max 5).")

    return {"valid": len(errors) == 0, "errors": errors}
