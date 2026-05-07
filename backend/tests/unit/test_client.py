"""
Unit tests for services/agents/_client.py — shared Anthropic client factory.
"""
import os
from unittest.mock import patch, MagicMock
import pytest


def test_model_default():
    """_MODEL defaults to claude-sonnet-4-6 when env var is absent."""
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("ANTHROPIC_MODEL", None)
        import importlib
        import services.agents._client as mod
        importlib.reload(mod)
        assert mod._MODEL == "claude-sonnet-4-6"


def test_model_from_env():
    """_MODEL picks up ANTHROPIC_MODEL from the environment."""
    with patch.dict(os.environ, {"ANTHROPIC_MODEL": "claude-opus-4-7"}):
        import importlib
        import services.agents._client as mod
        importlib.reload(mod)
        assert mod._MODEL == "claude-opus-4-7"


def test_get_client_uses_api_key_and_timeout():
    """get_client() passes ANTHROPIC_API_KEY and the 60-second timeout."""
    with patch("services.agents._client.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = MagicMock()
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            from services.agents._client import get_client, _TIMEOUT
            get_client()
            mock_anthropic.Anthropic.assert_called_once_with(
                api_key="test-key",
                timeout=_TIMEOUT,
            )


def test_get_client_timeout_is_60():
    """Timeout constant is exactly 60 seconds."""
    from services.agents._client import _TIMEOUT
    assert _TIMEOUT == 60.0


def test_get_client_returns_anthropic_instance():
    """get_client() returns whatever anthropic.Anthropic() produces."""
    sentinel = MagicMock()
    with patch("services.agents._client.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = sentinel
        from services.agents._client import get_client
        result = get_client()
        assert result is sentinel
