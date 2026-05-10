from __future__ import annotations
import logging
import time
from concurrent.futures import ThreadPoolExecutor

from services.nlp import preprocess
from services.tools.search_tool import search_fragrance_db
from services.agents import orchestrator, composer

logger = logging.getLogger(__name__)

_MAX_RETRIES = 2


def generate_fragrance_from_description(
    description: str,
    pinned_notes: list | None = None,
) -> dict:
    with ThreadPoolExecutor(max_workers=2) as pool:
        preprocess_f = pool.submit(preprocess, description)
        search_f = pool.submit(search_fragrance_db, description, 5)
        context = preprocess_f.result()
        context["initial_hits"] = search_f.result()
    context["pinned_notes"] = pinned_notes or []

    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        if attempt:
            wait = 2 ** (attempt - 1)  # 1 s, 2 s
            logger.warning("Generation attempt %d failed, retrying in %ds", attempt, wait)
            time.sleep(wait)
        try:
            orchestrator_result = orchestrator.run(context)
            return composer.run(description, orchestrator_result)
        except Exception as exc:
            last_exc = exc

    raise last_exc  # type: ignore[misc]
