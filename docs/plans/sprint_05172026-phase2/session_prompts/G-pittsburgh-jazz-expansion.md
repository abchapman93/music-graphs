# Track G — pittsburgh-jazz expansion (dogfood)

**Sprint:** `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/`
**Branch:** `sprint/pittsburgh-jazz-expansion`
**Worktree path (PM pre-creates):** `/private/tmp/mg-wt-G`
**Wave:** 3 (parallel with E, F)
**Dependencies:** Tracks A, B, C merged to main.

## How to work on this branch

PM has pre-created the worktree off `main` after A–C merged. You do NOT call `EnterWorktree`. Use `git -C /private/tmp/mg-wt-G <git-op>`.

## Goal

Expand `graphs/pittsburgh-jazz/` so **every current person card has at least one album they appear on** (lead artist or sideman). Use the `retrieve-spotify-song`, `add-node`, and `add-edge` skills. Three specific albums (with provided URLs and required notes) are mandatory; the rest the skill proposes for Alec approval.

## Context files to read

- `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/project_spec.md` — section "C3. pittsburgh-jazz" (the table of mandatory albums + the personal notes Alec specified).
- `.claude/skills/{retrieve-spotify-song,add-node,add-edge}/SKILL.md`.
- All person cards under `graphs/pittsburgh-jazz/cards/person-*.md` — the universe of artists you must cover.
- Existing album cards in the graph: `graphs/pittsburgh-jazz/cards/album-moanin.md`, `album-sugar.md` — match style.

## Definition of done

### Three mandatory albums (with notes)

- [ ] **Gene Harris Trio Plus One**, Spotify `https://open.spotify.com/album/2AglF11Jys2hkEy44XBlBR`
  - Linked via wikilinks to `[[person:stanley-turrentine]]` AND `[[person:ray-brown]]`.
  - 3–5 sentence body summarizing the album and noting the Turrentine + Ray Brown personnel.
  - `symmetric=True` edges so both person cards gain a `[[album:<slug>]]` link.

- [ ] **Sean Jones album** (skill proposes title; Spotify URL is `https://open.spotify.com/album/3ucQJ8hwxcOFrFvdL3YN9j` — confirm title via MCP).
  - Linked to `[[person:sean-jones]]`.
  - **Required note on the Sean Jones *person* card** (not the album card): one sentence noting that Alec studied with him at Duquesne University in Pittsburgh. Use `add-edge` style appended sentence on the person card, or hand-edit only if the skill doesn't accommodate free-text notes (flag in HANDOFF if so).

- [ ] **Maureen Budway album** (skill proposes title; Spotify URL is `https://open.spotify.com/album/2PoDg7kkMyCOASqSIAReuV` — confirm title via MCP).
  - Linked to `[[person:maureen-budway]]`.
  - **Required notes on the Maureen Budway *person* card:** one or two sentences noting (a) Alec accompanied her voice lessons when she worked at Duquesne, (b) the album was recorded shortly before her death, which makes the Stephen Foster track "Hard Times Come Again No More" especially poignant in that context.
  - **Cross-artist edge.** Sean Jones plays on the track "Sweet Lover No More" from this album. Add a wikilink between Sean Jones's person card and this album, AND add a sentence on the Maureen Budway album card body noting Sean Jones's appearance on "Sweet Lover No More" (with a `[[person:sean-jones]]` wikilink).

### Coverage requirement

- [ ] For each remaining person card under `graphs/pittsburgh-jazz/cards/person-*.md` that does NOT yet have an album wikilink, the `expand-graph` skill (or manual use of `retrieve-spotify-song` + `add-node` + `add-edge`) proposes an album they appear on (lead or sideman). Alec approves; you write the approved ones. Document each proposal/approval in HANDOFF.

### Quality bars

- [ ] All Spotify URLs verified via MCP. No training-data guesses.
- [ ] `tools/lint_graphs.py pittsburgh-jazz` reports 0 errors.
- [ ] `app.py` serves `/graph/pittsburgh-jazz`; node count increased by at least the number of new albums; edges between each new album and its linked person(s) visible in the rendered graph.

## Workflow discipline (graded)

- [ ] Every card written via `add-node`.
- [ ] Every edge written via `add-edge` (use `symmetric=True` for person↔album).
- [ ] Skill friction (especially around adding biographical sentences to a person card) documented in HANDOFF.

## Not in scope

- Do NOT change Phase 1 person cards' biographical content beyond the explicit note additions for Sean Jones and Maureen Budway.
- Do NOT add albums for artists not already in the graph as person cards.
- Do NOT add tracks unless narratively required (e.g., "Sweet Lover No More" can be a *body sentence with wikilink*, not a separate track card).
- Do NOT modify the skills (any gaps → HANDOFF).

## Test protocol

```bash
cd /private/tmp/mg-wt-G
.venv/bin/python tools/lint_graphs.py pittsburgh-jazz 2>&1 | tee /tmp/test_results_track-g.txt
.venv/bin/python -m pytest 2>&1 | tee -a /tmp/test_results_track-g.txt
```
Confirm lint = 0 and pytest FAIL=0. Log path in HANDOFF.

## Handoff protocol

```
HANDOFF (Track G):
- Person cards in graph: <count>
- Albums added: <list of paths>
- Mandatory albums (Gene Harris, Sean Jones, Maureen Budway): <three lines, each with verified Spotify URL>
- Personal-note additions (Sean Jones, Maureen Budway person cards): <quoted sentences as added>
- Sean Jones ↔ Maureen Budway album cross-edge: <yes/no, file path>
- Skill friction notes (esp. adding free-text notes to existing person cards): <list>
- /tmp/test_results_track-g.txt: lint=0 errors, pytest FAIL=<count>
- Smoke check: /graph/pittsburgh-jazz renders with new albums + edges: <yes/no>
- Deviations: <none / list>
```

## Close-out

```
git -C /private/tmp/mg-wt-G add .
git -C /private/tmp/mg-wt-G commit -m "content(pittsburgh-jazz): album per artist + personal notes (dogfood)"
```
Report SHA + HANDOFF to PM.
