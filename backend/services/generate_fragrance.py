from __future__ import annotations
import logging
import time

from services.nlp import preprocess
from services.tools.search_tool import search_fragrance_db
from services.agents import orchestrator, composer

logger = logging.getLogger(__name__)

_MAX_RETRIES = 2


def generate_fragrance_from_description(
    description: str,
    pinned_notes: list | None = None,
) -> dict:
    context = preprocess(description)
    context["pinned_notes"] = pinned_notes or []

    # Seed the orchestrator with a broad semantic search upfront so it can
    # skip its own initial search call and go straight to profiling notes.
    context["initial_hits"] = search_fragrance_db(query=description, top_k=10)

    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        if attempt:
            wait = 2 ** (attempt - 1)  # 1s, 2s
            logger.warning("Generation attempt %d failed, retrying in %ds", attempt, wait)
            time.sleep(wait)
        try:
            orchestrator_result = orchestrator.run(context)
            composition = composer.run(description, orchestrator_result)
            return composition
        except Exception as exc:
            last_exc = exc

    raise last_exc  # type: ignore[misc]
