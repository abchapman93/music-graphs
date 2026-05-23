"""music-graphs Flask app.

Routes the home + graph view + JSON API for vis-network, plus a
server-rendered single-card page for deep links. Card index (`/cards`)
remains a 501 stub for Track G.
"""

from __future__ import annotations

from pathlib import Path

import sys

from flask import Flask, abort, jsonify, render_template, request, send_from_directory

from lib.cards import parse_card, split_frontmatter_bytes

# Import the per-graph linter so writes can be gated without shelling out
# (subprocess works too but importing keeps it in-process and per-graph).
sys.path.insert(0, str(Path(__file__).parent))
from tools.lint_graphs import lint_graph  # noqa: E402
from lib.graph import build_graph, list_graphs
from lib.spotify import spotify_embed_url

# Skill libs reused by the note-creation endpoint (Track R).
_SKILLS_ROOT = Path(__file__).parent / ".claude" / "skills"
sys.path.insert(0, str(_SKILLS_ROOT / "add-node" / "scripts"))
sys.path.insert(0, str(_SKILLS_ROOT / "add-edge" / "scripts"))
from write_card import write_card  # noqa: E402
from add_edge import add_edge, CardNotFoundError  # noqa: E402

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
        "body_md": card.get("body_md", ""),
        "spotify_embed_url": embed,
        "spotify_kind": spotify_kind,
        "spotify_tall": spotify_kind in SPOTIFY_TALL_KINDS if spotify_kind else False,
    }


@app.route("/graph-images/<slug>/<path:filename>")
def graph_image(slug, filename):
    """Serve images committed under ``graphs/<slug>/images/``.

    Used by graph READMEs that reference local cover images via a relative
    ``images/...`` path. Resolves to ``GRAPHS_ROOT/<slug>/images/<filename>``.
    """
    images_dir = _graph_dir(slug) / "images"
    if not images_dir.is_dir():
        abort(404)
    return send_from_directory(images_dir, filename)


def _resolve_cover_image(slug: str, cover: str | None) -> str | None:
    """Rewrite a relative ``images/...`` cover_image to the graph-images route.

    Absolute (``http(s)://``) URLs pass through unchanged.
    """
    if not cover:
        return None
    if cover.startswith(("http://", "https://", "/")):
        return cover
    if cover.startswith("images/"):
        return f"/graph-images/{slug}/{cover[len('images/'):]}"
    return cover


@app.route("/")
def home():
    graphs = list_graphs(GRAPHS_ROOT)
    for g in graphs:
        g["cover_image"] = _resolve_cover_image(g["slug"], g.get("cover_image"))
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
        spotify_playlist_url=g.get("spotify_playlist_url"),
    )


@app.route("/api/graph/<slug>")
def api_graph(slug):
    gdir = _graph_dir(slug)
    if not (gdir / "cards").is_dir():
        abort(404)
    return jsonify(build_graph(gdir))


@app.route("/api/cards/<graph_slug>")
def api_cards(graph_slug):
    """JSON list of every card in a graph for client-side search + directory.

    Returns ``[{slug, type, name, image_url|null}, ...]`` sorted by
    ``(type, name.lower())``. Files that fail to parse are skipped.
    """
    cards_dir = _graph_dir(graph_slug) / "cards"
    if not cards_dir.is_dir():
        abort(404)
    out: list[dict] = []
    for md_path in cards_dir.glob("*.md"):
        try:
            card = parse_card(md_path)
        except (ValueError, Exception):
            continue
        fm = card.get("frontmatter") or {}
        image = fm.get("image") if isinstance(fm, dict) else None
        out.append({
            "slug": card["slug"],
            "type": card["type"],
            "name": card["name"],
            "image_url": image,
        })
    out.sort(key=lambda c: (c["type"], c["name"].lower()))
    return jsonify(out)


@app.route("/api/card/<graph_slug>/<card_slug>")
def api_card(graph_slug, card_slug):
    path = _find_card_path(graph_slug, card_slug)
    if path is None:
        abort(404)
    card = parse_card(path)
    return jsonify(_build_card_payload(card))


@app.route("/api/cards/<graph_slug>/<card_slug>", methods=["PUT"])
def api_update_card(graph_slug, card_slug):
    """Replace the body (markdown after frontmatter) of a card on disk.

    Request body: ``{"body": "<markdown>"}``. Frontmatter is preserved
    bit-for-bit — we re-emit the original frontmatter block verbatim and
    rewrite only the body bytes that follow. On lint failure the file is
    restored from the in-memory backup and a 422 is returned with the
    lint output so the editor can surface it inline.
    """
    path = _find_card_path(graph_slug, card_slug)
    if path is None:
        abort(404)
    payload = request.get_json(silent=True) or {}
    new_body = payload.get("body")
    if not isinstance(new_body, str):
        return jsonify({"error": "missing or non-string 'body' field"}), 400

    original_bytes = path.read_bytes()
    split = split_frontmatter_bytes(original_bytes)
    if split is None:
        return jsonify({
            "error": "frontmatter parse failed — refusing to edit",
        }), 422
    fm_block, _old_body = split

    # Ensure the new body starts on its own line and ends with a single
    # trailing newline so the file remains well-formed.
    body_bytes = new_body.encode("utf-8")
    if body_bytes and not body_bytes.endswith(b"\n"):
        body_bytes += b"\n"
    new_bytes = fm_block + body_bytes

    path.write_bytes(new_bytes)

    # Lint only the affected graph. Any error reverts the write.
    errs = lint_graph(_graph_dir(graph_slug))
    if errs:
        path.write_bytes(original_bytes)
        return jsonify({
            "error": "lint failed; changes reverted",
            "stdout": "\n".join(errs),
            "stderr": "",
        }), 422

    card = parse_card(path)
    return jsonify(_build_card_payload(card))


