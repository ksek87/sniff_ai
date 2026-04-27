from services.nlp import preprocess
from services.tools.search_tool import search_fragrance_db
from services.agents import orchestrator, composer


def generate_fragrance_from_description(
    description: str,
    pinned_notes: list | None = None,
) -> dict:
    context = preprocess(description)
    context["pinned_notes"] = pinned_notes or []

    # Seed the orchestrator with a broad semantic search upfront.
    # The orchestrator receives these as pre-loaded context so it can skip
    # its own initial search call and go straight to profiling notes.
    context["initial_hits"] = search_fragrance_db(query=description, top_k=10)

    orchestrator_result = orchestrator.run(context)
    composition = composer.run(description, orchestrator_result)
    return composition
