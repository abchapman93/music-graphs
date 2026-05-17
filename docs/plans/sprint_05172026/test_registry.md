# Test Registry — sprint_05172026 (music-graphs Phase 1)

Demo-ready when **both columns are fully green**. The Sprint Manager signs off on automated; Alec signs off on manual.

## Automated checks (Sprint Manager signs off — FAIL=0 verified from `/tmp/test_results_<task_id>.txt`)

| Track | Check | File | Status |
|---|---|---|---|
| A | Smoke: `app` importable, `GET /` returns 200 | `tests/test_app.py` | ✅ 3 passed (commit `ee74a7d`) |
| B | `extract_wikilinks` covers brackets, pipes, dedup, whitespace, empty | `tests/test_cards.py` | ✅ part of 14 passed (commit `8909b2b`) |
| B | `parse_card` returns spec schema + slug derivation + body wikilink rewrite | `tests/test_cards.py` | ✅ part of 14 passed |
| B | `parse_card` raises on missing `type` / `name` | `tests/test_cards.py` | ✅ part of 14 passed |
| C | `spotify_embed_url` track/album/playlist/artist/episode/show happy path | `tests/test_spotify.py` | ✅ 17 passed (commit `e1ac97c`) |
| C | `spotify_embed_url` strips query strings, normalizes http→https, no trailing slash | `tests/test_spotify.py` | ✅ part of 17 passed |
| C | `spotify_embed_url` returns None on None/empty/malformed/unknown-kind | `tests/test_spotify.py` | ✅ part of 17 passed |
| D | `build_graph` on fixture: 4 nodes, 2 edges (dedup verified) | `tests/test_graph.py` | ✅ 7 passed (commit `0a189ec`) |
| D | `build_graph` drops dangling wikilinks (no edge to nonexistent card) | `tests/test_graph.py` | ✅ part of 7 passed |
| D | `build_graph` drops self-loops | `tests/test_graph.py` | ✅ part of 7 passed |
| D | `list_graphs` returns expected metadata | `tests/test_graph.py` | ✅ part of 7 passed |
| E | Routes return 200: `/`, `/graph/<fixture>`, `/api/graph/<fixture>`, `/api/card/<fixture>/<slug>` | `tests/test_routes.py` | ✅ part of 50 passed (commit `353eb69`) |
| E | 404s: `/api/graph/missing`, `/api/card/<fixture>/missing` | `tests/test_routes.py` | ✅ part of 50 passed |
| E | Integration curls (graph API + card API + page HTML) succeed on running server | PM smoke 2026-05-17 | ✅ all 200; pittsburgh-jazz 16n/37e, band-x 13n/49e, bowie-covers 13n/28e; spotify embed wired |
| F | `tools/lint_graphs.py` reports 0 errors across all 3 real graph folders | `tools/lint_graphs.py` | ✅ "Total errors: 0" (PM run 2026-05-17) |
| F | Full `pytest tests/` green after all 3 graphs in place (no regression) | `tests/` | ✅ 50 passed (commit `afc751b`) |
| G | `GET /cards` returns 200, contains 9 type-filter options + ≥1 card name | `tests/test_routes.py` | ✅ part of 51 passed (commit `3a2f454`) |
| All | Full `pytest tests/` green after Wave 4 merges | `tests/` | ✅ **51 passed, 0 failed** on main HEAD `afc751b` |

## Manual interaction checks (Alec signs off — exercise in browser)

Numbered to match the **Demo criteria** in `project_spec.md`. Don't skip — automated tests caught zero UI bugs in past sprints when these were skipped.

| # | Check | Status |
|---|---|---|
| M1 | `python app.py` starts on 8766 with no tracebacks; home page lists 3 graphs with covers + descriptions | ⬜ |
| M2 | `/graph/pittsburgh-jazz` renders; all cards visible as nodes; Stanley Turrentine ↔ Pittsburgh edge present; ≥1 album↔artist edge present | ⬜ |
| M3 | Click a Person node → right panel shows name, image, bio, frontmatter dl | ⬜ |
| M4 | Click an Album node with `spotify_url` → Spotify embed renders AND pressing play actually plays audio | ⬜ |
| M5 | Click a `[[wikilink]]` inside a card body → graph focuses/zooms to target node and panel loads the target card | ⬜ |
| M6 | `/graph/band-x` works identically; "X at Red Butte" Memory card is present and reachable | ⬜ |
| M7 | `/graph/bowie-covers` works identically; at least one Bowie original + cover pair both have working Spotify embeds | ⬜ |
| M8 | `/cards` lists all ~45 cards; type filter narrows; text search narrows; combined filter works | ⬜ |
| M9 | Browser devtools console has zero errors during M1–M8 | ⬜ |
| M10 | Flask logs have zero tracebacks during M1–M8 | ⬜ |
| M11 | Server-rendered deep link `/graph/<slug>/card/<card_slug>` works without JS (right-click "Open in incognito + JS disabled" check) | ⬜ |
| M12 | Cover images load (no broken-image icons) on home page | ⬜ |

## Demo-readiness rule

If any row in either column is ⬜ at demo time, the Sprint Manager flags explicitly:
> **Demo-ready: NO — <N> automated + <M> manual checks outstanding.**

Do NOT let Alec walk into the demo thinking the app is ready when it isn't.

## Tag / version

Once both columns are fully green: tag `v0.1-phase1-demo` on `main`.
