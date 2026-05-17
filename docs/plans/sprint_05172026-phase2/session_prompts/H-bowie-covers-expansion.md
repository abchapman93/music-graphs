# Track H — bowie-covers expansion via `expand-graph` (dogfood)

**Sprint:** `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/`
**Branch:** `sprint/bowie-covers-expansion`
**Worktree path (PM pre-creates):** `/private/tmp/mg-wt-H`
**Wave:** 4
**Dependencies:** Tracks A, B, C, D (especially D) merged to main. This is the explicit test case for `expand-graph`.

## How to work on this branch

PM has pre-created the worktree off `main` after Wave 3 merged. You do NOT call `EnterWorktree`. Use `git -C /private/tmp/mg-wt-H <git-op>`.

## Goal

Use the `expand-graph` skill to add new entries to `graphs/bowie-covers/`. Goal: a few more notable hits — covers of Bowie songs, or Bowie covers of others' songs (match the scope already established in the graph's existing cards/README). Plus: resolve or document the missing Nirvana MTV Unplugged Spotify URL.

This track is the acceptance test for Track D's `expand-graph` skill. If the skill's UX is bad, that's the news.

## Context files to read

- `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/project_spec.md` — section "C2. bowie-covers".
- `.claude/skills/expand-graph/SKILL.md` — primary tool.
- `/Users/alecchapman/Code/music-graphs/graphs/bowie-covers/cards/note-bowie-songbook.md` and `README.md` (if present) — scope statement.
- All existing cards under `graphs/bowie-covers/cards/` — to avoid duplicates.
- `/Users/alecchapman/Code/music-graphs/graphs/bowie-covers/cards/album-unplugged-in-new-york.md` — has missing Spotify URL; the goal here is to try once more via combined web search + MCP.

## Definition of done

- [ ] Ran `expand-graph` against `bowie-covers` with a clear inclusion criterion (state it in HANDOFF).
- [ ] At least **5 new approved cards** committed (album cards by default; tracks only when narratively justified).
- [ ] Every approved candidate has a verified Spotify URL from `retrieve-spotify-song`, OR `spotify_url: null` with a one-line comment explaining why (e.g., `# Spotify MCP search exhausted 2026-MM-DD`).
- [ ] Every candidate that the skill surfaced but Alec rejected is listed in HANDOFF (with the reason, briefly). This is the audit trail for the test case.
- [ ] **Nirvana MTV Unplugged retry.** Attempt the Spotify URL lookup using both `retrieve-spotify-song` and a broader search (e.g., search for the track "About a Girl - Unplugged" by Nirvana; some tracks index the album it's on). If found, update `album-unplugged-in-new-york.md` frontmatter with the verified URL. If still not found, write a one-line comment in the frontmatter documenting the exhaustion and date.
- [ ] `tools/lint_graphs.py bowie-covers` reports 0 errors.
- [ ] All new cards link (via `add-edge`) to at least one existing card (the artist or the song being covered) — no orphans.
- [ ] `app.py` serves `/graph/bowie-covers` with the new nodes + edges rendered.

## Workflow discipline (graded)

- [ ] Every node was created via `add-node` (called through `expand-graph`).
- [ ] Every edge was created via `add-edge` (called through `expand-graph`).
- [ ] No hand-edits to card files except for the documented `spotify_url: null` comment on `album-unplugged-in-new-york.md` if the URL can't be resolved.
- [ ] **Document `expand-graph` UX in HANDOFF.** Was the candidate list sensible? Did it respect scope? Did the 5–10 ceiling feel right? Anything Alec had to clarify mid-run? This is the test case's payload.

## Not in scope

- Do NOT modify the `expand-graph` skill itself. UX issues are HANDOFF items.
- Do NOT add covers that fall outside the graph's existing scope.
- Do NOT touch the other two graphs.

## Test protocol

```bash
cd /private/tmp/mg-wt-H
.venv/bin/python tools/lint_graphs.py bowie-covers 2>&1 | tee /tmp/test_results_track-h.txt
.venv/bin/python -m pytest 2>&1 | tee -a /tmp/test_results_track-h.txt
```
Confirm lint=0, FAIL=0. Log path in HANDOFF.

## Handoff protocol

```
HANDOFF (Track H):
- Inclusion criterion (verbatim, as given to expand-graph): "<criterion>"
- Candidates surfaced: <list, with approve/reject per candidate>
- Cards added (paths + slugs): <list>
- Spotify URLs verified: <list>
- Nirvana MTV Unplugged outcome: <URL found OR "MCP search exhausted, frontmatter comment added">
- expand-graph UX notes (the real payload): <bulleted observations — what worked, what felt clunky, where Alec had to override>
- /tmp/test_results_track-h.txt: lint=0 errors, pytest FAIL=<count>
- Smoke check: /graph/bowie-covers renders with new nodes + edges: <yes/no>
- Deviations: <none / list>
```

## Close-out

```
git -C /private/tmp/mg-wt-H add .
git -C /private/tmp/mg-wt-H commit -m "content(bowie-covers): expansion via expand-graph + Nirvana URL retry"
```
Report SHA + HANDOFF to PM.
