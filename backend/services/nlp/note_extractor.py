import json
import logging
import os
import spacy

from services.config import NOTE_PROFILES_PATH as _NOTES_PATH

logger = logging.getLogger(__name__)


class NoteExtractor:
    def __init__(self):
        self.all_notes: list[str] = []
        self.nlp = spacy.blank("en")
        self._load_notes()
        self._build_ruler()

    def _load_notes(self):
        if os.path.exists(_NOTES_PATH):
            with open(_NOTES_PATH) as f:
                profiles = json.load(f)
            self.all_notes = sorted(profiles.keys())
        else:
            logger.warning("note_profiles.json not found; NER will be disabled")

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
