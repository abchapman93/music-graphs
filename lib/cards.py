"""
cards.py — Parse music-graphs markdown cards.

Each card is a YAML-frontmatter + markdown body file at
``graphs/<graph>/cards/<type>-<slug>.md``. Bodies and frontmatter values may
contain ``[[type:slug]]`` or ``[[type:slug|Display Text]]`` wikilinks that
become edges in the graph view.

Public API:
    extract_wikilinks(text) -> list[tuple[str, str]]
    parse_card(path)         -> dict
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import frontmatter
import markdown as md

# Wikilink format: [[type:slug]] or [[type:slug|Display Text]].
# Permissive about whitespace inside the brackets and around the colon/pipe.
# Card types are not pinned here (Phase 1 schema is loose); the type is any
# lowercase word.
WIKILINK_RE = re.compile(
    r"""
    \[\[\s*
    ([a-zA-Z][a-zA-Z0-9_-]*)   # 1: type
    \s*:\s*
    ([a-zA-Z0-9][a-zA-Z0-9._\-]*)  # 2: slug
    \s*
    (?:\|\s*([^\]]*?)\s*)?      # 3: optional display text
    \s*\]\]
    """,
    re.VERBOSE,
)


def extract_wikilinks(text: str) -> list[tuple[str, str]]:
    """Return ordered, de-duplicated ``(type, slug)`` tuples found in ``text``.

    Handles ``[[type:slug]]`` and ``[[type:slug|Display]]`` and tolerates
    whitespace inside the brackets. The display text (if any) is ignored
    for extraction purposes. Returns ``[]`` on no match.
    """
    if not text:
        return []
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for m in WIKILINK_RE.finditer(text):
        key = (m.group(1), m.group(2))
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def _rewrite_wikilinks(text: str) -> str:
    """Replace ``[[type:slug|Display]]`` with an HTML anchor.

    Anchor shape:
        <a href="#{type}:{slug}" data-wikilink="{type}:{slug}"
           class="wikilink">{display}</a>

    Applied to the raw markdown body before rendering so the rendered HTML
    contains the anchor inline.
    """
    def repl(m: re.Match) -> str:
        t, slug, display = m.group(1), m.group(2), m.group(3)
        label = display if display else f"{t}:{slug}"
        return (
            f'<a href="#{t}:{slug}" data-wikilink="{t}:{slug}" '
            f'class="wikilink">{label}</a>'
        )
    return WIKILINK_RE.sub(repl, text)


def _walk_strings(value) -> Iterable[str]:
    """Yield every string scalar reachable inside a frontmatter value."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _walk_strings(v)
    elif isinstance(value, (list, tuple, set)):
        for v in value:
            yield from _walk_strings(v)
    # Other scalars (int, float, bool, None, date) cannot contain wikilinks.


def _derive_slug(stem: str) -> str:
    """Filename stem → card slug.

    Filenames follow ``<type>-<slug>.md``; the slug is everything after the
    first hyphen. Files without a hyphen fall back to the full stem.
    """
    if "-" not in stem:
        return stem
    return stem.split("-", 1)[1]


def split_frontmatter_bytes(raw: bytes) -> tuple[bytes, bytes] | None:
    """Split a card file's bytes into (frontmatter_block, body_bytes).

    The frontmatter block includes the leading ``---`` line, the YAML body,
    and the closing ``---`` line plus its trailing newline. The body is
    everything after — preserved bit-for-bit so the frontmatter can be
    re-emitted verbatim alongside a new body.

    Returns ``None`` if the file does not start with a ``---`` fence or
    the closing fence cannot be found.
    """
    # Accept both \n and \r\n line endings; emit them back unchanged.
    # We only need to locate the two fence lines.
    if not raw.startswith(b"---"):
        return None
    # Require a newline after the opening fence.
    nl = raw.find(b"\n", 3)
    if nl < 0:
        return None
    # Opening fence line must be exactly "---" (allow trailing \r).
    opening = raw[:nl].rstrip(b"\r")
    if opening != b"---":
        return None
    # Search for a closing "---" on its own line.
    search_from = nl + 1
    while True:
        idx = raw.find(b"\n---", search_from - 1)
        if idx < 0:
            return None
        # idx points at the "\n" before "---". The closing fence starts at idx+1.
        end_of_fence_line = raw.find(b"\n", idx + 1)
        if end_of_fence_line < 0:
            # Closing fence with no trailing newline — treat as end of file.
            line = raw[idx + 1:].rstrip(b"\r")
            if line == b"---":
                return raw[: len(raw)], b""
            search_from = idx + 4
            continue
        line = raw[idx + 1: end_of_fence_line].rstrip(b"\r")
        if line == b"---":
            fm_block = raw[: end_of_fence_line + 1]
            body = raw[end_of_fence_line + 1:]
            return fm_block, body
        search_from = end_of_fence_line + 1


def parse_card(path: Path) -> dict:
    """Parse a markdown card file and return the schema documented in
    ``docs/plans/sprint_05172026/project_spec.md`` (section "Parsed card").

    Required frontmatter keys: ``type``, ``name``. Missing either raises
    ``ValueError`` naming the offending path.

    Notes
    -----
    - Wikilinks are extracted from both the raw body and every string scalar
      reachable inside the frontmatter (recursive walk), then merged in
      first-seen order with duplicates dropped.
    - ``body_html`` is markdown-rendered HTML with wikilinks already rewritten
      to anchors. Consumers should render it as-is.
    - ``spotify_embed`` is intentionally **omitted** from this output. Track E
      will compute the embed URL at request time in ``app.py`` from
      ``frontmatter["spotify_url"]`` using ``lib.spotify.spotify_embed_url``.
      That keeps ``lib/cards.py`` free of a dependency on ``lib/spotify``.
    """
    path = Path(path)
    post = frontmatter.load(str(path))
    fm = dict(post.metadata or {})
    body_md = post.content or ""

    card_type = fm.get("type")
    name = fm.get("name")
    if not card_type or not name:
        missing = [k for k in ("type", "name") if not fm.get(k)]
        raise ValueError(
            f"Card at {path} missing required frontmatter key(s): "
            f"{', '.join(missing)}"
        )

    slug = _derive_slug(path.stem)

    # Wikilinks: frontmatter strings first, then body. De-dup preserves order.
    seen: set[tuple[str, str]] = set()
    merged: list[tuple[str, str]] = []
    for s in _walk_strings(fm):
        for pair in extract_wikilinks(s):
            if pair not in seen:
                seen.add(pair)
                merged.append(pair)
    for pair in extract_wikilinks(body_md):
        if pair not in seen:
            seen.add(pair)
            merged.append(pair)

    rewritten = _rewrite_wikilinks(body_md)
    body_html = md.markdown(rewritten, extensions=["extra", "sane_lists"])

    return {
        "type": str(card_type),
        "slug": slug,
        "name": str(name),
        "frontmatter": fm,
        "body_html": body_html,
        "body_md": body_md,
        "wikilinks": merged,
        # spotify_embed: intentionally omitted — Track E wires this in app.py.
    }
