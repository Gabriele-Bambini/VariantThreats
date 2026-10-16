import pytest
from graphweave.graph import KnowledgeGraph
from graphweave.extractors import Triple


def make_triples():
    return [
        Triple("CRISPR", "is a", "gene editing tool", "technology", "concept"),
        Triple("CRISPR", "developed by", "Jennifer Doudna", "technology", "person"),
        Triple("Jennifer Doudna", "won", "Nobel Prize", "person", "event"),
        Triple("gene editing tool", "treats", "cancer", "concept", "disease"),
        Triple("cancer", "caused by", "mutation", "disease", "concept"),
    ]


def test_add_triples():
    kg = KnowledgeGraph()
    kg.add_triples(make_triples())
    assert kg.graph.number_of_nodes() >= 5
    assert kg.graph.number_of_edges() >= 5


def test_no_self_loops():
    kg = KnowledgeGraph()
    kg.add_triples([Triple("X", "relates to", "X")])
    assert kg.graph.number_of_edges() == 0


def test_stats():
    kg = KnowledgeGraph()
    kg.add_triples(make_triples())
    s = kg.stats()
    assert s["nodes"] > 0
    assert s["edges"] > 0


def test_to_d3():
    kg = KnowledgeGraph()
    kg.add_triples(make_triples())
    d3 = kg.to_d3()
    assert "nodes" in d3
    assert "links" in d3
    assert len(d3["nodes"]) > 0


def test_save_load(tmp_path):
    kg = KnowledgeGraph()
    kg.add_triples(make_triples())
    path = tmp_path / "graph.json"
    kg.save(path)
    kg2 = KnowledgeGraph.load(path)
    assert kg2.graph.number_of_nodes() == kg.graph.number_of_nodes()


def test_obsidian_export(tmp_path):
    kg = KnowledgeGraph()
    kg.add_triples(make_triples())
    kg.to_obsidian(tmp_path)
    notes = list((tmp_path / "notes").glob("*.md"))
    assert len(notes) > 0
    content = notes[0].read_text()
    assert "##" in content
