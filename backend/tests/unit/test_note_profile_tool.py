"""
Unit tests for get_note_profile.
"""
import json
import pytest
from unittest.mock import patch


_SAMPLE_PROFILES = {
    "Bergamot": {"volatility": "top", "family": "Fresh/Citrus", "pairs_well_with": ["Lemon"]},
    "Rose": {"volatility": "middle", "family": "Floral", "pairs_well_with": ["Jasmine"]},
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
    assert len(result) == 3
    assert result["Rose"]["volatility"] == "middle"
    assert result["Musk"]["volatility"] == "base"


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
