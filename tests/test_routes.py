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


def test_put_card_round_trips(tmp_path, monkeypatch):
    """Q1 — PUT writes a new body, preserves frontmatter bit-for-bit, returns
    refreshed payload."""
    # Build a tiny in-tmp graph with two cards (so each has at least one
    # wikilink and lint passes after the edit).
    import app as app_mod
    gdir = tmp_path / "tmpgraph"
    cards = gdir / "cards"
    cards.mkdir(parents=True)
    a = cards.joinpath("person-alpha.md")
    b = cards.joinpath("person-beta.md")
    a.write_bytes(
        b"---\nname: Alpha\ntype: person\n---\nAlpha links to [[person:beta]].\n"
    )
    b.write_bytes(
        b"---\nname: Beta\ntype: person\n---\nBeta links to [[person:alpha]].\n"
    )
    monkeypatch.setattr(app_mod, "GRAPHS_ROOT", tmp_path)

    original_fm = a.read_bytes().split(b"---\n", 2)[1]  # the YAML between fences

    new_body = "Alpha was updated. Still links to [[person:beta]].\n"
    resp = _client().put(
        "/api/cards/tmpgraph/alpha",
        json={"body": new_body},
    )
    assert resp.status_code == 200, resp.get_data(as_text=True)
    payload = resp.get_json()
    assert payload["slug"] == "alpha"
    assert "Alpha was updated" in payload["body_html"]
    assert payload["body_md"].strip() == new_body.strip()

    on_disk = a.read_bytes()
    # Frontmatter block intact byte-for-byte.
    assert on_disk.split(b"---\n", 2)[1] == original_fm
    # Body replaced.
    assert b"Alpha was updated" in on_disk


def test_put_card_lint_failure_reverts(tmp_path, monkeypatch):
    """Q2 — body with a dangling wikilink fails lint; file restored
    bit-for-bit; 422 returned with the lint error."""
    import app as app_mod
    gdir = tmp_path / "tmpgraph"
    cards = gdir / "cards"
    cards.mkdir(parents=True)
    a = cards.joinpath("person-alpha.md")
    b = cards.joinpath("person-beta.md")
    a.write_bytes(
        b"---\nname: Alpha\ntype: person\n---\nAlpha links to [[person:beta]].\n"
    )
    b.write_bytes(
        b"---\nname: Beta\ntype: person\n---\nBeta links to [[person:alpha]].\n"
    )
    monkeypatch.setattr(app_mod, "GRAPHS_ROOT", tmp_path)
    original = a.read_bytes()

    resp = _client().put(
        "/api/cards/tmpgraph/alpha",
        json={"body": "Broken link to [[person:nope-not-real]].\n"},
    )
    assert resp.status_code == 422
    data = resp.get_json()
    assert "lint" in data.get("error", "").lower()
    assert "nope-not-real" in (data.get("stdout") or "")
    # File restored bit-for-bit.
    assert a.read_bytes() == original


