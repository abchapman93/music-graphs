"""
graph.py — Build vis-network graph JSON from a folder of markdown cards.

Public API:
    build_graph(graph_dir)  -> {"nodes": [...], "edges": [...]}
    list_graphs(graphs_root) -> [{"slug","name","description","cover_image","card_count"}, ...]

Pure-Python. No Flask imports. Wired into app.py by Track E.
"""

from __future__ import annotations

import logging
from pathlib import Path

import frontmatter

from lib.cards import parse_card

logger = logging.getLogger(__name__)


def build_graph(graph_dir: Path) -> dict:
    """Parse every ``cards/*.md`` under ``graph_dir`` and return graph JSON.

    Nodes are deterministic (sorted by id). Edges are de-duplicated as
    undirected pairs (A→B and B→A collapse to a single edge), self-loops are
    dropped, and dangling wikilinks (target card not present in the folder)
    are logged at DEBUG and excluded.
    """
    graph_dir = Path(graph_dir)
    cards_dir = graph_dir / "cards"

    nodes_by_id: dict[str, dict] = {}
    # Track (source_id, wikilinks) so we can emit edges only after all nodes
    # are known (needed to detect dangling links).
    pending: list[tuple[str, list[tuple[str, str]]]] = []

    if cards_dir.is_dir():
        for md_path in sorted(cards_dir.glob("*.md")):
            try:
                card = parse_card(md_path)
            except ValueError as e:
                logger.debug("Skipping unparseable card %s: %s", md_path, e)
                continue
            node_id = f"{card['type']}:{card['slug']}"
            nodes_by_id[node_id] = {
                "id": node_id,
                "label": card["name"],
                "group": card["type"],
                "title": f"{card['name']} ({card['type']})",
            }
            pending.append((node_id, card["wikilinks"]))

    # Resolve edges. Use a frozenset key for undirected dedup.
    edge_keys: set[frozenset] = set()
    edges: list[dict] = []
    for source_id, wikilinks in pending:
        for t, slug in wikilinks:
            target_id = f"{t}:{slug}"
            if target_id not in nodes_by_id:
                logger.debug(
                    "Dangling wikilink in %s -> %s (target card not in folder)",
                    source_id, target_id,
                )
                continue
            if target_id == source_id:
                # Self-loop: drop.
                continue
            key = frozenset((source_id, target_id))
            if key in edge_keys:
                continue
            edge_keys.add(key)
            edges.append({"from": source_id, "to": target_id})

    nodes = [nodes_by_id[k] for k in sorted(nodes_by_id)]
    edges.sort(key=lambda e: (e["from"], e["to"]))
    return {"nodes": nodes, "edges": edges}


def list_graphs(graphs_root: Path) -> list[dict]:
    """List graph folders under ``graphs_root``.

    A folder counts as a graph if it contains a ``cards/`` subfolder.
    For each, read ``<slug>/README.md`` frontmatter for ``name``,
    ``description``, ``cover_image``; fall back gracefully if missing.
    ``card_count`` counts ``*.md`` files in ``cards/``. Sorted by slug.
    """
    graphs_root = Path(graphs_root)
    out: list[dict] = []
    if not graphs_root.is_dir():
        return out

    for child in sorted(graphs_root.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        cards_dir = child / "cards"
        if not cards_dir.is_dir():
            continue

        slug = child.name
        name = slug
        description = ""
        cover_image = None

        readme = child / "README.md"
        if readme.is_file():
            try:
                post = frontmatter.load(str(readme))
                fm = dict(post.metadata or {})
                name = str(fm.get("name") or slug)
                description = str(fm.get("description") or "")
                cover_image = fm.get("cover_image") or None
            except Exception as e:
                logger.debug("Failed to parse README for %s: %s", slug, e)

        card_count = sum(1 for _ in cards_dir.glob("*.md"))

        out.append({
            "slug": slug,
            "name": name,
            "description": description,
            "cover_image": cover_image,
            "card_count": card_count,
        })

    return out
