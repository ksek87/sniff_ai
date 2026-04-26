import pytest
from unittest.mock import patch, MagicMock


def _make_extractor_with_notes(notes):
    """Build a NoteExtractor with a fixed notes list (no filesystem needed)."""
    with patch("services.nlp.note_extractor.os.path.exists", return_value=False), \
         patch("services.nlp.note_extractor.pd") as mock_pd:
        mock_df = MagicMock()
        mock_df.__len__.return_value = len(notes)
        mock_df["Notes"].dropna.return_value = [str(notes)]
        mock_pd.read_csv.return_value = mock_df

        import ast
        import importlib
        import services.nlp.note_extractor as mod
        importlib.reload(mod)

        extractor = mod.NoteExtractor.__new__(mod.NoteExtractor)
        extractor.all_notes = notes
        import spacy
        from spacy.pipeline import EntityRuler
        extractor.nlp = spacy.blank("en")
        ruler = extractor.nlp.add_pipe("entity_ruler")
        patterns = [{"label": "FRAGRANCE_NOTE", "pattern": n} for n in notes]
        patterns += [{"label": "FRAGRANCE_NOTE", "pattern": n.lower()} for n in notes if n != n.lower()]
        ruler.add_patterns(patterns)
        return extractor


def test_extracts_explicit_notes():
    extractor = _make_extractor_with_notes(["Bergamot", "Sandalwood", "Oud"])
    result = extractor.extract("I want something with sandalwood and bergamot")
    assert "Sandalwood" in result or "sandalwood".title() in result
    assert "Bergamot" in result or "bergamot".title() in result


def test_no_false_positives():
    extractor = _make_extractor_with_notes(["Bergamot", "Rose"])
    result = extractor.extract("I like walking in the park on rainy days")
    assert result == []


def test_deduplicates_notes():
    extractor = _make_extractor_with_notes(["Rose"])
    result = extractor.extract("rose and rose again rose")
    assert result.count("Rose") == 1
