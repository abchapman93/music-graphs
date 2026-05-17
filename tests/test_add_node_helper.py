"""Tests for the `add-node` skill's write_card helper."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / ".claude" / "skills" / "add-node" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO_ROOT))

from write_card import (  # noqa: E402
    LintError,
    derive_filename,
    slugify,
    write_card,
)
from lib.cards import parse_card  # noqa: E402


# ---------- helpers ----------

def _make_graph(tmp_path: Path, name: str = "test-graph") -> tuple[Path, Path]:
    """Create a graphs_root/<name>/cards/ structure with two mutually-linked
    anchor cards (so lint sees no orphans and no dangling links)."""
    graphs_root = tmp_path / "graphs"
    cards = graphs_root / name / "cards"
    cards.mkdir(parents=True)
    (cards / "person-anchor.md").write_text(
        "---\n"
        "type: person\n"
        'name: "Anchor"\n'
        "---\n\n"
        "Anchor works with [[person:anchor-two]].\n",
        encoding="utf-8",
    )
    (cards / "person-anchor-two.md").write_text(
        "---\n"
        "type: person\n"
        'name: "Anchor Two"\n'
        "---\n\n"
        "Anchor Two collaborates with [[person:anchor]].\n",
        encoding="utf-8",
    )
    return graphs_root, cards


def _fake_lint_pass():
    return ["true"]


def _fake_lint_fail():
    return ["false"]


# ---------- slug / filename derivation ----------

def test_slugify_basic():
    assert slugify("Dave Alvin") == "dave-alvin"
    assert slugify("X") == "x"
    assert slugify("Sugar (Track)") == "sugar-track"


def test_slugify_accents():
    assert slugify("Café del Mar") == "cafe-del-mar"


def test_slugify_empty_raises():
    with pytest.raises(ValueError):
        slugify("")
    with pytest.raises(ValueError):
        slugify("???")


def test_derive_filename_no_collision():
    fname, slug, disambig = derive_filename("person", "Dave Alvin", existing_slugs=set())
    assert fname == "person-dave-alvin.md"
    assert slug == "dave-alvin"
    assert disambig is False


def test_derive_filename_collision_uses_type_suffix():
    """Track named 'Sugar' colliding with an existing slug 'sugar' becomes
    'track-sugar-track.md' (slug == 'sugar-track')."""
    fname, slug, disambig = derive_filename(
        "track", "Sugar", existing_slugs={"sugar"}
    )
    assert fname == "track-sugar-track.md"
    assert slug == "sugar-track"
    assert disambig is True


def test_derive_filename_double_collision_uses_numeric_suffix():
    fname, slug, disambig = derive_filename(
        "track", "Sugar", existing_slugs={"sugar", "sugar-track"}
    )
    assert fname == "track-sugar-track-2.md"
    assert slug == "sugar-track-2"
    assert disambig is True


# ---------- happy-path write ----------

def test_write_card_happy_path(tmp_path):
    graphs_root, cards = _make_graph(tmp_path)
    target = write_card(
        graph="test-graph",
        type="person",
        name="New Person",
        graphs_root=graphs_root,
        repo_root=REPO_ROOT,
        body="New Person is friends with [[person:anchor]].",
        run_lint=False,
    )
    assert target == cards / "person-new-person.md"
    assert target.exists()

    parsed = parse_card(target)
    assert parsed["type"] == "person"
    assert parsed["name"] == "New Person"
    assert parsed["slug"] == "new-person"
    assert ("person", "anchor") in parsed["wikilinks"]


def test_write_card_with_spotify_and_canonical(tmp_path):
    graphs_root, cards = _make_graph(tmp_path)
    target = write_card(
        graph="test-graph",
        type="album",
        name="Ashgrove",
        graphs_root=graphs_root,
        repo_root=REPO_ROOT,
        spotify_url="https://open.spotify.com/album/2At5ShihdUNDdc33Ztp7RX",
        canonical_link="https://en.wikipedia.org/wiki/Ashgrove_(album)",
        body="Solo album by [[person:anchor]].",
        run_lint=False,
    )
    parsed = parse_card(target)
    assert parsed["frontmatter"]["spotify_url"].startswith("https://open.spotify.com/")
    assert parsed["frontmatter"]["canonical_link"].startswith("https://en.wikipedia.org/")


def test_write_card_wikilinks_appended_to_body(tmp_path):
    graphs_root, cards = _make_graph(tmp_path)
    target = write_card(
        graph="test-graph",
        type="album",
        name="Side Project",
        graphs_root=graphs_root,
        repo_root=REPO_ROOT,
        body="A solo album.",
        wikilinks=["person:anchor", ("group", "anchor-band")],
        run_lint=False,
    )
    text = target.read_text()
    assert "[[person:anchor]]" in text
    assert "[[group:anchor-band]]" in text


# ---------- collision handling at write time ----------

def test_write_card_collision_disambiguates(tmp_path):
    graphs_root, cards = _make_graph(tmp_path)
    # Seed an album named 'sugar' first, then add a track 'Sugar'.
    (cards / "album-sugar.md").write_text(
        "---\ntype: album\nname: \"Sugar\"\n---\n\nAlbum [[person:anchor]].\n",
        encoding="utf-8",
    )
    target = write_card(
        graph="test-graph",
        type="track",
        name="Sugar",
        graphs_root=graphs_root,
        repo_root=REPO_ROOT,
        body="Track [[album:sugar]].",
        run_lint=False,
    )
    assert target.name == "track-sugar-track.md"
    parsed = parse_card(target)
    assert parsed["slug"] == "sugar-track"


# ---------- lint gate behavior ----------

def test_write_card_lint_pass(tmp_path):
    graphs_root, cards = _make_graph(tmp_path)
    target = write_card(
        graph="test-graph",
        type="person",
        name="New Person",
        graphs_root=graphs_root,
        repo_root=REPO_ROOT,
        body="Connected to [[person:anchor]].",
        run_lint=True,
        lint_cmd=_fake_lint_pass(),
    )
    assert target.exists()


def test_write_card_lint_failure_rolls_back(tmp_path):
    graphs_root, cards = _make_graph(tmp_path)
    with pytest.raises(LintError) as ei:
        write_card(
            graph="test-graph",
            type="person",
            name="Doomed Card",
            graphs_root=graphs_root,
            repo_root=REPO_ROOT,
            body="orphan body, no wikilinks",
            run_lint=True,
            lint_cmd=_fake_lint_fail(),
        )
    assert ei.value.returncode != 0
    # File must be gone — rollback contract.
    assert not (cards / "person-doomed-card.md").exists()


def test_write_card_real_lint_against_real_graphs(tmp_path):
    """Sanity-check the real lint command runs and exits 0 on a clean graph."""
    graphs_root, cards = _make_graph(tmp_path)
    target = write_card(
        graph="test-graph",
        type="person",
        name="Linked Person",
        graphs_root=graphs_root,
        repo_root=REPO_ROOT,
        body="Friend of [[person:anchor]].",
        run_lint=True,
        # use the default lint_cmd (real tools/lint_graphs.py)
    )
    assert target.exists()


# ---------- error cases ----------

def test_write_card_missing_graph_dir_raises(tmp_path):
    graphs_root = tmp_path / "graphs"
    graphs_root.mkdir()
    with pytest.raises(FileNotFoundError):
        write_card(
            graph="nonexistent",
            type="person",
            name="Nobody",
            graphs_root=graphs_root,
            repo_root=REPO_ROOT,
            run_lint=False,
        )
