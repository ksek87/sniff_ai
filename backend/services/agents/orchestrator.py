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
from services.tools.note_profile_tool import get_note_profile, get_note_pairings
from services.tools.validate_tool import validate_composition

logger = logging.getLogger(__name__)

_MAX_TOOL_ROUNDS = 5

# cache_control on the last tool marks the entire tools block for caching.
# Combined with the cached system prompt this means only the user message +
# accumulated tool rounds are billed at full price after the first call.
_TOOLS: list[dict] = [
    {
        "name": "search_fragrance_db",
        "description": (
            "Search the fragrance database using semantic similarity. "
            "Returns real-world fragrances most similar to the query. "
            "Optionally filter by scent family."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "default": 8},
                "family": {
                    "type": "string",
                    "description": "Optional: Floral, Oriental, Woody, Fresh/Citrus, Fougère, Chypre, Gourmand, Aquatic/Marine, Earthy/Mossy",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_note_profile",
        "description": "Get volatility (top/middle/base), family, and pairing notes for one or more fragrance ingredients. 'found: false' means unknown — avoid it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "notes": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["notes"],
        },
    },
    {
        "name": "get_note_pairings",
        "description": "Given committed notes, return notes that pair well with ALL of them (intersection). Useful for filling remaining tiers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "notes": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["notes"],
        },
    },
    {
        "name": "validate_composition",
        "description": "Validate a draft composition: checks percentages sum to 100, tier balance, and recognised family. Errors have severity 'critical' or 'warning'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "composition": {
                    "type": "object",
                    "description": "FragranceComposition with top_notes, middle_notes, base_notes, scent_family",
                },
            },
            "required": ["composition"],
        },
        "cache_control": {"type": "ephemeral"},
    },
]

_SYSTEM_PROMPT = """You are a master perfumer's assistant. Use the tools to gather fragrance knowledge, then return your findings as JSON.

Workflow:
1. Review the pre-loaded search results in the user message.
2. Call get_note_profile on the most relevant notes (and any pinned notes).
3. Call search_fragrance_db only if you need additional targeted references.

Return this exact JSON at end_turn (no markdown):
{"reference_fragrances":[...],"recommended_notes":{"top":[...],"middle":[...],"base":[...]},"reasoning":"..."}

Only use notes that exist in real perfumery. Prefer notes from the provided references."""


def _compress_for_history(tool_name: str, result: object) -> object:
    """Strip non-essential fields from tool results before appending to conversation history."""
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
        return {
            note: {
                "volatility": p.get("volatility"),
                "family": p.get("family"),
                "pairs": p.get("pairs_well_with", [])[:6],
                "found": p.get("found"),
            }
            for note, p in result.items()
        }
    return result


def _dispatch_tool(tool_name: str, tool_input: dict):
    if tool_name == "search_fragrance_db":
        return search_fragrance_db(**tool_input)
    elif tool_name == "get_note_profile":
        return get_note_profile(tool_input["notes"])
    elif tool_name == "get_note_pairings":
        return get_note_pairings(tool_input["notes"], limit=tool_input.get("limit", 10))
    elif tool_name == "validate_composition":
        return validate_composition(tool_input["composition"])
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
        user_message += f"\nTop references:\n{hits_lines}\n\nPrefer notes from these; call search only if you need more."

    # Cache the user message so rounds 2+ pay only for the new accumulated content.
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
