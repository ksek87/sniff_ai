"""
Unit tests for NoteExtractor.

The extractor is built directly with a fixed note list so no filesystem
access or model downloads are needed.
"""
import spacy
import pytest
from services.nlp.note_extractor import NoteExtractor


def _make_extractor(notes: list[str]) -> NoteExtractor:
    """Construct an extractor with an explicit note list, bypassing file I/O."""
    extractor = object.__new__(NoteExtractor)
    extractor.all_notes = notes
    extractor.nlp = spacy.blank("en")
    ruler = extractor.nlp.add_pipe("entity_ruler")
    patterns = [{"label": "FRAGRANCE_NOTE", "pattern": note} for note in notes]
    patterns += [
        {"label": "FRAGRANCE_NOTE", "pattern": note.lower()}
        for note in notes
        if note != note.lower()
    ]
    ruler.add_patterns(patterns)
    return extractor


def test_extracts_notes_from_text():
    extractor = _make_extractor(["Bergamot", "Sandalwood", "Oud"])
    result = extractor.extract("I want something with sandalwood and bergamot")
    assert "Sandalwood" in result
    assert "Bergamot" in result


def test_case_insensitive_detection():
    extractor = _make_extractor(["Rose", "Jasmine"])
    assert "Rose" in extractor.extract("rose petals everywhere")
    assert "Jasmine" in extractor.extract("jasmine blossom")


def test_no_false_positives():
    extractor = _make_extractor(["Bergamot", "Rose"])
    result = extractor.extract("I like walking in the park on rainy days")
    assert result == []


def test_deduplicates_notes():
    extractor = _make_extractor(["Rose"])
    result = extractor.extract("rose and rose again rose")
    assert result.count("Rose") == 1


def test_empty_string_returns_empty():
    extractor = _make_extractor(["Rose", "Oud"])
    assert extractor.extract("") == []


def test_multi_word_note():
    extractor = _make_extractor(["Pink Pepper", "Tonka Bean"])
    result = extractor.extract("hints of pink pepper and tonka bean")
    assert "Pink Pepper" in result
    assert "Tonka Bean" in result


def test_note_not_in_list_ignored():
    extractor = _make_extractor(["Rose"])
    result = extractor.extract("bergamot and oud and musk")
    assert result == []


def test_returns_title_case_canonical():
    extractor = _make_extractor(["Cedarwood"])
    result = extractor.extract("cedarwood smoke")
    assert result == ["Cedarwood"]
