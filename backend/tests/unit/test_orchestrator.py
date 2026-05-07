"""
Unit tests for services/agents/orchestrator.py — tool dispatch and run() exit paths.
Claude API calls are fully mocked; no network I/O.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from services.agents.orchestrator import _dispatch_tool


# ── Helpers ────────────────────────────────────────────────────────────────

def _text_block(text: str):
    block = MagicMock()
    block.text = text
    block.type = "text"
    return block


def _tool_use_block(tool_id: str, name: str, input_data: dict):
    block = MagicMock()
    del block.text          # tool_use blocks have no .text
    block.type = "tool_use"
    block.id = tool_id
    block.name = name
    block.input = input_data
    return block


def _make_response(content, stop_reason: str):
    resp = MagicMock()
    resp.content = content
    resp.stop_reason = stop_reason
    return resp


def _base_context():
    return {
        "description": "autumn forest",
        "detected_notes": [],
        "predicted_family": "Woody",
        "family_confidence": 0.8,
        "pinned_notes": [],
        "initial_hits": [],
    }


# ── _dispatch_tool ─────────────────────────────────────────────────────────

def test_dispatch_unknown_tool_returns_error():
    result = _dispatch_tool("nonexistent_tool", {})
    assert "error" in result
    assert "nonexistent_tool" in result["error"]


def test_dispatch_search_fragrance_db():
    with patch("services.agents.orchestrator.search_fragrance_db") as mock_fn:
        mock_fn.return_value = [{"name": "Forest Walk"}]
        result = _dispatch_tool("search_fragrance_db", {"query": "pine", "top_k": 5})
        mock_fn.assert_called_once_with(query="pine", top_k=5)
        assert result == [{"name": "Forest Walk"}]


def test_dispatch_get_note_profile():
    with patch("services.agents.orchestrator.get_note_profile") as mock_fn:
        mock_fn.return_value = {"Oud": {"volatility": "base"}}
        result = _dispatch_tool("get_note_profile", {"notes": ["Oud"]})
        mock_fn.assert_called_once_with(["Oud"])
        assert "Oud" in result


def test_dispatch_get_note_pairings():
    with patch("services.agents.orchestrator.get_note_pairings") as mock_fn:
        mock_fn.return_value = ["Cedar", "Musk"]
        result = _dispatch_tool("get_note_pairings", {"notes": ["Bergamot", "Rose"], "limit": 5})
        mock_fn.assert_called_once_with(["Bergamot", "Rose"], limit=5)
        assert "Cedar" in result


def test_dispatch_get_note_pairings_default_limit():
    with patch("services.agents.orchestrator.get_note_pairings") as mock_fn:
        mock_fn.return_value = []
        _dispatch_tool("get_note_pairings", {"notes": ["Bergamot"]})
        mock_fn.assert_called_once_with(["Bergamot"], limit=10)


def test_dispatch_validate_composition():
    comp = {"name": "Test", "scent_family": "Woody"}
    with patch("services.agents.orchestrator.validate_composition") as mock_fn:
        mock_fn.return_value = {"valid": True}
        result = _dispatch_tool("validate_composition", {"composition": comp})
        mock_fn.assert_called_once_with(comp)
        assert result["valid"] is True


# ── run() — end_turn with valid JSON ──────────────────────────────────────

def test_run_end_turn_returns_parsed_json():
    payload = {
        "reference_fragrances": [{"name": "Test Frag"}],
        "recommended_notes": {"top": ["Bergamot"]},
        "reasoning": "Pine and cedar dominate",
    }
    with patch("services.agents.orchestrator.get_client") as mock_gc:
        mock_client = MagicMock()
        mock_gc.return_value = mock_client
        mock_client.messages.create.return_value = _make_response(
            [_text_block(json.dumps(payload))], "end_turn"
        )
        from services.agents.orchestrator import run
        result = run(_base_context())
    assert result["reasoning"] == "Pine and cedar dominate"
    assert result["reference_fragrances"][0]["name"] == "Test Frag"


def test_run_end_turn_strips_markdown_fences():
    """JSON wrapped in ```json ... ``` should still parse correctly."""
    payload = {"reference_fragrances": [], "recommended_notes": {}, "reasoning": "ok"}
    raw = f"```json\n{json.dumps(payload)}\n```"
    with patch("services.agents.orchestrator.get_client") as mock_gc:
        mock_client = MagicMock()
        mock_gc.return_value = mock_client
        mock_client.messages.create.return_value = _make_response(
            [_text_block(raw)], "end_turn"
        )
        from services.agents.orchestrator import run
        result = run(_base_context())
    assert result["reasoning"] == "ok"


def test_run_end_turn_malformed_json_returns_dict_with_reasoning():
    """If the final text isn't valid JSON, reasoning is preserved as raw text."""
    with patch("services.agents.orchestrator.get_client") as mock_gc:
        mock_client = MagicMock()
        mock_gc.return_value = mock_client
        mock_client.messages.create.return_value = _make_response(
            [_text_block("Not JSON at all")], "end_turn"
        )
        from services.agents.orchestrator import run
        result = run(_base_context())
    assert "reasoning" in result
    assert result["reference_fragrances"] == []


def test_run_max_tokens_returns_fallback():
    """stop_reason=max_tokens breaks the loop and returns the did-not-complete sentinel."""
    with patch("services.agents.orchestrator.get_client") as mock_gc:
        mock_client = MagicMock()
        mock_gc.return_value = mock_client
        mock_client.messages.create.return_value = _make_response(
            [_text_block("truncated...")], "max_tokens"
        )
        from services.agents.orchestrator import run
        result = run(_base_context())
    assert "reasoning" in result
    assert "Orchestration did not complete" in result["reasoning"]


def test_run_tool_use_dispatches_and_continues():
    """A tool_use response causes tool execution, then a follow-up create call."""
    tool_resp = _make_response(
        [_tool_use_block("id-1", "search_fragrance_db", {"query": "pine"})],
        "tool_use",
    )
    final_payload = {"reference_fragrances": [], "recommended_notes": {}, "reasoning": "done"}
    final_resp = _make_response([_text_block(json.dumps(final_payload))], "end_turn")

    with (
        patch("services.agents.orchestrator.get_client") as mock_gc,
        patch("services.agents.orchestrator.search_fragrance_db") as mock_search,
    ):
        mock_client = MagicMock()
        mock_gc.return_value = mock_client
        mock_client.messages.create.side_effect = [tool_resp, final_resp]
        mock_search.return_value = [{"name": "Forest Walk"}]

        from services.agents.orchestrator import run
        result = run(_base_context())

    assert mock_client.messages.create.call_count == 2
    mock_search.assert_called_once_with(query="pine")
    assert result["reasoning"] == "done"


def test_run_includes_pinned_notes_in_user_message():
    """Pinned notes appear in the initial user message sent to the API."""
    payload = {"reference_fragrances": [], "recommended_notes": {}, "reasoning": "x"}
    with patch("services.agents.orchestrator.get_client") as mock_gc:
        mock_client = MagicMock()
        mock_gc.return_value = mock_client
        mock_client.messages.create.return_value = _make_response(
            [_text_block(json.dumps(payload))], "end_turn"
        )
        ctx = {**_base_context(), "pinned_notes": ["Oud", "Bergamot"]}
        from services.agents.orchestrator import run
        run(ctx)

    call_args = mock_client.messages.create.call_args
    messages = call_args.kwargs["messages"]
    user_content = messages[0]["content"]
    assert "Oud" in user_content
    assert "Bergamot" in user_content
