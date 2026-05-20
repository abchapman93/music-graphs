"""Integration tests for the graph view + API routes using the
``pittsburgh-jazz`` graph."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app  # noqa: E402

SLUG = "pittsburgh-jazz"
KNOWN_CARD_SLUG = "stanley-turrentine"


def _client():
    return app.test_client()


def test_home_lists_fixture():
    body = _client().get("/").get_data(as_text=True)
    assert SLUG in body


def test_graph_view_renders():
    resp = _client().get(f"/graph/{SLUG}")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'id="graph"' in body
    assert "vis-network" in body
    assert f'GRAPH_SLUG = "{SLUG}"' in body
    # K1/K2/K3 — full-bleed graph page with zoom + freeze controls.
    assert 'class="graph-page"' in body
    assert 'id="zoom-in"' in body
    assert 'id="zoom-out"' in body
    assert 'id="zoom-fit"' in body
    assert 'id="freeze-toggle"' in body


def test_graph_view_unknown_404():
    assert _client().get("/graph/does-not-exist").status_code == 404


def test_api_graph_ok():
    resp = _client().get(f"/api/graph/{SLUG}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "nodes" in data and "edges" in data
    assert len(data["nodes"]) >= 5
    assert len(data["edges"]) >= 5
    ids = {n["id"] for n in data["nodes"]}
    assert f"person:{KNOWN_CARD_SLUG}" in ids


def test_api_graph_404():
    assert _client().get("/api/graph/does-not-exist").status_code == 404


def test_api_card_ok():
    resp = _client().get(f"/api/card/{SLUG}/{KNOWN_CARD_SLUG}")
    assert resp.status_code == 200
    data = resp.get_json()
    for key in ("type", "slug", "name", "frontmatter", "body_html", "spotify_embed_url"):
        assert key in data
    assert data["slug"] == KNOWN_CARD_SLUG
    assert data["type"] == "person"


def test_api_card_with_spotify_embed():
    # The "sugar" album card has a real Spotify album URL.
    resp = _client().get(f"/api/card/{SLUG}/sugar")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["spotify_embed_url"] is not None
    assert "open.spotify.com/embed/album/" in data["spotify_embed_url"]


def test_api_card_404():
    assert _client().get(f"/api/card/{SLUG}/does-not-exist").status_code == 404


def test_api_cards_list_ok():
    """N/O — shared `/api/cards/<slug>` index used by search + directory."""
    resp = _client().get(f"/api/cards/{SLUG}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) >= 5
    # Each entry has the documented shape.
    for c in data:
        assert set(c.keys()) == {"slug", "type", "name", "image_url"}
    # Known card present.
    slugs = {c["slug"] for c in data}
    assert KNOWN_CARD_SLUG in slugs
    # Sorted by (type, name.lower()).
    keys = [(c["type"], c["name"].lower()) for c in data]
    assert keys == sorted(keys)


def test_api_cards_list_404():
    assert _client().get("/api/cards/does-not-exist").status_code == 404


def test_graph_view_has_search_and_directory():
    """N/O — graph page exposes the search input + directory panel."""
    body = _client().get(f"/graph/{SLUG}").get_data(as_text=True)
    assert 'id="search-input"' in body
    assert 'id="search-results"' in body
    assert 'id="directory-panel"' in body


def test_card_view_renders():
    resp = _client().get(f"/graph/{SLUG}/card/{KNOWN_CARD_SLUG}")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Stanley Turrentine" in body
    assert "back to graph" in body


def test_card_view_404():
    assert _client().get(f"/graph/{SLUG}/card/does-not-exist").status_code == 404


def test_cards_index_ok():
    resp = _client().get("/cards")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    # At least one card name from the fixture appears.
    assert "Stanley Turrentine" in body
    # type-filter <select> is present with all 9 card type options.
    assert 'id="type-filter"' in body
    for t in ("person", "group", "album", "song", "track",
              "location", "genre", "note", "memory"):
        assert f'value="{t}"' in body
    # search input present
    assert 'id="search"' in body
