"""music-graphs Flask app.

Routes the home + graph view + JSON API for vis-network, plus a
server-rendered single-card page for deep links. Card index (`/cards`)
remains a 501 stub for Track G.
"""

from __future__ import annotations

from pathlib import Path

from flask import Flask, abort, jsonify, render_template

from lib.cards import parse_card
from lib.graph import build_graph, list_graphs
from lib.spotify import spotify_embed_url

app = Flask(__name__)

GRAPHS_ROOT = Path(__file__).parent / "graphs"

# Frontmatter keys to hide from the side-panel definition list; they are
# rendered elsewhere (image, name, type) or used only for embedding (spotify_url).
HIDDEN_FRONTMATTER_KEYS = frozenset({"name", "type", "body", "spotify_url", "image"})

# Spotify embed heights per kind (track default vs album/playlist).
SPOTIFY_TALL_KINDS = frozenset({"album", "playlist", "show"})


def _graph_dir(slug: str) -> Path:
    return GRAPHS_ROOT / slug


def _find_card_path(graph_slug: str, card_slug: str) -> Path | None:
    """Locate a card by its slug (everything after the first ``-`` in the
    filename). Returns None if not found."""
    cards_dir = _graph_dir(graph_slug) / "cards"
    if not cards_dir.is_dir():
        return None
    for md_path in cards_dir.glob("*.md"):
        stem = md_path.stem
        slug = stem.split("-", 1)[1] if "-" in stem else stem
        if slug == card_slug:
            return md_path
    return None


def _build_card_payload(card: dict) -> dict:
    fm = card.get("frontmatter") or {}
    raw_spotify = fm.get("spotify_url") if isinstance(fm, dict) else None
    embed = spotify_embed_url(raw_spotify) if isinstance(raw_spotify, str) else None
    spotify_kind = None
    if embed:
        # embed format: https://open.spotify.com/embed/<kind>/<id>
        try:
            spotify_kind = embed.split("/embed/", 1)[1].split("/", 1)[0]
        except Exception:
            spotify_kind = None
    image = fm.get("image") if isinstance(fm, dict) else None
    display_fm = {
        k: v for k, v in (fm.items() if isinstance(fm, dict) else [])
        if k not in HIDDEN_FRONTMATTER_KEYS
    }
    return {
        "type": card["type"],
        "slug": card["slug"],
        "name": card["name"],
        "frontmatter": fm,
        "display_frontmatter": display_fm,
        "image": image,
        "body_html": card["body_html"],
        "spotify_embed_url": embed,
        "spotify_kind": spotify_kind,
        "spotify_tall": spotify_kind in SPOTIFY_TALL_KINDS if spotify_kind else False,
    }


@app.route("/")
def home():
    graphs = list_graphs(GRAPHS_ROOT)
    return render_template("home.html", graphs=graphs)


@app.route("/graph/<slug>")
def graph_view(slug):
    graphs = {g["slug"]: g for g in list_graphs(GRAPHS_ROOT)}
    if slug not in graphs:
        abort(404)
    g = graphs[slug]
    return render_template(
        "graph.html",
        slug=slug,
        name=g["name"],
        description=g["description"],
    )


@app.route("/api/graph/<slug>")
def api_graph(slug):
    gdir = _graph_dir(slug)
    if not (gdir / "cards").is_dir():
        abort(404)
    return jsonify(build_graph(gdir))


@app.route("/api/card/<graph_slug>/<card_slug>")
def api_card(graph_slug, card_slug):
    path = _find_card_path(graph_slug, card_slug)
    if path is None:
        abort(404)
    card = parse_card(path)
    return jsonify(_build_card_payload(card))


@app.route("/graph/<slug>/card/<card_slug>")
def card_view(slug, card_slug):
    path = _find_card_path(slug, card_slug)
    if path is None:
        abort(404)
    card = parse_card(path)
    payload = _build_card_payload(card)
    return render_template("card.html", slug=slug, card=payload)


@app.route("/cards")
def cards_index():
    # Track G owns this.
    return ("not implemented", 501)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8766, debug=True)
