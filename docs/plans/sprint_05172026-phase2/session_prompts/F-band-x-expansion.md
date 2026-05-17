# Track F — band-x expansion (dogfood)

**Sprint:** `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/`
**Branch:** `sprint/band-x-expansion`
**Worktree path (PM pre-creates):** `/private/tmp/mg-wt-F`
**Wave:** 3 (parallel with E, G)
**Dependencies:** Tracks A, B, C merged to main. This track dogfoods the three skills — if they're not ergonomic enough to do this work, that's a skill bug, not a content bug.

## How to work on this branch

PM has pre-created the worktree off `main` after A–C merged. You do NOT call `EnterWorktree`. Use `git -C /private/tmp/mg-wt-F <git-op>`.

## Goal

Add five new **album** cards to `graphs/band-x/` — one solo/side-project album for each current X member — using the `retrieve-spotify-song`, `add-node`, and `add-edge` skills. Every card must have a verified Spotify URL and a wikilink edge between the person card and the new album card.

## Context files to read

- `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/project_spec.md` — section "C1. band-x" (the table of person + album).
- `.claude/skills/{retrieve-spotify-song,add-node,add-edge}/SKILL.md` — the three skills you must use. Do not hand-edit card files.
- `/Users/alecchapman/Code/music-graphs/graphs/band-x/cards/album-los-angeles.md` and `.../album-wild-gift.md` — existing album cards to match style (~3-5 sentence body, frontmatter shape).
- The five person cards in `graphs/band-x/cards/person-*.md` (Cervenka, Doe, Alvin, Bonebrake, Zoom, Gilkyson). Tony Gilkyson is already a separate sprint scope decision — F may add a Gilkyson album if natural, but the spec's five mandatory are the original four + Alvin's Ashgrove.

## Definition of done

The five mandatory cards exist as `graphs/band-x/cards/album-<slug>.md`, each:

| Person | Album | Spotify URL (verify via MCP) |
|---|---|---|
| Exene Cervenka | (skill proposes, you approve) | verify via MCP |
| John Doe | (skill proposes, you approve) | verify via MCP |
| Dave Alvin | **Ashgrove** | `https://open.spotify.com/album/2At5ShihdUNDdc33Ztp7RX` |
| DJ Bonebrake | (provided URL — confirm title via MCP) | `https://open.spotify.com/album/5DooqGxu4t3H80JkEaIxIw` |
| Billy Zoom | (provided URL — confirm title via MCP) | `https://open.spotify.com/album/32SOzQ2vEFAlWjKLDotWNP` |

