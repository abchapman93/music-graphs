# Track B — Card parser

**Sprint:** `~/Code/music-graphs/docs/plans/sprint_05172026/`
**Branch:** `sprint/card-parser` — **use `EnterWorktree` before writing any files.**
**Wave:** 1 (parallel with A, C)
**Dependencies:** P0 (repo-init) complete. Does NOT depend on Track A.

## Goal

Implement `lib/cards.py` with `parse_card(path) -> dict` and `extract_wikilinks(text) -> list[tuple[str, str]]` per the schema in the sprint spec. Pure-Python module, no Flask. Backed by unit tests.

## Context files to read

- `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026/project_spec.md` — sections "Card schema", "Module signatures", "Data contracts" (the "Parsed card" output shape is the contract you must match).
- `/Users/alecchapman/Code/Claude Setup/tools/wiki_lib.py` — close-analog implementation; reuse the wikilink regex and frontmatter-parse pattern (full file is large — focus on `parse_frontmatter`, wikilink regex `WIKILINK_RE`, and any body-rendering helper).

## Definition of done

- [ ] `lib/__init__.py` exists (empty).
- [ ] `lib/cards.py` exists exporting:
  - `extract_wikilinks(text: str) -> list[tuple[str, str]]` — returns `[(type, slug), ...]` from `[[type:slug]]` and `[[type:slug|Display]]` matches. De-duplicates while preserving first-seen order. Handles whitespace inside brackets gracefully.
  - `parse_card(path: pathlib.Path) -> dict` — returns the exact schema below.
- [ ] Returned dict from `parse_card` has these keys, all present (use empty/None where not applicable):
  ```python
  {
    "type": str,         # required from frontmatter
    "slug": str,         # derived from filename: stem after the first "-" (e.g., "person-stanley-turrentine.md" → "stanley-turrentine"); fall back to full stem if no hyphen
    "name": str,         # required from frontmatter
    "frontmatter": dict, # full parsed YAML
    "body_html": str,    # markdown rendered to HTML, with [[type:slug]] rewritten to <a href="#{type}:{slug}" data-wikilink="{type}:{slug}">{display}</a>
    "body_md": str,      # raw markdown body (post-frontmatter)
    "wikilinks": [(str, str)],  # de-duplicated list across BOTH frontmatter scalar/list values AND body text
    "spotify_embed": str | None,  # call lib.spotify.spotify_embed_url(frontmatter["spotify_url"]) if present, else None — but this track does NOT import lib.spotify; instead, leave spotify_embed as raw frontmatter["spotify_url"] or None, and add a TODO comment noting the wiring point. Track E will wire it.
  }
  ```
  → Actually: to keep dependencies clean, **omit `spotify_embed` from this track's output entirely**. Leave a comment in `parse_card` marking where Track E should insert it. The contract that ships to Wave 2 will be a tuple of `(parse_card_output, spotify_embed_url_for_card)` computed in `app.py` at request time, not in `lib/cards.py`.
- [ ] Wikilink rewriting in `body_html` uses HTML anchor `<a href="#{type}:{slug}" data-wikilink="{type}:{slug}" class="wikilink">{Display}</a>`. The display text is the part after `|` if present, else `{type}:{slug}`.
- [ ] **Wikilinks must also be extracted from frontmatter values.** Specifically: any string scalar matching the wikilink pattern, and any list of such strings (e.g., `birth_location`, `primary_link`, `secondary_links`). Use `extract_wikilinks` on every string value reachable in the frontmatter dict (recursive walk).
- [ ] Unit tests at `tests/test_cards.py` cover:
  - Wikilink extraction: `[[person:foo]]`, `[[person:foo|Foo Bar]]`, multiple in one line, duplicates de-duped, no-match returns empty list, weird-whitespace tolerated.
  - `parse_card` on a fixture card (created in `tests/fixtures/sample_card.md`) returns the expected schema with frontmatter, body_html containing rewritten anchors, and wikilinks merged across frontmatter and body.
  - `parse_card` correctly derives slug from filename with and without a `<type>-` prefix.
  - `parse_card` raises a clear error on missing `type` or `name` in frontmatter (use `ValueError` with the path in the message).
- [ ] All tests pass.

## Test protocol

```bash
cd ~/Code/music-graphs
pytest tests/test_cards.py -v 2>&1 | tee /tmp/test_results_<task_id>.txt
```
Confirm FAIL=0. Log the path in HANDOFF.

## Not in scope

- Do **not** import or implement `lib/spotify.py` or `lib/graph.py`. Leave a comment in `parse_card` where spotify embed wiring will go (Track E's job).
- Do **not** read any `graphs/<slug>/*` content. Tests use fixtures under `tests/fixtures/`.
- Do **not** touch `app.py` or templates.
- Do **not** add CLI / argparse entry points to `lib/cards.py`.

## Handoff protocol

Append HANDOFF note before declaring done:
```
HANDOFF:
- lib/cards.py exports: extract_wikilinks, parse_card.
- parse_card output schema: <one-line summary, e.g., "matches spec; omits spotify_embed key — Track E to wire">.
- Test fixtures: tests/fixtures/sample_card.md.
- Packages used: python-frontmatter, markdown, PyYAML (via frontmatter), <others>.
- Integration gotchas for Track D: <e.g., "wikilinks() returns frontmatter+body merged; consumers should NOT extract again">.
- /tmp/test_results_<task_id>.txt: <path>, FAIL=<count>.
- Deviations: <none / list>.
```

## Close-out

Commit on `sprint/card-parser` with subject `feat(lib): card markdown + wikilink parser`. Brief paragraph summary of the module shape and test coverage.

---

HANDOFF:
- lib/cards.py exports: extract_wikilinks, parse_card.
- parse_card output schema: matches spec; spotify_embed key omitted — Track E wires open.spotify.com → embed URL in app.py at request time using lib.spotify.spotify_embed_url(card["frontmatter"].get("spotify_url")).
- Test fixtures: tests/fixtures/person-stanley-turrentine.md (canonical sample with frontmatter + body wikilinks), tests/fixtures/sample_card.md (identical copy for spec-named reference), tests/fixtures/track-only.md (minimal card, no wikilinks), tests/fixtures/missing_type.md (error path).
- Packages used: python-frontmatter (which pulls in PyYAML), markdown, pytest (test-only).
- Integration gotchas for Track D: card["wikilinks"] is the merged, de-duplicated list of (type, slug) from BOTH frontmatter string scalars (recursive walk over dicts/lists) AND the body. Consumers (build_graph) should iterate card["wikilinks"] directly — do NOT re-run extract_wikilinks on body or frontmatter, or you'll double-count. Frontmatter wikilinks come first in first-seen order, then body links.
- Wikilink regex is permissive on type (any lowercase-ish identifier) since the music-graphs schema uses person|group|album|song|track|location|genre|note|memory. Whitespace inside [[...]] and around `:` / `|` is tolerated.
- body_html anchor shape: <a href="#{type}:{slug}" data-wikilink="{type}:{slug}" class="wikilink">{display}</a>. Display is the part after `|` if present, else "{type}:{slug}".
- Markdown extensions enabled: "extra", "sane_lists".
- /tmp/test_results_track-B.txt: /tmp/test_results_track-B.txt, FAIL=0 (14 passed).
- Deviations: none.
