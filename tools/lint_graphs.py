"""Lint music-graphs graph folders.

Reports:
- Cards missing required frontmatter (type, name).
- Dangling wikilinks (target card absent from same graph).
- Orphan nodes (no inbound or outbound edges).
- Cards with `spotify_url` not matching the embed-URL regex.

Usage:
    python tools/lint_graphs.py [graphs_root]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.cards import parse_card, extract_wikilinks  # noqa: E402
import frontmatter  # noqa: E402

SPOTIFY_RE = re.compile(
    r"^https://open\.spotify\.com/(track|album|playlist|artist|episode|show)/[A-Za-z0-9]+"
)


def lint_graph(graph_dir: Path) -> list[str]:
    errs: list[str] = []
    cards_dir = graph_dir / "cards"
    if not cards_dir.is_dir():
        return [f"{graph_dir}: no cards/ folder"]

    cards: dict[str, dict] = {}
    inbound: dict[str, int] = {}
    outbound: dict[str, int] = {}

    for p in sorted(cards_dir.glob("*.md")):
        try:
            c = parse_card(p)
        except ValueError as e:
            errs.append(f"{p}: {e}")
            continue
        node_id = f"{c['type']}:{c['slug']}"
        cards[node_id] = c
        outbound.setdefault(node_id, 0)
        inbound.setdefault(node_id, 0)

        sp = c["frontmatter"].get("spotify_url")
        if sp and not SPOTIFY_RE.match(str(sp)):
            errs.append(f"{p}: spotify_url does not match embed regex: {sp}")

    for node_id, c in cards.items():
        for t, slug in c["wikilinks"]:
            target = f"{t}:{slug}"
            if target == node_id:
                continue
            if target not in cards:
                errs.append(f"{graph_dir.name}/{node_id}: dangling wikilink -> {target}")
            else:
                outbound[node_id] = outbound.get(node_id, 0) + 1
                inbound[target] = inbound.get(target, 0) + 1

    for node_id in cards:
        if inbound.get(node_id, 0) == 0 and outbound.get(node_id, 0) == 0:
            errs.append(f"{graph_dir.name}/{node_id}: orphan node (no edges)")

    return errs


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else ROOT / "graphs"
    total = 0
    for graph in sorted(root.iterdir()):
        if not graph.is_dir() or not (graph / "cards").is_dir():
            continue
        errs = lint_graph(graph)
        print(f"== {graph.name} ==")
        if not errs:
            print("  OK")
        else:
            for e in errs:
                print(f"  {e}")
            total += len(errs)
    print(f"\nTotal errors: {total}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
