from services.nlp import preprocess
from services.tools.search_tool import search_fragrance_db
from services.agents import orchestrator, composer


def generate_fragrance_from_description(
    description: str,
    pinned_notes: list | None = None,
) -> dict:
    context = preprocess(description)
    context["pinned_notes"] = pinned_notes or []

    # Seed the orchestrator with top-k semantic matches upfront
    initial_hits = search_fragrance_db(
        query=description,
        scent_family=context["predicted_family"] if context["family_confidence"] > 0.5 else None,
        top_k=10,
    )
    context["initial_hits"] = initial_hits

    orchestrator_result = orchestrator.run(context)
    composition = composer.run(description, orchestrator_result)
    return composition