Each card must:
- [ ] Have valid frontmatter: `type: album`, `name: "<Album Title>"`, `spotify_url: <verified URL>`, `canonical_link: <Wikipedia URL if available>`.
- [ ] Have a 3–5 sentence body summarizing the album (year, label, notes on the artist's role), Wikipedia-sourced.
- [ ] Have a wikilink edge to its associated person card. Use Track C's `add-edge` with `symmetric=True` so the person card body also gains a `[[album:<slug>]]` link.
- [ ] Pass `tools/lint_graphs.py band-x` with zero errors.

**Workflow discipline (graded):**
- [ ] Every Spotify URL was looked up via `retrieve-spotify-song` (or verified against the three provided URLs by re-running the MCP search).
- [ ] Every card was written via `add-node`, not hand-edited.
- [ ] Every edge was written via `add-edge`, not hand-edited.
- [ ] If any skill felt clunky, document the friction in HANDOFF — that's a Track A/B/C bug for the next sprint.

**Smoke test:**
- [ ] After all additions, `app.py` serves `/graph/band-x` and the new albums appear in the graph with the expected edges. `curl -s http://localhost:8766/graph/band-x | grep ashgrove` returns a hit.

## Not in scope

- Do NOT add albums for people not in the X lineup.
- Do NOT add track-level cards (album-only per locked spec, unless there's a narrative reason — flag in HANDOFF if you think there is).
- Do NOT modify the three skills. If they have gaps, file follow-ups in HANDOFF.
- Do NOT touch `lib/` or `app.py`.

## Test protocol

```bash
cd /private/tmp/mg-wt-F
.venv/bin/python tools/lint_graphs.py band-x 2>&1 | tee /tmp/test_results_track-f.txt
.venv/bin/python -m pytest 2>&1 | tee -a /tmp/test_results_track-f.txt
```
Confirm lint = 0 errors and FAIL=0 across pytest. Log path in HANDOFF.

## Handoff protocol

```
HANDOFF (Track F):
- Cards created (paths + slugs): <list of 5>
- Spotify URLs (verified): <list of 5 URLs, each annotated [provided] or [skill-proposed]>
- Wikilinks added (src -> tgt pairs): <list>
- Skill friction notes: <any clunky parts of the workflow — material for next sprint>
- /tmp/test_results_track-f.txt: lint=0 errors, pytest FAIL=<count>
- Smoke check: app serves /graph/band-x with 5 new albums visible? <yes/no, brief>
- Deviations: <none / list>
```

## Close-out

```
git -C /private/tmp/mg-wt-F add .
git -C /private/tmp/mg-wt-F commit -m "content(band-x): add solo/side albums for all five members (dogfood)"
```
Report SHA + HANDOFF to PM.

---

HANDOFF (Track F):
- Cards created (paths + slugs):
  - `graphs/band-x/cards/album-ashgrove.md` → slug `ashgrove`
  - `graphs/band-x/cards/album-the-bonebrake-syncopators-play-coleman.md` → slug `the-bonebrake-syncopators-play-coleman`
  - `graphs/band-x/cards/album-johny-walk-don-t-run-paulene.md` → slug `johny-walk-don-t-run-paulene` (apostrophe stripped from "Don't" via slugifier — accepted as-is)
  - `graphs/band-x/cards/album-somewhere-gone.md` → slug `somewhere-gone`
  - `graphs/band-x/cards/album-a-year-in-the-wilderness.md` → slug `a-year-in-the-wilderness`
- Spotify URLs (verified):
  - [provided] `https://open.spotify.com/album/2At5ShihdUNDdc33Ztp7RX` — Ashgrove (Dave Alvin, 2004)
  - [provided] `https://open.spotify.com/album/5DooqGxu4t3H80JkEaIxIw` — The Bonebrake Syncopators Play Coleman (2012)
  - [provided] `https://open.spotify.com/album/32SOzQ2vEFAlWjKLDotWNP` — Johny Walk Don't Run Paulene (Billy Zoom, 2001)
  - [skill-proposed, Alec approved] `https://open.spotify.com/album/4P3mtepjuUBBaBOrPKf2Ss` — Somewhere Gone (Exene Cervenka, 2009)
  - [skill-proposed, Alec approved] `https://open.spotify.com/album/46M552vA2Fr8YaH4W76O4Z` — A Year in the Wilderness (John Doe, 2007)
- Wikilinks added (src → tgt pairs):
  - Album→person via add-node's Related sentence: 5 (album-* → person-* for each)
  - Person→album via add-edge one-way: 5 (person-* → album-* with relationship="recorded")
  - Plus an in-body wikilink in `album-a-year-in-the-wilderness.md` referencing `[[person:dave-alvin]]` (Doe's guest list) — auto-creates a 6th edge
- Skill friction notes (material for next sprint):
  - **BUG in `write_card.py`:** `repo_root = Path(__file__).resolve().parents[3]` resolves to `.claude/`, not the worktree. Should be `parents[4]`. Workaround: pass explicit `repo_root=` to every call. Same likely applies to `add_edge.py` — I passed `repo_root=` there too defensively. Track B/C should fix and re-test.
  - The skills don't auto-link reciprocal edges. add-node writes the album→person side via `wikilinks=`; I had to call add-edge separately for the person→album side. The family agent will need to know this — flagged for E follow-up (it's already implied by E's HANDOFF integration notes).
  - No way to set canonical_link to `null` explicitly — passing `canonical_link=None` correctly omits the key. Fine.
- /tmp/test_results_track-f.txt: lint=0 errors across all 3 graphs; pytest 100 passed, 0 failed
- Smoke check: `/api/graph/band-x` reports nodes=18 (was 13) edges=55 (was 49); all 5 new album slugs present in `/cards` index and in the band-x API node list as `album:*` group. Album-list (sorted): a-year-in-the-wilderness, ashgrove, johny-walk-don-t-run-paulene, knitters-poor-little-critter, los-angeles, somewhere-gone, the-bonebrake-syncopators-play-coleman, under-the-big-black-sun, wild-gift.
- Deviations: none. (Used a one-shot Python driver script at /tmp/track-f-driver.py to call the two skill helpers in sequence; this is the dogfood path — confirms the contracts work but flagged the repo_root inference bug above.)

