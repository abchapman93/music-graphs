"""Collect Spotify-bearing cards from a music-graphs graph.

Usage:
    python -m .claude.skills.graph-to-playlist.scripts.collect_tracks <graph> [--types track,album]

Or directly:
    python .claude/skills/graph-to-playlist/scripts/collect_tracks.py <graph>

Outputs JSON to stdout: a list of {type, name, slug, spotify_url, spotify_uri}
objects, deduped by spotify_uri and stable-ordered by (type, slug).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lib.cards import parse_card  # noqa: E402

# Match canonical embed URLs that lib.spotify already normalizes.
SPOTIFY_URL_RE = re.compile(
    r"^https?://open\.spotify\.com/(track|album|playlist|artist|show|episode)/([A-Za-z0-9]+)/?"
)


def url_to_uri(url: str) -> tuple[str, str] | None:
    """Return (kind, spotify:kind:id) for a canonical open.spotify.com URL, else None."""
    if not isinstance(url, str):
        return None
    m = SPOTIFY_URL_RE.match(url.strip())
    if not m:
        return None
    return m.group(1), f"spotify:{m.group(1)}:{m.group(2)}"


def collect(graph: str, types: set[str], repo_root: Path) -> list[dict]:
    cards_dir = repo_root / "graphs" / graph / "cards"
    if not cards_dir.is_dir():
        raise SystemExit(f"No such graph: {graph} (looked at {cards_dir})")

    seen_uris: set[str] = set()
    out: list[dict] = []
    for path in sorted(cards_dir.glob("*.md")):
        try:
            card = parse_card(path)
        except Exception:
            # Skip malformed cards; surfacing is the linter's job, not ours.
            continue
        if card["type"] not in types:
            continue
        spotify_url = (card.get("frontmatter") or {}).get("spotify_url")
        parsed = url_to_uri(spotify_url) if spotify_url else None
        if not parsed:
            continue
        kind, uri = parsed
        if uri in seen_uris:
            continue
        seen_uris.add(uri)
        out.append(
            {
                "type": card["type"],
                "name": card["name"],
                "slug": card["slug"],
                "spotify_url": spotify_url,
                "spotify_uri": uri,
                "spotify_kind": kind,
            }
        )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", help="Graph slug (folder under graphs/)")
    parser.add_argument(
        "--types",
        default="track",
        help="Comma-separated card types to include (default: track). E.g. track,album",
    )
    args = parser.parse_args(argv)

    types = {t.strip() for t in args.types.split(",") if t.strip()}
    items = collect(args.graph, types, REPO_ROOT)
    json.dump(items, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
