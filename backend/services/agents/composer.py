"""
Composition Agent: takes the Orchestrator's findings and produces
the final structured FragranceComposition JSON.
"""
from __future__ import annotations
import json
import os
import re

import anthropic

_MODEL = "claude-sonnet-4-6"

_SYSTEM_PROMPT = """You are a master perfumer who writes the final fragrance formula and description.

You will receive:
- The user's original description
- The orchestrator's recommended notes (split by top/middle/base)
- Reference fragrances from the database
- Any notes the user has pinned as required

Your job is to produce a single JSON object matching this schema exactly:

{
  "name": string,              // Evocative, original fragrance name (2-4 words)
  "scent_family": string,      // One of: Floral, Oriental, Woody, Fresh/Citrus, Fougère, Chypre, Gourmand, Aquatic/Marine, Earthy/Mossy
  "top_notes": [{"note": string, "percentage": number}],
  "middle_notes": [{"note": string, "percentage": number}],
  "base_notes": [{"note": string, "percentage": number}],
  "poetic_description": string,  // 2-4 sentences, written in the user's register
  "similar_fragrances": [{"brand": string, "name": string, "similarity_score": number}],
  "confidence_score": number    // 0.0 – 1.0, your confidence in this composition
}

Rules:
- top + middle + base percentages MUST sum to exactly 100
- Each tier MUST have 1–6 notes
- similar_fragrances: pick 1–3 from the provided references (highest similarity scores)
- Do NOT add markdown formatting — return raw JSON only
- The poetic_description should mirror the tone and register of the user's input"""


def run(description: str, orchestrator_result: dict) -> dict:
    """
    Run the Composition Agent.

    Returns a FragranceComposition dict, falling back to a minimal valid
    composition if Claude returns malformed JSON.
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    user_message = (
        f"Original description: \"{description}\"\n\n"
        f"Orchestrator findings:\n{json.dumps(orchestrator_result, indent=2)}"
    )

    response = client.messages.create(
        model=_MODEL,
        max_tokens=1500,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip() if response.content else ""

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        composition = json.loads(raw)
        # Normalise percentages to sum to 100 if slightly off
        _normalise_percentages(composition)
        return composition
    except (json.JSONDecodeError, KeyError):
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
    # Fix rounding drift on last note
    remainder = 100 - sum(n["percentage"] for n in all_notes)
    if all_notes:
        all_notes[-1]["percentage"] = round(all_notes[-1]["percentage"] + remainder, 1)


def _fallback_composition(description: str, orchestrator_result: dict) -> dict:
    """Returns a minimal valid composition when JSON parsing fails."""
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
