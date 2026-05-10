"""
Composition Agent: takes the Orchestrator's findings and produces
the final structured FragranceComposition JSON.
"""
from __future__ import annotations
import json
import logging
import re

try:
    from langfuse.decorators import observe
except ImportError:
    def observe(name=None):
        def decorator(func):
            return func
        return decorator

from services.agents._client import _MODEL, get_client

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a master perfumer. Output a single raw JSON object — no markdown, no extra keys:

{
  "name": "evocative 2-4 word name",
  "scent_family": "Floral|Oriental|Woody|Fresh/Citrus|Fougère|Chypre|Gourmand|Aquatic/Marine|Earthy/Mossy",
  "top_notes": [{"note": "string", "percentage": 0}],
  "middle_notes": [{"note": "string", "percentage": 0}],
  "base_notes": [{"note": "string", "percentage": 0}],
  "poetic_description": "2-4 sentences written in the user's tone and register",
  "similar_fragrances": [{"brand": "string", "name": "string", "similarity_score": 0.0}],
  "confidence_score": 0.0
}

Rules: all percentages sum to exactly 100; 1–6 notes per tier; 1–3 similar_fragrances chosen from provided references."""


def _trim_orchestrator_result(orchestrator_result: dict) -> str:
    """Strip verbose fields before sending to composer — keeps only what it needs."""
    refs = [
        {
            "brand": r.get("brand", ""),
            "name": r.get("name", ""),
            "score": round(r.get("similarity_score", 0), 2),
        }
        for r in orchestrator_result.get("reference_fragrances", [])[:3]
    ]
    trimmed = {
        "notes": orchestrator_result.get("recommended_notes", {}),
        "refs": refs,
        "reasoning": (orchestrator_result.get("reasoning") or "")[:300],
    }
    return json.dumps(trimmed, separators=(',', ':'))


@observe(name="composer")
def run(description: str, orchestrator_result: dict) -> dict:
    """
    Run the Composition Agent.

    Returns a FragranceComposition dict, falling back to a minimal valid
    composition if Claude returns malformed JSON.
    """
    client = get_client()

    user_message = (
        f'Description: "{description}"\n\n'
        f"Orchestrator:\n{_trim_orchestrator_result(orchestrator_result)}"
    )

    response = client.messages.create(
        model=_MODEL,
        max_tokens=1500,
        system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip() if response.content else ""
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        composition = json.loads(raw)
        _normalise_percentages(composition)
        return composition
    except (json.JSONDecodeError, KeyError) as exc:
        logger.warning("Composer returned malformed JSON (%s); using fallback. Raw: %.200s", exc, raw)
        return _fallback_composition(description, orchestrator_result)


def _normalise_percentages(composition: dict) -> None:
    all_notes = (
        composition.get("top_notes", [])
        + composition.get("middle_notes", [])
        + composition.get("base_notes", [])
    )
    total = sum(n.get("percentage", 0) for n in all_notes)
    if total == 0 or abs(total - 100) <= 1:
        return
    scale = 100.0 / total
    for note in all_notes:
        note["percentage"] = round(note["percentage"] * scale, 1)
    remainder = 100 - sum(n["percentage"] for n in all_notes)
    if all_notes:
        all_notes[-1]["percentage"] = round(all_notes[-1]["percentage"] + remainder, 1)


def _fallback_composition(description: str, orchestrator_result: dict) -> dict:
    refs = orchestrator_result.get("reference_fragrances", [])[:2]
    similar = [
        {"brand": r.get("brand", ""), "name": r.get("name", ""), "similarity_score": r.get("similarity_score", 0.0)}
        for r in refs
    ]
    return {
        "name": "Untitled Accord",
        "scent_family": "Woody",
        "top_notes": [{"note": "Bergamot", "percentage": 20}],
        "middle_notes": [{"note": "Rose", "percentage": 40}, {"note": "Geranium", "percentage": 20}],
        "base_notes": [{"note": "Cedarwood", "percentage": 20}],
        "poetic_description": f"A fragrance inspired by: {description}",
        "similar_fragrances": similar,
        "confidence_score": 0.5,
    }