@app.route("/api/notes/<graph_slug>", methods=["POST"])
def api_create_note(graph_slug):
    """Create a new ``note-*.md`` or ``memory-*.md`` card and write a wikilink
    edge from the source card body to the new card.

    Request body: ``{type, title, body, source_slug, source_type}``.

    Implementation:
    - Delegate the card write to ``add-node`` skill's ``write_card``.
    - Delegate the edge insertion to ``add-edge`` skill's ``add_edge``.
    - Run ``lint_graph`` in-process over the affected graph.
    - On lint failure: delete the new file and restore the source body from
      the in-memory backup; return 422 with the lint output.
    """
    gdir = _graph_dir(graph_slug)
    if not (gdir / "cards").is_dir():
        abort(404)

    payload = request.get_json(silent=True) or {}
    note_type = payload.get("type")
    title = payload.get("title")
    body = payload.get("body")
    source_slug = payload.get("source_slug")
    source_type = payload.get("source_type")

    if note_type not in ("note", "memory"):
        return jsonify({"error": "type must be 'note' or 'memory'"}), 400
    if not isinstance(title, str) or len(title.strip()) < 3:
        return jsonify({"error": "title is required (>=3 chars)"}), 400
    if not isinstance(body, str) or len(body.strip()) < 1:
        return jsonify({"error": "body is required"}), 400
    if not isinstance(source_slug, str) or not source_slug:
        return jsonify({"error": "source_slug is required"}), 400
    if not isinstance(source_type, str) or not source_type:
        return jsonify({"error": "source_type is required"}), 400

    source_path = _find_card_path(graph_slug, source_slug)
    if source_path is None:
        return jsonify({"error": f"source card not found: {source_slug}"}), 404
    source_backup = source_path.read_bytes()

    repo_root = Path(__file__).parent
    graphs_root = GRAPHS_ROOT

    # 1) Write the new card. Skip the skill's lint — we lint once at the end.
    try:
        new_path = write_card(
            graph_slug,
            note_type,
            title.strip(),
            repo_root=repo_root,
            graphs_root=graphs_root,
            body=body.strip(),
            run_lint=False,
        )
    except (FileExistsError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    new_slug = new_path.stem.split("-", 1)[1] if "-" in new_path.stem else new_path.stem

    # 2) Add the edge from source -> new note. Skip the skill's lint here too;
    #    skill default is one-way (symmetric=False), no relationship verb.
    try:
        add_edge(
            graph_slug,
            source_slug,
            new_slug,
            repo_root=repo_root,
            graphs_root=graphs_root,
            run_lint=False,
        )
    except CardNotFoundError as exc:
        new_path.unlink(missing_ok=True)
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:
        new_path.unlink(missing_ok=True)
        return jsonify({"error": f"add_edge failed: {exc}"}), 422

    # 3) Lint the affected graph in-process. Revert both writes on failure.
    errs = lint_graph(gdir)
    if errs:
        new_path.unlink(missing_ok=True)
        source_path.write_bytes(source_backup)
        return jsonify({
            "error": "lint failed; changes reverted",
            "stdout": "\n".join(errs),
            "stderr": "",
        }), 422

    return jsonify({
        "slug": new_slug,
        "type": note_type,
        "name": title.strip(),
        "url": f"/graph/{graph_slug}/card/{new_slug}",
    })


@app.route("/graph/<slug>/card/<card_slug>")
def card_view(slug, card_slug):
    path = _find_card_path(slug, card_slug)
    if path is None:
        abort(404)
    card = parse_card(path)
    payload = _build_card_payload(card)
    return render_template("card.html", slug=slug, card=payload)


CARD_TYPES = (
    "person", "group", "album", "song", "track",
    "location", "genre", "note", "memory",
)


@app.route("/cards")
def cards_index():
    """Flat index of every card across every graph.

    Server walks `graphs/<slug>/cards/*.md` and emits a JSON list of card
    entries that the template embeds for client-side filtering.
    """
    graphs = list_graphs(GRAPHS_ROOT)
    cards: list[dict] = []
    for g in graphs:
        gslug = g["slug"]
        cards_dir = _graph_dir(gslug) / "cards"
        if not cards_dir.is_dir():
            continue
        for md_path in sorted(cards_dir.glob("*.md")):
            try:
                card = parse_card(md_path)
            except ValueError:
                continue
            fm = card.get("frontmatter") or {}
            image = fm.get("image") if isinstance(fm, dict) else None
            cards.append({
                "graph_slug": gslug,
                "graph_name": g["name"],
                "card_slug": card["slug"],
                "type": card["type"],
                "name": card["name"],
                "image": image,
                "url": f"/graph/{gslug}/card/{card['slug']}",
            })
    cards.sort(key=lambda c: (c["name"].lower(), c["graph_slug"]))
    return render_template(
        "cards.html",
        cards=cards,
        card_types=CARD_TYPES,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8766, debug=True)
