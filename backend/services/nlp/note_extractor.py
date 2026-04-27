import json
import logging
import os
import spacy

logger = logging.getLogger(__name__)

_NOTES_PATH = os.path.join(os.path.dirname(__file__), "../../data/note_profiles.json")
_FALLBACK_NOTES_PATH = os.path.join(
    os.path.dirname(__file__), "../../../data_collection/dataset.csv"
)


class NoteExtractor:
    def __init__(self):
        self.all_notes: list[str] = []
        self.nlp = spacy.blank("en")
        self._load_notes()
        self._build_ruler()

    def _load_notes(self):
        # Prefer pre-generated note_profiles.json
        if os.path.exists(_NOTES_PATH):
            with open(_NOTES_PATH) as f:
                profiles = json.load(f)
            self.all_notes = sorted(profiles.keys())
            return

        # Fall back to extracting unique notes from dataset.csv at runtime
        try:
            import ast
            import pandas as pd

            df = pd.read_csv(_FALLBACK_NOTES_PATH)
            notes_set: set[str] = set()
            for val in df["Notes"].dropna():
                try:
                    notes = ast.literal_eval(val)
                    if isinstance(notes, list):
                        notes_set.update(n.strip() for n in notes if n.strip())
                except (ValueError, SyntaxError):
                    pass
            self.all_notes = sorted(notes_set)
        except Exception:
            logger.warning("Failed to load notes from dataset; NER will be disabled", exc_info=True)
            self.all_notes = []

    def _build_ruler(self):
        ruler = self.nlp.add_pipe("entity_ruler")
        patterns = [
            {"label": "FRAGRANCE_NOTE", "pattern": note}
            for note in self.all_notes
        ]
        # Also add lowercase variants
        patterns += [
            {"label": "FRAGRANCE_NOTE", "pattern": note.lower()}
            for note in self.all_notes
            if note != note.lower()
        ]
        ruler.add_patterns(patterns)

    def extract(self, text: str) -> list[str]:
        doc = self.nlp(text)
        seen: set[str] = set()
        result: list[str] = []
        for ent in doc.ents:
            if ent.label_ == "FRAGRANCE_NOTE":
                canonical = ent.text.title()
                if canonical not in seen:
                    seen.add(canonical)
                    result.append(canonical)
        return result
