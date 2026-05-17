"""Tests for lib/graph.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from lib.graph import build_graph, list_graphs

FIXTURES = Path(__file__).parent / "fixtures" / "graphs"
FIXTURE_GRAPH = FIXTURES / "fixture-graph"


def test_build_graph_nodes():
    g = build_graph(FIXTURE_GRAPH)
    node_ids = [n["id"] for n in g["nodes"]]
    assert node_ids == sorted(node_ids), "nodes must be sorted by id"
    assert set(node_ids) == {
        "person:alice",
        "person:bob",
        "person:charlie",
        "location:wonderland",
    }
    # Spot-check node fields.
    by_id = {n["id"]: n for n in g["nodes"]}
    assert by_id["person:alice"]["label"] == "Alice"
    assert by_id["person:alice"]["group"] == "person"
    assert "Alice" in by_id["person:alice"]["title"]
    assert "person" in by_id["person:alice"]["title"]


def test_build_graph_edges_deduped_and_no_dangling():
    g = build_graph(FIXTURE_GRAPH)
    edges = g["edges"]
    # alice<->bob dedupes to 1 edge; alice->wonderland = 1 edge.
    # charlie->nonexistent is dangling, dropped.
    assert len(edges) == 2

    # Edges sorted by (from, to)
    assert edges == sorted(edges, key=lambda e: (e["from"], e["to"]))

    pairs = {frozenset((e["from"], e["to"])) for e in edges}
    assert frozenset(("person:alice", "person:bob")) in pairs
    assert frozenset(("person:alice", "location:wonderland")) in pairs

    # No edge to nonexistent target.
    for e in edges:
        assert "nonexistent" not in (e["from"], e["to"])


def test_build_graph_drops_self_loop(tmp_path):
    """Self-loops (source id == target id) must be dropped."""
    graph_dir = tmp_path / "selfy"
    cards = graph_dir / "cards"
    cards.mkdir(parents=True)
    (cards / "person-loop.md").write_text(
        "---\n"
        "type: person\n"
        "name: Loopy\n"
        "---\n\n"
        "I link to myself: [[person:loop]].\n"
    )
    (cards / "person-other.md").write_text(
        "---\n"
        "type: person\n"
        "name: Other\n"
        "---\n\n"
        "I link to [[person:loop]].\n"
    )
    g = build_graph(graph_dir)
    # 2 nodes; loop->loop dropped; other->loop kept = 1 edge
    assert len(g["nodes"]) == 2
    assert len(g["edges"]) == 1
    assert g["edges"][0]["from"] != g["edges"][0]["to"]


def test_build_graph_empty_dir(tmp_path):
    """Missing cards/ folder is tolerated and yields empty graph."""
    g = build_graph(tmp_path)
    assert g == {"nodes": [], "edges": []}


def test_list_graphs_fixture():
    entries = list_graphs(FIXTURES)
    slugs = [e["slug"] for e in entries]
    assert "fixture-graph" in slugs
    entry = next(e for e in entries if e["slug"] == "fixture-graph")
    assert entry["name"] == "Fixture Graph"
    assert "tiny graph" in entry["description"].lower()
    assert entry["cover_image"] == "covers/fixture.jpg"
    assert entry["card_count"] == 4


def test_list_graphs_sorted_and_skips_non_graph_folders(tmp_path):
    # Create two valid graphs and one folder without a cards/ subdir.
    for slug in ("zebra", "alpha"):
        (tmp_path / slug / "cards").mkdir(parents=True)
        (tmp_path / slug / "cards" / "x-y.md").write_text(
            "---\ntype: x\nname: Y\n---\n"
        )
    (tmp_path / "not-a-graph").mkdir()
    (tmp_path / "not-a-graph" / "README.md").write_text("no cards subfolder")

    entries = list_graphs(tmp_path)
    assert [e["slug"] for e in entries] == ["alpha", "zebra"]
    for e in entries:
        assert e["card_count"] == 1
        # No README -> name falls back to slug, description "", cover_image None.
        assert e["name"] == e["slug"]
        assert e["description"] == ""
        assert e["cover_image"] is None


def test_list_graphs_missing_root(tmp_path):
    assert list_graphs(tmp_path / "does-not-exist") == []
