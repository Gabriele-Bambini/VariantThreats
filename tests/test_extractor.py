import pytest
from graphweave.extractors.llm import _parse_triples, _chunk_text, Triple


def test_parse_valid_json():
    raw = '[{"subject": "A", "predicate": "relates to", "object": "B", "subject_type": "concept", "object_type": "concept"}]'
    triples = _parse_triples(raw, source="test")
    assert len(triples) == 1
    assert triples[0].subject == "A"
    assert triples[0].predicate == "relates to"
    assert triples[0].object == "B"


def test_parse_json_embedded_in_text():
    raw = 'Here are the triples:\n[{"subject": "X", "predicate": "is", "object": "Y"}]\nDone.'
    triples = _parse_triples(raw, source="test")
    assert len(triples) == 1


def test_parse_invalid_json():
    triples = _parse_triples("not json at all", "test")
    assert triples == []


def test_chunk_text():
    text = " ".join(["word"] * 5000)
    chunks = _chunk_text(text, chunk_size=1000, overlap=100)
    assert len(chunks) > 1
    # overlap means consecutive chunks share words
    first_words = set(chunks[0].split()[-100:])
    second_words = set(chunks[1].split()[:100])
    assert len(first_words & second_words) > 0


def test_deduplication_in_extract(monkeypatch):
    from graphweave.extractors.llm import LLMExtractor

    extractor = LLMExtractor.__new__(LLMExtractor)
    extractor.provider = "anthropic"

    duplicate_json = '[{"subject": "A", "predicate": "is", "object": "B"}, {"subject": "A", "predicate": "is", "object": "B"}]'
    monkeypatch.setattr(extractor, "_call_llm", lambda text: duplicate_json)

    triples = extractor.extract("some text", source="test")
    assert len(triples) == 1
