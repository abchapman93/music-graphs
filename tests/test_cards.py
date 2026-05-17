"""Unit tests for lib.cards."""

from pathlib import Path

import pytest

from lib.cards import extract_wikilinks, parse_card

FIXTURES = Path(__file__).parent / "fixtures"


# ─── extract_wikilinks ──────────────────────────────────────────────────────


def test_extract_simple():
    assert extract_wikilinks("hello [[person:foo]] world") == [("person", "foo")]


def test_extract_with_display():
    assert extract_wikilinks("[[person:foo|Foo Bar]]") == [("person", "foo")]


def test_extract_multiple_in_one_line():
    text = "[[person:foo]] and [[album:bar|Bar]] and [[track:baz]]"
    assert extract_wikilinks(text) == [
        ("person", "foo"),
        ("album", "bar"),
        ("track", "baz"),
    ]


def test_extract_dedupes_preserving_order():
    text = "[[person:foo]] [[album:bar]] [[person:foo|again]] [[person:foo]]"
    assert extract_wikilinks(text) == [("person", "foo"), ("album", "bar")]


def test_extract_no_match_returns_empty():
    assert extract_wikilinks("nothing to see here") == []
    assert extract_wikilinks("") == []


def test_extract_tolerates_whitespace():
    text = "[[ person : foo ]] and [[person:bar | Display ]]"
    assert extract_wikilinks(text) == [("person", "foo"), ("person", "bar")]


# ─── parse_card ─────────────────────────────────────────────────────────────


def test_parse_card_schema():
    card = parse_card(FIXTURES / "person-stanley-turrentine.md")
    # We'll create that file by symlinking sample_card via fixture below.
    assert card["type"] == "person"
    assert card["slug"] == "stanley-turrentine"
    assert card["name"] == "Stanley Turrentine"
    assert isinstance(card["frontmatter"], dict)
    assert card["frontmatter"]["birth_date"]
    assert isinstance(card["body_md"], str) and "Pittsburgh" in card["body_md"]
    assert "spotify_embed" not in card  # Track E wires this


def test_parse_card_body_html_has_anchors():
    card = parse_card(FIXTURES / "person-stanley-turrentine.md")
    html = card["body_html"]
    assert 'data-wikilink="location:pittsburgh"' in html
    assert 'href="#location:pittsburgh"' in html
    assert 'class="wikilink"' in html
    # Display text preserved
    assert ">Pittsburgh<" in html


def test_parse_card_wikilinks_merge_frontmatter_and_body():
    card = parse_card(FIXTURES / "person-stanley-turrentine.md")
    wl = card["wikilinks"]
    # From frontmatter
    assert ("location", "pittsburgh") in wl
    assert ("genre", "hard-bop") in wl
    assert ("person", "max-roach") in wl
    # From body
    assert ("group", "blue-note") in wl
    # No duplicates
    assert len(wl) == len(set(wl))


def test_parse_card_slug_from_filename_with_type_prefix():
    card = parse_card(FIXTURES / "person-stanley-turrentine.md")
    assert card["slug"] == "stanley-turrentine"


def test_parse_card_slug_falls_back_to_full_stem(tmp_path):
    p = tmp_path / "loner.md"
    p.write_text("---\ntype: note\nname: Loner\n---\n\nhi\n")
    card = parse_card(p)
    assert card["slug"] == "loner"


def test_parse_card_missing_type_raises():
    with pytest.raises(ValueError, match="type"):
        parse_card(FIXTURES / "missing_type.md")


def test_parse_card_missing_name_raises(tmp_path):
    p = tmp_path / "person-noname.md"
    p.write_text("---\ntype: person\n---\n\nbody\n")
    with pytest.raises(ValueError) as exc:
        parse_card(p)
    assert "name" in str(exc.value)
    assert str(p) in str(exc.value)


def test_parse_card_minimal():
    card = parse_card(FIXTURES / "track-only.md")
    assert card["type"] == "track"
    assert card["slug"] == "only"  # "track-only" → after first "-" is "only"
    assert card["name"] == "Sugar"
    assert card["wikilinks"] == []
