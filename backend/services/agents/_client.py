from __future__ import annotations
import os
import anthropic

_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
_TIMEOUT = 60.0


def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        timeout=_TIMEOUT,
    )
