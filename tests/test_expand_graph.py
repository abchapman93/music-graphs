"""Tests for the `expand-graph` skill helper.

Covers:
    - candidate ceiling clamp (max 10, min 1) + overflow accounting
    - dry-run candidate generation against a mocked search function
    - scope context passes README + existing slugs to the search function
    - no-search-fn default raises (the helper does not invent candidates)
    - Candidate validation: missing spotify_url + missing reason raises
    - run_expand_graph in dry-run does NOT invoke add-node / add-edge
    - run_expand_graph wired write path calls injected add-node / add-edge
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / ".claude" / "skills" / "expand-graph" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO_ROOT))

from expand_graph import (  # noqa: E402
    CANDIDATE_CEILING_MAX,
    Candidate,
    ExpansionResult,
    generate_candidates,
    run_expand_graph,
)


# ---------- fixtures ----------


def _make_bowie_like_graph(tmp_path: Path) -> Path:
    graphs_root = tmp_path / "graphs"
    cards = graphs_root / "bowie-covers" / "cards"
    cards.mkdir(parents=True)
    (graphs_root / "bowie-covers" / "README.md").write_text(
        "---\nname: \"Bowie Covers\"\n---\n\n"
        "A graph centered on David Bowie's songbook.\n",
        encoding="utf-8",
    )
    (cards / "person-david-bowie.md").write_text(
        "---\ntype: person\nname: \"David Bowie\"\n---\n\n"
        "David Bowie wrote [[song:life-on-mars]].\n",
        encoding="utf-8",
    )
    (cards / "song-life-on-mars.md").write_text(
        "---\ntype: song\nname: \"Life on Mars?\"\n---\n\n"
        "Written by [[person:david-bowie]].\n",
        encoding="utf-8",
    )
    (cards / "note-bowie-songbook.md").write_text(
        "---\ntype: note\nname: \"The Bowie Songbook\"\n---\n\n"
        "Scope: Bowie covers across genres. References "
        "[[person:david-bowie]].\n",
        encoding="utf-8",
    )
    return graphs_root


def _fake_candidates(n: int) -> list[Candidate]:
    return [
        Candidate(
            name=f"Test Album {i}",
            type="album",
            wikilinks=["person:david-bowie"],
            spotify_url=f"https://open.spotify.com/album/fakeid{i:02d}",
            rationale=f"Rationale {i}",
        )
        for i in range(1, n + 1)
    ]


# ---------- Candidate validation ----------


def test_candidate_requires_name():
    with pytest.raises(ValueError):
        Candidate(name="", spotify_url="https://open.spotify.com/album/x")


def test_candidate_requires_spotify_or_reason():
    with pytest.raises(ValueError):
        Candidate(name="No URL", spotify_url=None, spotify_reason=None)


def test_candidate_accepts_null_url_with_reason():
    c = Candidate(
        name="MCP-exhausted candidate",
        spotify_url=None,
        spotify_reason="MCP search exhausted",
    )
    assert c.spotify_url is None
    assert c.spotify_reason == "MCP search exhausted"


# ---------- ceiling ----------


def test_ceiling_clamped_to_max_ten(tmp_path):
    graphs_root = _make_bowie_like_graph(tmp_path)
    # Search returns 15; ceiling=20 must clamp to 10 and overflow=5.
    def search(graph, criterion, scope):
        return _fake_candidates(15)

    candidates, overflow = generate_candidates(
        "bowie-covers",
        "find more Bowie covers",
        graphs_root=graphs_root,
        ceiling=20,
        search_fn=search,
    )
    assert len(candidates) == CANDIDATE_CEILING_MAX == 10
    assert overflow == 5


def test_ceiling_clamped_to_min_one(tmp_path):
    graphs_root = _make_bowie_like_graph(tmp_path)
    def search(graph, criterion, scope):
        return _fake_candidates(3)
    candidates, overflow = generate_candidates(
        "bowie-covers", "x", graphs_root=graphs_root,
        ceiling=0, search_fn=search,
    )
    assert len(candidates) == 1
    assert overflow == 2


def test_ceiling_default_truncates(tmp_path):
    graphs_root = _make_bowie_like_graph(tmp_path)
    def search(graph, criterion, scope):
        return _fake_candidates(8)
    candidates, overflow = generate_candidates(
        "bowie-covers", "x", graphs_root=graphs_root, search_fn=search,
    )
    # default ceiling = 5
    assert len(candidates) == 5
    assert overflow == 3


def test_ceiling_no_overflow_when_search_returns_fewer(tmp_path):
    graphs_root = _make_bowie_like_graph(tmp_path)
    def search(graph, criterion, scope):
        return _fake_candidates(2)
    candidates, overflow = generate_candidates(
        "bowie-covers", "x", graphs_root=graphs_root, ceiling=5, search_fn=search,
    )
    assert len(candidates) == 2
    assert overflow == 0


# ---------- scope context ----------


def test_scope_passed_to_search_fn(tmp_path):
    graphs_root = _make_bowie_like_graph(tmp_path)
    captured = {}

    def search(graph, criterion, scope):
        captured.update(scope)
        return _fake_candidates(2)

    generate_candidates(
        "bowie-covers", "expand", graphs_root=graphs_root, search_fn=search,
    )

    assert captured["graph"] == "bowie-covers"
    assert "Bowie's songbook" in captured["readme"]
    assert "person:david-bowie" in captured["existing_slugs"]
    assert "song:life-on-mars" in captured["existing_slugs"]
    assert any("note-bowie-songbook.md" == c for c in captured["existing_cards"])
    assert len(captured["scope_notes"]) == 1
    assert "Bowie covers across genres" in captured["scope_notes"][0]


def test_missing_graph_raises(tmp_path):
    graphs_root = tmp_path / "graphs"
    graphs_root.mkdir()
    with pytest.raises(FileNotFoundError):
        generate_candidates(
            "no-such-graph", "x", graphs_root=graphs_root,
            search_fn=lambda g, c, s: [],
        )


# ---------- default search refuses to invent ----------


def test_default_search_fn_raises(tmp_path):
    graphs_root = _make_bowie_like_graph(tmp_path)
    with pytest.raises(NotImplementedError):
        generate_candidates(
            "bowie-covers", "x", graphs_root=graphs_root,  # no search_fn
        )


# ---------- dry-run ----------


def test_dry_run_returns_candidates_without_writes(tmp_path):
    graphs_root = _make_bowie_like_graph(tmp_path)
    def search(graph, criterion, scope):
        return _fake_candidates(4)

    # Sentinels: if add-node / add-edge get called, fail loudly.
    def fail_add_node(**kw):  # pragma: no cover - must NOT be invoked
        raise AssertionError("add-node must not run in dry_run mode")

    def fail_add_edge(**kw):  # pragma: no cover - must NOT be invoked
        raise AssertionError("add-edge must not run in dry_run mode")

    result = run_expand_graph(
        "bowie-covers", "find covers",
        repo_root=tmp_path, graphs_root=graphs_root,
        dry_run=True, search_fn=search,
        add_node_fn=fail_add_node, add_edge_fn=fail_add_edge,
    )

    assert isinstance(result, ExpansionResult)
    assert result.dry_run is True
    assert len(result.candidates) == 4
    assert result.created_paths == []
    assert result.edge_paths == []
    assert result.lint_returncode is None


# ---------- non-dry-run wiring ----------


def test_run_expand_graph_invokes_add_node_per_approved(tmp_path):
    graphs_root = _make_bowie_like_graph(tmp_path)
    def search(graph, criterion, scope):
        return _fake_candidates(3)

    add_node_calls: list[dict] = []
    add_edge_calls: list[dict] = []

    def fake_add_node(**kwargs):
        add_node_calls.append(kwargs)
        # Pretend we wrote: return a path that mirrors add-node's slug rule.
        graph = kwargs["graph"]
        ctype = kwargs["type"]
        name = kwargs["name"].lower().replace(" ", "-").replace("?", "")
        return Path(graphs_root) / graph / "cards" / f"{ctype}-{name}.md"

    def fake_add_edge(**kwargs):
        add_edge_calls.append(kwargs)
        return [Path(graphs_root) / kwargs["graph"] / "cards" /
                f"person-{kwargs['src_slug']}.md"]

    result = run_expand_graph(
        "bowie-covers", "find covers",
        repo_root=tmp_path, graphs_root=graphs_root,
        ceiling=5, dry_run=False, search_fn=search,
        approved_indices=[1, 3],   # skip candidate 2
        add_node_fn=fake_add_node, add_edge_fn=fake_add_edge,
        run_lint=False,
    )

    assert len(add_node_calls) == 2
    names = {c["name"] for c in add_node_calls}
    assert names == {"Test Album 1", "Test Album 3"}
    assert len(result.created_paths) == 2
    # Each candidate had one wikilink → one reciprocal add-edge call each.
    assert len(add_edge_calls) == 2
    for call in add_edge_calls:
        assert call["src_slug"] == "david-bowie"
    # Lint skipped per run_lint=False.
    assert result.lint_returncode is None


def test_run_expand_graph_records_add_node_failure(tmp_path):
    graphs_root = _make_bowie_like_graph(tmp_path)
    def search(graph, criterion, scope):
        return _fake_candidates(2)

    def boom_add_node(**kwargs):
        raise RuntimeError("simulated lint failure")

    def never_add_edge(**kwargs):  # pragma: no cover
        raise AssertionError("add-edge should not run after add-node failure")

    result = run_expand_graph(
        "bowie-covers", "x",
        repo_root=tmp_path, graphs_root=graphs_root,
        dry_run=False, search_fn=search,
        add_node_fn=boom_add_node, add_edge_fn=never_add_edge,
        run_lint=False,
    )

    assert result.created_paths == []
    assert len(result.skipped) == 2
    assert all("add-node failed" in reason for _name, reason in result.skipped)


def test_run_expand_graph_approved_none_writes_all(tmp_path):
    graphs_root = _make_bowie_like_graph(tmp_path)
    def search(graph, criterion, scope):
        return _fake_candidates(2)

    calls: list[str] = []
    def fake_add_node(**kwargs):
        calls.append(kwargs["name"])
        return Path(graphs_root) / "bowie-covers" / "cards" / f"album-x.md"

    result = run_expand_graph(
        "bowie-covers", "x",
        repo_root=tmp_path, graphs_root=graphs_root,
        dry_run=False, search_fn=search,
        approved_indices=None,                     # default: write all
        add_node_fn=fake_add_node, add_edge_fn=None,
        run_lint=False,
    )
    assert calls == ["Test Album 1", "Test Album 2"]
    assert len(result.created_paths) == 2
