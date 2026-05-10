"""
Unit tests for get_note_profile and get_note_pairings.
"""
import json
import pytest
from unittest.mock import patch


_SAMPLE_PROFILES = {
    "Bergamot": {"volatility": "top", "family": "Fresh/Citrus", "pairs_well_with": ["Lemon", "Cedar"]},
    "Rose": {"volatility": "middle", "family": "Floral", "pairs_well_with": ["Jasmine", "Cedar"]},
    "Musk": {"volatility": "base", "family": "Oriental", "pairs_well_with": ["Amber"]},
}


@pytest.fixture()
def patched_profiles():
    with patch("services.tools.note_profile_tool._profiles", _SAMPLE_PROFILES):
        yield


def test_exact_case_match(patched_profiles):
    from services.tools.note_profile_tool import get_note_profile
    result = get_note_profile(["Bergamot"])
    assert result["Bergamot"]["volatility"] == "top"
    assert result["Bergamot"]["family"] == "Fresh/Citrus"


def test_title_case_fallback(patched_profiles):
    from services.tools.note_profile_tool import get_note_profile
    result = get_note_profile(["bergamot"])  # lowercase lookup
    assert result["bergamot"]["volatility"] == "top"


def test_multiple_notes(patched_profiles):
    from services.tools.note_profile_tool import get_note_profile
    result = get_note_profile(["Bergamot", "Rose", "Musk"])
    assert result["Rose"]["volatility"] == "middle"
    assert result["Musk"]["volatility"] == "base"
    assert "shared_pairings" in result  # merged pairings included for multi-note calls


def test_unknown_note_returns_middle_default(patched_profiles):
    from services.tools.note_profile_tool import get_note_profile
    result = get_note_profile(["UnknownIngredient"])
    profile = result["UnknownIngredient"]
    assert profile["volatility"] == "middle"
    assert profile["family"] == "unknown"
    assert profile["pairs_well_with"] == []


def test_empty_profiles_falls_back_gracefully():
    with patch("services.tools.note_profile_tool._profiles", {}):
        from services.tools.note_profile_tool import get_note_profile
        result = get_note_profile(["Bergamot"])
        assert result["Bergamot"]["volatility"] == "middle"


def test_empty_note_list(patched_profiles):
    from services.tools.note_profile_tool import get_note_profile
    assert get_note_profile([]) == {}


# ── shared_pairings ───────────────────────────────────────────────────────────

def test_shared_pairings_is_intersection(patched_profiles):
    """get_note_profile with multiple notes includes shared_pairings = intersection."""
    from services.tools.note_profile_tool import get_note_profile
    # Bergamot: ["Lemon", "Cedar"], Rose: ["Jasmine", "Cedar"] → intersection = ["Cedar"]
    result = get_note_profile(["Bergamot", "Rose"])
    assert result["shared_pairings"] == ["Cedar"]


def test_shared_pairings_excludes_input_notes(patched_profiles):
    from services.tools.note_profile_tool import get_note_profile
    result = get_note_profile(["Bergamot", "Rose"])
    assert "Bergamot" not in result["shared_pairings"]
    assert "Rose" not in result["shared_pairings"]


def test_shared_pairings_empty_when_no_common(patched_profiles):
    """No common pairings → shared_pairings is an empty list."""
    from services.tools.note_profile_tool import get_note_profile
    # Bergamot pairs with Lemon/Cedar, Musk pairs with Amber — no overlap
    result = get_note_profile(["Bergamot", "Musk"])
    assert result["shared_pairings"] == []


def test_single_note_has_no_shared_pairings(patched_profiles):
    from services.tools.note_profile_tool import get_note_profile
    result = get_note_profile(["Bergamot"])
    assert "shared_pairings" not in result


# ── found field ───────────────────────────────────────────────────────────────

def test_known_note_has_found_true(patched_profiles):
    from services.tools.note_profile_tool import get_note_profile
    result = get_note_profile(["Bergamot"])
    assert result["Bergamot"]["found"] is True


def test_unknown_note_has_found_false(patched_profiles):
    from services.tools.note_profile_tool import get_note_profile
    result = get_note_profile(["FakeNote123"])
    assert result["FakeNote123"]["found"] is False


# ── get_note_pairings ─────────────────────────────────────────────────────────

def test_pairings_returns_intersection(patched_profiles):
    from services.tools.note_profile_tool import get_note_pairings
    # Bergamot pairs with ["Lemon", "Cedar"], Rose pairs with ["Jasmine", "Cedar"]
    # Intersection = ["Cedar"]
    result = get_note_pairings(["Bergamot", "Rose"])
    assert result == ["Cedar"]


def test_pairings_excludes_input_notes(patched_profiles):
    from services.tools.note_profile_tool import get_note_pairings
    result = get_note_pairings(["Bergamot"])
    assert "Bergamot" not in result


def test_pairings_single_note_returns_its_pairs(patched_profiles):
    from services.tools.note_profile_tool import get_note_pairings
    result = get_note_pairings(["Musk"])
    assert "Amber" in result


def test_pairings_unknown_note_returns_empty(patched_profiles):
    from services.tools.note_profile_tool import get_note_pairings
    result = get_note_pairings(["NonExistent"])
    assert result == []


def test_pairings_limit_is_respected(patched_profiles):
    from services.tools.note_profile_tool import get_note_pairings
    result = get_note_pairings(["Bergamot"], limit=1)
    assert len(result) <= 1


def test_pairings_empty_input_returns_empty(patched_profiles):
    from services.tools.note_profile_tool import get_note_pairings
    assert get_note_pairings([]) == []
