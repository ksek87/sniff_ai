"""
Orchestrator Agent: uses Claude tool-use to retrieve fragrance knowledge
and prepare the context the Composition Agent needs.
"""
from __future__ import annotations
import json
import logging
import os

import anthropic

from services.tools.search_tool import search_fragrance_db
from services.tools.note_profile_tool import get_note_profile
from services.tools.validate_tool import validate_composition

logger = logging.getLogger(__name__)

_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
_MAX_TOOL_ROUNDS = 5

_TOOLS: list[dict] = [
    {
        "name": "search_fragrance_db",
        "description": (
            "Search the fragrance database using semantic similarity. "
            "Returns real-world fragrances most similar to the query description. "
            "Use this to ground the composition in real fragrance knowledge."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Descriptive search query"},
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (1–15)",
                    "default": 8,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_note_profile",
        "description": (
            "Get the volatility class (top/middle/base), scent family, and "
            "best pairing notes for one or more fragrance ingredients."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "notes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of fragrance note names",
                }
            },
            "required": ["notes"],
        },
    },
    {
        "name": "validate_composition",
        "description": (
            "Validate a draft fragrance composition. Checks that percentages sum "
            "to 100%, tiers are balanced, and the scent family is recognised."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "composition": {
                    "type": "object",
                    "description": "FragranceComposition object to validate",
                }
            },
            "required": ["composition"],
        },
    },
]

_SYSTEM_PROMPT = """You are a master perfumer's assistant with deep knowledge of fragrance chemistry and composition.

Your job is to use the available tools to build rich, grounded context for creating a new fragrance composition from a user's description.

Strategy:
1. Review the pre-loaded semantic search results provided in the user message.
2. Use get_note_profile to understand the volatility and pairing properties of the most relevant notes.
3. If the user has specified pinned notes, call get_note_profile on those as well.
4. Call search_fragrance_db only if you need more targeted references beyond the pre-loaded ones.
5. Return a JSON summary of your findings in this exact structure:

{
  "reference_fragrances": [...],
  "recommended_notes": {
    "top": ["note1", "note2"],
    "middle": ["note3", "note4"],
    "base": ["note5", "note6"]
  },
  "reasoning": "Brief explanation of why these notes fit the description"
}

Be precise. Do not invent notes that don't exist in perfumery. Prefer notes that appear in the reference fragrances."""


def _dispatch_tool(tool_name: str, tool_input: dict):
    if tool_name == "search_fragrance_db":
        return search_fragrance_db(**tool_input)
    elif tool_name == "get_note_profile":
        return get_note_profile(tool_input["notes"])
    elif tool_name == "validate_composition":
        return validate_composition(tool_input["composition"])
    return {"error": f"Unknown tool: {tool_name}"}


def run(context: dict) -> dict:
    """
    Run the Orchestrator Agent.

    context keys:
        description: str
        detected_notes: list[str]
        predicted_family: str
        family_confidence: float
        pinned_notes: list[str]
        initial_hits: list[dict]   pre-computed semantic search results
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"), timeout=60.0)

    user_message = (
        f"Create a fragrance composition for this description:\n\n"
        f"\"{context['description']}\"\n\n"
        f"Detected notes (explicitly mentioned): "
        f"{context.get('detected_notes', []) or 'none'}\n"
        f"Predicted scent family: {context.get('predicted_family', 'unknown')} "
        f"(confidence: {context.get('family_confidence', 0):.0%})\n"
    )
    if context.get("pinned_notes"):
        user_message += f"Required notes (user-pinned): {context['pinned_notes']}\n"

    initial_hits = context.get("initial_hits", [])
    if initial_hits:
        user_message += (
            f"\nPre-loaded semantic search results ({len(initial_hits)} references):\n"
            f"{json.dumps(initial_hits[:5], indent=2)}\n\n"
            f"Use these as your primary reference set. Call search_fragrance_db "
            f"only if you need additional targeted results."
        )

    messages = [{"role": "user", "content": user_message}]

    for _ in range(_MAX_TOOL_ROUNDS):
        response = client.messages.create(
            model=_MODEL,
            max_tokens=2048,
            system=_SYSTEM_PROMPT,
            tools=_TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in reversed(response.content):
                if hasattr(block, "text"):
                    text = block.text.strip()
                    if "```" in text:
                        start = text.find("{")
                        end = text.rfind("}") + 1
                        if start != -1 and end > start:
                            text = text[start:end]
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        return {"reasoning": text, "reference_fragrances": [], "recommended_notes": {}}
            return {}

        if response.stop_reason == "max_tokens":
            logger.warning("Orchestrator hit max_tokens limit before completing")
            break

        if response.stop_reason != "tool_use":
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = _dispatch_tool(block.name, block.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    }
                )
        messages.append({"role": "user", "content": tool_results})

    return {"reasoning": "Orchestration did not complete.", "reference_fragrances": [], "recommended_notes": {}}