def test_get_card_includes_body_md():
    """Q — `/api/card/<g>/<s>` exposes raw markdown body so the editor can
    load source verbatim."""
    resp = _client().get(f"/api/card/{SLUG}/{KNOWN_CARD_SLUG}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data.get("body_md"), str)
    assert len(data["body_md"]) > 0
    # Raw markdown is the source — should contain a wikilink token, not HTML.
    assert "[[" in data["body_md"]


def test_cancel_does_not_touch_file(tmp_path, monkeypatch):
    """Q3 — cancel discards changes without writing. Modeled as the API
    contract: opening the editor (GET) followed by no PUT leaves the file
    bit-for-bit unchanged. The frontend Cancel button bypasses fetch."""
    import app as app_mod
    gdir = tmp_path / "tmpgraph"
    cards = gdir / "cards"
    cards.mkdir(parents=True)
    a = cards.joinpath("person-alpha.md")
    b = cards.joinpath("person-beta.md")
    a.write_bytes(
        b"---\nname: Alpha\ntype: person\n---\nAlpha links to [[person:beta]].\n"
    )
    b.write_bytes(
        b"---\nname: Beta\ntype: person\n---\nBeta links to [[person:alpha]].\n"
    )
    monkeypatch.setattr(app_mod, "GRAPHS_ROOT", tmp_path)
    original = a.read_bytes()
    mtime_before = a.stat().st_mtime_ns

    # Open the editor (GET source).
    resp = _client().get("/api/card/tmpgraph/alpha")
    assert resp.status_code == 200
    assert "Alpha links to" in resp.get_json()["body_md"]
    # No PUT — simulate Cancel.
    assert a.read_bytes() == original
    assert a.stat().st_mtime_ns == mtime_before


def test_put_card_404_when_missing(tmp_path, monkeypatch):
    """Edge — missing card returns 404 (UI keeps textarea content)."""
    import app as app_mod
    monkeypatch.setattr(app_mod, "GRAPHS_ROOT", tmp_path)
    resp = _client().put(
        "/api/cards/does-not-exist/whatever",
        json={"body": "anything"},
    )
    assert resp.status_code == 404


def _seed_tmp_graph(tmp_path):
    """Build a minimal tmp graph with two linked cards used by Track R tests."""
    gdir = tmp_path / "tmpgraph"
    cards = gdir / "cards"
    cards.mkdir(parents=True)
    cards.joinpath("person-alpha.md").write_bytes(
        b"---\nname: Alpha\ntype: person\n---\nAlpha links to [[person:beta]].\n"
    )
    cards.joinpath("person-beta.md").write_bytes(
        b"---\nname: Beta\ntype: person\n---\nBeta links to [[person:alpha]].\n"
    )
    return gdir


def test_post_note_creates_card(tmp_path, monkeypatch):
    """R1 — POST creates a new note-*.md card with frontmatter + body and lint passes."""
    import app as app_mod
    gdir = _seed_tmp_graph(tmp_path)
    monkeypatch.setattr(app_mod, "GRAPHS_ROOT", tmp_path)

    resp = _client().post(
        "/api/notes/tmpgraph",
        json={
            "type": "note",
            "title": "Studio anecdote",
            "body": "Heard this on the studio tour.",
            "source_slug": "alpha",
            "source_type": "person",
        },
    )
    assert resp.status_code == 200, resp.get_data(as_text=True)
    payload = resp.get_json()
    assert payload["type"] == "note"
    assert payload["slug"] == "studio-anecdote"
    assert payload["name"] == "Studio anecdote"
    assert payload["url"] == "/graph/tmpgraph/card/studio-anecdote"

    new_path = gdir / "cards" / "note-studio-anecdote.md"
    assert new_path.is_file()
    body_text = new_path.read_text(encoding="utf-8")
    assert "type: note" in body_text
    assert 'name: "Studio anecdote"' in body_text
    assert "Heard this on the studio tour." in body_text


def test_post_note_writes_edge_back(tmp_path, monkeypatch):
    """R2 — source card body gains a `[[note:<slug>]]` wikilink edge."""
    import app as app_mod
    gdir = _seed_tmp_graph(tmp_path)
    monkeypatch.setattr(app_mod, "GRAPHS_ROOT", tmp_path)

    resp = _client().post(
        "/api/notes/tmpgraph",
        json={
            "type": "memory",
            "title": "Backstage memory",
            "body": "Backstage at the Birdland gig.",
            "source_slug": "alpha",
            "source_type": "person",
        },
    )
    assert resp.status_code == 200, resp.get_data(as_text=True)
    payload = resp.get_json()
    assert payload["type"] == "memory"

    src_text = (gdir / "cards" / "person-alpha.md").read_text(encoding="utf-8")
    assert f"[[memory:{payload['slug']}" in src_text


def test_post_note_lint_failure_reverts(tmp_path, monkeypatch):
    """R3 — lint failure during note create reverts both writes and returns 422.

    Force a lint failure by stubbing ``lint_graph`` to return an error list.
    Verifies the new card file is deleted and the source card is restored
    bit-for-bit.
    """
    import app as app_mod
    gdir = _seed_tmp_graph(tmp_path)
    monkeypatch.setattr(app_mod, "GRAPHS_ROOT", tmp_path)

    src_before = (gdir / "cards" / "person-alpha.md").read_bytes()
    monkeypatch.setattr(
        app_mod, "lint_graph", lambda _gdir: ["tmpgraph: synthetic lint failure"]
    )

    resp = _client().post(
        "/api/notes/tmpgraph",
        json={
            "type": "note",
            "title": "Doomed note",
            "body": "Should be rolled back.",
            "source_slug": "alpha",
            "source_type": "person",
        },
    )
    assert resp.status_code == 422
    data = resp.get_json()
    assert "lint" in data.get("error", "").lower()
    assert "synthetic lint failure" in (data.get("stdout") or "")

    # New file gone, source restored bit-for-bit.
    assert not (gdir / "cards" / "note-doomed-note.md").exists()
    assert (gdir / "cards" / "person-alpha.md").read_bytes() == src_before


def test_post_note_validation_errors(tmp_path, monkeypatch):
    """Edge — invalid type/title/body rejected with 400."""
    import app as app_mod
    _seed_tmp_graph(tmp_path)
    monkeypatch.setattr(app_mod, "GRAPHS_ROOT", tmp_path)

    bad_type = _client().post(
        "/api/notes/tmpgraph",
        json={"type": "person", "title": "ok title", "body": "ok",
              "source_slug": "alpha", "source_type": "person"},
    )
    assert bad_type.status_code == 400

    short_title = _client().post(
        "/api/notes/tmpgraph",
        json={"type": "note", "title": "xy", "body": "ok",
              "source_slug": "alpha", "source_type": "person"},
    )
    assert short_title.status_code == 400


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
