"""Tests for the `add-edge` skill's add_edge helper."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / ".claude" / "skills" / "add-edge" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO_ROOT))

from add_edge import (  # noqa: E402
    add_edge,
    CardNotFoundError,
    DanglingTargetError,
    DuplicateEdgeError,
    LintError,
)
from lib.cards import parse_card  # noqa: E402


# ---------- fixture ----------

def _make_graph(tmp_path: Path, name: str = "test-graph") -> tuple[Path, Path]:
    """Create a graphs_root/<name>/cards/ structure with two mutually-linked
    anchor cards plus an album card the tests can link from."""
    graphs_root = tmp_path / "graphs"
    cards = graphs_root / name / "cards"
    cards.mkdir(parents=True)
    (cards / "person-dave.md").write_text(
        "---\n"
        "type: person\n"
        'name: "Dave"\n'
        "---\n\n"
        "Dave plays with [[person:phil]].\n",
        encoding="utf-8",
    )
    (cards / "person-phil.md").write_text(
        "---\n"
        "type: person\n"
        'name: "Phil"\n'
        "---\n\n"
        "Phil plays with [[person:dave]].\n",
        encoding="utf-8",
    )
    (cards / "album-ashgrove.md").write_text(
        "---\n"
        "type: album\n"
        'name: "Ashgrove"\n'
        "---\n\n"
        "Ashgrove was released in 2004 by [[person:dave]].\n",
        encoding="utf-8",
    )
    return graphs_root, cards


# ---------- happy path: one-way ----------

def test_add_edge_one_way(tmp_path):
    graphs_root, cards = _make_graph(tmp_path)
    paths = add_edge(
        graph="test-graph",
        src_slug="dave",
        tgt_slug="ashgrove",
        graphs_root=graphs_root,
        repo_root=REPO_ROOT,
        relationship="appears on",
        run_lint=False,
    )
    assert paths == [cards / "person-dave.md"]

    parsed = parse_card(cards / "person-dave.md")
    # Wikilink should now be present.
    assert ("album", "ashgrove") in parsed["wikilinks"]
    # The relationship sentence should be in the body.
    assert "appears on" in parsed["body_md"]
    assert "[[album:ashgrove|Ashgrove]]" in parsed["body_md"]
    # Original content must be preserved.
    assert "Dave plays with [[person:phil]]." in parsed["body_md"]

    # Target should be untouched.
    tgt_parsed = parse_card(cards / "album-ashgrove.md")
    assert ("person", "dave") in tgt_parsed["wikilinks"]  # was already there
    # No new "Ashgrove appears on dave" sentence in target.
    assert "appears on" not in tgt_parsed["body_md"]


# ---------- happy path: symmetric ----------

def test_add_edge_symmetric_writes_both(tmp_path):
    graphs_root, cards = _make_graph(tmp_path)
    # Remove the pre-existing reciprocal link in phil so we can observe both
    # sides being written.
    (cards / "person-phil.md").write_text(
        "---\n"
        "type: person\n"
        'name: "Phil"\n'
        "---\n\n"
        "Phil is a musician.\n",
        encoding="utf-8",
    )
    (cards / "person-dave.md").write_text(
        "---\n"
        "type: person\n"
        'name: "Dave"\n'
        "---\n\n"
        "Dave is a musician.\n",
        encoding="utf-8",
    )
    paths = add_edge(
        graph="test-graph",
        src_slug="dave",
        tgt_slug="phil",
        graphs_root=graphs_root,
        repo_root=REPO_ROOT,
        symmetric=True,
        run_lint=False,
    )
    assert cards / "person-dave.md" in paths
    assert cards / "person-phil.md" in paths
    assert len(paths) == 2

    dave = parse_card(cards / "person-dave.md")
    phil = parse_card(cards / "person-phil.md")
    assert ("person", "phil") in dave["wikilinks"]
    assert ("person", "dave") in phil["wikilinks"]


def test_add_edge_symmetric_skips_existing_reciprocal(tmp_path):
    """If the target already has the reciprocal link, the second write is skipped
    silently; only the source path is returned."""
    graphs_root, cards = _make_graph(tmp_path)
    # phil already contains [[person:dave]]; dave does NOT contain
    # [[person:phil]] in the album body, so source-side write must happen,
    # but target-side write should be skipped.
    (cards / "person-dave.md").write_text(
        "---\n"
        "type: person\n"
        'name: "Dave"\n'
        "---\n\n"
        "Dave is a musician.\n",
        encoding="utf-8",
    )
    paths = add_edge(
        graph="test-graph",
        src_slug="dave",
        tgt_slug="phil",
        graphs_root=graphs_root,
        repo_root=REPO_ROOT,
        symmetric=True,
        run_lint=False,
    )
    assert paths == [cards / "person-dave.md"]


# ---------- dangling target ----------

def test_add_edge_dangling_aborts_by_default(tmp_path):
    graphs_root, _cards = _make_graph(tmp_path)
    with pytest.raises(DanglingTargetError):
        add_edge(
            graph="test-graph",
            src_slug="dave",
            tgt_slug="nonexistent-album",
            graphs_root=graphs_root,
            repo_root=REPO_ROOT,
            relationship="appears on",
            run_lint=False,
        )

    # Source must be unchanged.
    dave_text = (graphs_root / "test-graph" / "cards" / "person-dave.md").read_text()
    assert "nonexistent-album" not in dave_text


def test_add_edge_dangling_forward_writes_anyway(tmp_path):
    graphs_root, cards = _make_graph(tmp_path)
    paths = add_edge(
        graph="test-graph",
        src_slug="dave",
        tgt_slug="future-album",
        graphs_root=graphs_root,
        repo_root=REPO_ROOT,
        relationship="will appear on",
        on_dangling="forward",
        run_lint=False,
    )
    assert paths == [cards / "person-dave.md"]
    body = (cards / "person-dave.md").read_text()
    assert "future-album" in body


# ---------- duplicate detection ----------

def test_add_edge_duplicate_raises(tmp_path):
    graphs_root, cards = _make_graph(tmp_path)
    # dave already references [[person:phil]] in his body.
    with pytest.raises(DuplicateEdgeError):
        add_edge(
            graph="test-graph",
            src_slug="dave",
            tgt_slug="phil",
            graphs_root=graphs_root,
            repo_root=REPO_ROOT,
            run_lint=False,
        )

    # File must be untouched.
    text = (cards / "person-dave.md").read_text()
    # Body still has exactly one [[person:phil]] reference.
    assert text.count("[[person:phil]]") == 1


# ---------- source missing ----------

def test_add_edge_missing_source_raises(tmp_path):
    graphs_root, _cards = _make_graph(tmp_path)
    with pytest.raises(CardNotFoundError):
        add_edge(
            graph="test-graph",
            src_slug="no-such-card",
            tgt_slug="ashgrove",
            graphs_root=graphs_root,
            repo_root=REPO_ROOT,
            run_lint=False,
        )


# ---------- lint rollback ----------

def test_add_edge_lint_failure_rolls_back(tmp_path):
    graphs_root, cards = _make_graph(tmp_path)
    src = cards / "person-dave.md"
    tgt = cards / "album-ashgrove.md"
    src_before = src.read_text()
    tgt_before = tgt.read_text()

    with pytest.raises(LintError):
        add_edge(
            graph="test-graph",
            src_slug="dave",
            tgt_slug="ashgrove",
            graphs_root=graphs_root,
            repo_root=REPO_ROOT,
            relationship="appears on",
            run_lint=True,
            lint_cmd=["false"],
        )

    # Both files restored.
    assert src.read_text() == src_before
    assert tgt.read_text() == tgt_before


def test_add_edge_lint_rollback_symmetric(tmp_path):
    """When symmetric write modifies two files, both must be restored on lint fail."""
    graphs_root, cards = _make_graph(tmp_path)
    # Strip phil/dave bodies so each side gets a fresh write.
    src = cards / "person-dave.md"
    tgt = cards / "person-phil.md"
    src.write_text(
        "---\ntype: person\nname: \"Dave\"\n---\n\nDave is a musician.\n",
        encoding="utf-8",
    )
    tgt.write_text(
        "---\ntype: person\nname: \"Phil\"\n---\n\nPhil is a musician.\n",
        encoding="utf-8",
    )
    src_before = src.read_text()
    tgt_before = tgt.read_text()

    with pytest.raises(LintError):
        add_edge(
            graph="test-graph",
            src_slug="dave",
            tgt_slug="phil",
            graphs_root=graphs_root,
            repo_root=REPO_ROOT,
            symmetric=True,
            run_lint=True,
            lint_cmd=["false"],
        )

    assert src.read_text() == src_before
    assert tgt.read_text() == tgt_before


# ---------- lint success ----------

def test_add_edge_lint_success_keeps_change(tmp_path):
    graphs_root, cards = _make_graph(tmp_path)
    paths = add_edge(
        graph="test-graph",
        src_slug="dave",
        tgt_slug="ashgrove",
        graphs_root=graphs_root,
        repo_root=REPO_ROOT,
        relationship="appears on",
        run_lint=True,
        lint_cmd=["true"],
    )
    assert paths == [cards / "person-dave.md"]
    parsed = parse_card(cards / "person-dave.md")
    assert ("album", "ashgrove") in parsed["wikilinks"]
