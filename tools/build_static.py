"""Render the Flask app to a static site for GitHub Pages.

Uses the Flask test client to fetch every route, then writes the responses
to `_site/` mirroring the URL structure. HTML pages are post-processed to:

  - inject `window.MG_BASE` + `window.MG_STATIC = true` so client JS knows
    to prefix API URLs and disable write-only UI;
  - rewrite root-absolute paths (`/static/...`, `/graph/...`, `/cards`,
    `/graph-images/...`) to include the project base path so the site
    works under `https://<user>.github.io/<repo>/`.

API responses are saved with a `.json` extension (e.g.
`_site/api/graph/<slug>.json`) because client JS appends `.json` in static
mode. Image directories under each graph are copied to
`_site/graph-images/<slug>/`.

Usage:
    python tools/build_static.py --base /music-graphs --out _site

If `--base` is empty (e.g. for a custom-domain deploy) all paths stay
absolute at the root.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import app, GRAPHS_ROOT  # noqa: E402
from lib.cards import parse_card  # noqa: E402
from lib.graph import list_graphs  # noqa: E402


def collect_routes() -> list[tuple[str, str, str]]:
    """Return (url, kind, out_path) tuples for every URL we want to render.

    `kind` is "html" or "json"; `out_path` is relative to the output root.
    """
    routes: list[tuple[str, str, str]] = []
    routes.append(("/", "html", "index.html"))
    routes.append(("/cards", "html", "cards/index.html"))

    graphs = list_graphs(GRAPHS_ROOT)
    for g in graphs:
        slug = g["slug"]
        routes.append((f"/graph/{slug}", "html", f"graph/{slug}/index.html"))
        routes.append((f"/api/graph/{slug}", "json", f"api/graph/{slug}.json"))
        routes.append((f"/api/cards/{slug}", "json", f"api/cards/{slug}.json"))

        cards_dir = GRAPHS_ROOT / slug / "cards"
        if not cards_dir.is_dir():
            continue
        for md_path in sorted(cards_dir.glob("*.md")):
            try:
                card = parse_card(md_path)
            except Exception:
                continue
            cslug = card["slug"]
            routes.append((
                f"/graph/{slug}/card/{cslug}",
                "html",
                f"graph/{slug}/card/{cslug}/index.html",
            ))
            routes.append((
                f"/api/card/{slug}/{cslug}",
                "json",
                f"api/card/{slug}/{cslug}.json",
            ))
    return routes


# Root-absolute paths we know about. We rewrite both href="/..." and src="/..."
# attributes plus a handful of URLs that appear inside scripts/JSON payloads.
REWRITE_ATTR_RE = re.compile(r'(href|src)="(/[^"#?]*)([^"]*)"')
# Inside <script id="cards-data"> the JSON contains `"url": "/graph/..."`;
# match anything that looks like a quoted root-absolute path inside that block.
SCRIPT_DATA_URL_RE = re.compile(r'("url"\s*:\s*")(/[^"]+)(")')


def rewrite_html(body: str, base: str) -> str:
    """Inject the static-mode flag + rewrite root-absolute URLs under `base`."""
    flags = (
        f'<script>window.MG_BASE={json.dumps(base)};'
        f'window.MG_STATIC=true;</script>'
    )
    # Inject right after the opening <head>.
    body = re.sub(r"(<head[^>]*>)", r"\1" + flags, body, count=1)

    if not base:
        return body

    def attr_sub(m: re.Match) -> str:
        attr, path, rest = m.group(1), m.group(2), m.group(3)
        # Skip protocol-relative or external — they start with `//`.
        if path.startswith("//"):
            return m.group(0)
        return f'{attr}="{base}{path}{rest}"'

    body = REWRITE_ATTR_RE.sub(attr_sub, body)

    def script_sub(m: re.Match) -> str:
        return f"{m.group(1)}{base}{m.group(2)}{m.group(3)}"

    body = SCRIPT_DATA_URL_RE.sub(script_sub, body)
    return body


def rewrite_json(body_text: str, base: str) -> str:
    """Card JSON payloads include `body_html` with absolute wikilink URLs.

    Same approach as rewrite_html: prefix root-absolute paths with `base`.
    """
    if not base:
        return body_text
    try:
        data = json.loads(body_text)
    except json.JSONDecodeError:
        return body_text
    if isinstance(data, dict) and isinstance(data.get("body_html"), str):
        def attr_sub(m: re.Match) -> str:
            attr, path, rest = m.group(1), m.group(2), m.group(3)
            if path.startswith("//"):
                return m.group(0)
            return f'{attr}="{base}{path}{rest}"'
        data["body_html"] = REWRITE_ATTR_RE.sub(attr_sub, data["body_html"])
        # Also rewrite a top-level `image` field if it's root-absolute.
        if isinstance(data.get("image"), str) and data["image"].startswith("/"):
            data["image"] = base + data["image"]
        if isinstance(data.get("spotify_embed_url"), str):
            pass  # external URL, leave alone.
    return json.dumps(data)


def write_route(client, url: str, kind: str, out_path: Path, base: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    resp = client.get(url)
    if resp.status_code != 200:
        print(f"  ⚠ {url} → {resp.status_code} (skipped)")
        return
    body = resp.get_data(as_text=True)
    if kind == "html":
        body = rewrite_html(body, base)
    elif kind == "json":
        body = rewrite_json(body, base)
    out_path.write_text(body, encoding="utf-8")


def copy_assets(out_root: Path, base: str) -> None:
    # static/ → docs/static/
    static_src = ROOT / "static"
    static_dst = out_root / "static"
    if static_dst.exists():
        shutil.rmtree(static_dst)
    shutil.copytree(static_src, static_dst)

    # graphs/<slug>/images/ → docs/graph-images/<slug>/
    images_root = out_root / "graph-images"
    if images_root.exists():
        shutil.rmtree(images_root)
    for g in list_graphs(GRAPHS_ROOT):
        slug = g["slug"]
        src = GRAPHS_ROOT / slug / "images"
        if not src.is_dir():
            continue
        shutil.copytree(src, images_root / slug)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base", default="/music-graphs",
        help="Project base path (e.g. '/music-graphs' for GH project pages, "
             "'' for a custom domain at root)",
    )
    parser.add_argument(
        "--out", default="_site",
        help="Output directory (default: _site)",
    )
    args = parser.parse_args()

    base = args.base.rstrip("/")
    out_root = (ROOT / args.out).resolve()

    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True)

    print(f"Building static site → {out_root} (base={base or '/'})")

    # `.nojekyll` so GH Pages doesn't strip files starting with `_`.
    (out_root / ".nojekyll").write_text("", encoding="utf-8")

    copy_assets(out_root, base)

    client = app.test_client()
    routes = collect_routes()
    print(f"Rendering {len(routes)} routes…")
    for url, kind, rel in routes:
        write_route(client, url, kind, out_root / rel, base)

    print(f"Done. {sum(1 for _ in out_root.rglob('*') if _.is_file())} files written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
