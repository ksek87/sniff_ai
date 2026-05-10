"""
Orchestrator Agent: uses Claude tool-use to retrieve fragrance knowledge
and prepare the context the Composition Agent needs.
"""
from __future__ import annotations
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from langfuse.decorators import observe
except ImportError:
    def observe(name=None):
        def decorator(func):
            return func
        return decorator

from services.agents._client import _MODEL, get_client
from services.tools.search_tool import search_fragrance_db
from services.tools.note_profile_tool import get_note_profile

logger = logging.getLogger(__name__)

_MAX_TOOL_ROUNDS = 3
_TOOLS: list[dict] = [
    {
        "name": "search_fragrance_db",
        "description": (
            "Search the fragrance database by semantic similarity. "
            "Returns real-world fragrances matching the query. "
            "Optional family filter: Floral, Oriental, Woody, Fresh/Citrus, "
            "Fougère, Chypre, Gourmand, Aquatic/Marine, Earthy/Mossy. "
            "Only call this if the pre-loaded references are insufficient."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "default": 5},
                "family": {"type": "string"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_note_profile",
        "description": (
            "Get volatility (top/middle/base), scent family, and pairing data for "
            "one or more fragrance notes in a single call. "
            "'found: false' means the note is unknown — avoid using it. "
            "When ≥2 notes are requested the response also includes 'shared_pairings': "
            "notes that pair well with ALL of the requested notes combined. "
            "Call this once with all candidate notes to avoid extra round-trips."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "notes": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["notes"],
        },
        "cache_control": {"type": "ephemeral"},
    },
]

_SYSTEM_PROMPT = """You are a master perfumer's assistant. Use the tools to gather fragrance knowledge, then return your findings as JSON.

Goal: complete in 2 rounds or fewer.
Round 1 — call get_note_profile with ALL candidate notes at once (5–8 notes from the references, plus any pinned notes). The response includes shared_pairings automatically. Only call search_fragrance_db if the pre-loaded references are clearly insufficient.
Round 2 — return findings as JSON (end_turn, no markdown):
{"reference_fragrances":[...],"recommended_notes":{"top":[...],"middle":[...],"base":[...]},"reasoning":"..."}

Only use notes that exist in real perfumery."""


def _compress_for_history(tool_name: str, result: object) -> object:
    """Strip non-essential fields before appending to conversation history."""
    if tool_name == "search_fragrance_db" and isinstance(result, list):
        return [
            {
                "name": r["name"],
                "brand": r["brand"],
                "notes": (r.get("notes") or "")[:80],
                "score": r["similarity_score"],
            }
            for r in result[:5]
        ]
    if tool_name == "get_note_profile" and isinstance(result, dict):
        compressed = {}
        for key, val in result.items():
            if key == "shared_pairings":
                compressed[key] = val[:8]
            else:
                compressed[key] = {
                    "volatility": val.get("volatility"),
                    "family": val.get("family"),
                    "pairs": val.get("pairs_well_with", [])[:5],
                    "found": val.get("found"),
                }
        return compressed
    return result


def _dispatch_tool(tool_name: str, tool_input: dict):
    if tool_name == "search_fragrance_db":
        return search_fragrance_db(**tool_input)
    if tool_name == "get_note_profile":
        return get_note_profile(tool_input["notes"])
    return {"error": f"Unknown tool: {tool_name}"}


@observe(name="orchestrator")
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
    client = get_client()

    user_message = (
        f"Create a fragrance for: \"{context['description']}\"\n"
        f"Detected notes: {context.get('detected_notes') or 'none'}\n"
        f"Predicted family: {context.get('predicted_family', 'unknown')} "
        f"({context.get('family_confidence', 0):.0%} confidence)\n"
    )
    if context.get("pinned_notes"):
        user_message += f"Required notes: {context['pinned_notes']}\n"

    initial_hits = context.get("initial_hits", [])
    if initial_hits:
        hits_lines = "\n".join(
            f"- {h['name']} by {h['brand']} ({h['similarity_score']:.2f}): {(h.get('notes') or '')[:80]}"
            for h in initial_hits[:3]
        )
        user_message += f"\nTop references:\n{hits_lines}\n"

    # Cache the user message so rounds 2+ pay only for newly accumulated content.
    messages = [{"role": "user", "content": [
        {"type": "text", "text": user_message, "cache_control": {"type": "ephemeral"}}
    ]}]

    for _ in range(_MAX_TOOL_ROUNDS):
        response = client.messages.create(
            model=_MODEL,
            max_tokens=1024,
            system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
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

        tool_blocks = [b for b in response.content if b.type == "tool_use"]
        with ThreadPoolExecutor(max_workers=len(tool_blocks)) as pool:
            futs = {pool.submit(_dispatch_tool, b.name, b.input): b for b in tool_blocks}
            results_by_id = {futs[f].id: f.result() for f in as_completed(futs)}

        tool_results = [
            {
                "type": "tool_result",
                "tool_use_id": b.id,
                "content": json.dumps(
                    _compress_for_history(b.name, results_by_id[b.id]),
                    separators=(',', ':'),
                ),
            }
            for b in tool_blocks
        ]
        messages.append({"role": "user", "content": tool_results})

    return {"reasoning": "Orchestration did not complete.", "reference_fragrances": [], "recommended_notes": {}}
