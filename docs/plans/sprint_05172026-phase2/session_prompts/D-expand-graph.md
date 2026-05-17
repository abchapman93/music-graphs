# Track D — `expand-graph` skill

**Sprint:** `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/`
**Branch:** `sprint/expand-graph`
**Worktree path (PM pre-creates):** `/private/tmp/mg-wt-D`
**Wave:** 2 (parallel with C)
**Dependencies:** Tracks A, B, C merged to main. This skill orchestrates them; it does not re-implement their behavior.

## How to work on this branch

PM has pre-created the worktree off `main` after A+B+C merged. You do NOT call `EnterWorktree`. Use `git -C /private/tmp/mg-wt-D <git-op>`.

## Goal

Create `.claude/skills/expand-graph/` — given a graph slug + an expansion criterion (e.g., "find more Bowie covers", "find an album for each person"), the skill searches (web search + Spotify MCP) for 5–10 candidate additions, presents them to the user for approval, and runs `add-node` + `add-edge` on accepted candidates.

This is the bowie-covers test case (Track H consumes it).

## Context files to read

- `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/project_spec.md` — section "C2. bowie-covers" (the explicit test case) and the locked candidate-ceiling rule (5–10).
- `.claude/skills/retrieve-spotify-song/SKILL.md`, `.claude/skills/add-node/SKILL.md`, `.claude/skills/add-edge/SKILL.md` — the three skills you orchestrate. Read them so you call them with correct inputs.
- An existing graph for context: `/Users/alecchapman/Code/music-graphs/graphs/bowie-covers/cards/note-bowie-songbook.md` (scope statement Phase 1 used).
- `/Users/alecchapman/Code/music-graphs/graphs/<any>/README.md` — graph-level scope hints the skill should respect.

## Definition of done

- [ ] `.claude/skills/expand-graph/SKILL.md` documents:
  - **Inputs:** graph slug, expansion criterion (free text), optional candidate ceiling (default 5, max 10).
  - **Workflow:** (1) read the graph's README + existing card names to understand scope; (2) generate candidates via web search and/or Spotify MCP; (3) for each candidate, verify it makes sense for the graph and find a Spotify URL via `retrieve-spotify-song`; (4) present a numbered candidate list with name, type, proposed wikilinks to existing nodes, and Spotify URL; (5) wait for user to approve a subset; (6) for each approved candidate, call `add-node` then `add-edge` for proposed wikilinks; (7) after all writes, run lint and report a summary.
- [ ] **Candidate-ceiling enforcement.** Never present more than 10 candidates in one pass; if more exist, surface the first batch and offer to continue after approval.
- [ ] **Scope-respect.** The skill reads the graph's README/scope cards and rejects candidates that obviously violate scope (e.g., proposing a non-Bowie-related cover for `bowie-covers`). State the inclusion criterion back to the user before searching.
- [ ] **No direct file writes.** Every node creation goes through `add-node`; every edge through `add-edge`. The skill's own code never writes a card file directly. This is a non-negotiable architectural rule from the spec.
- [ ] **Spotify policy.** Every candidate must have either a verified Spotify URL (via `retrieve-spotify-song`) OR explicit `spotify_url: null` with a documented reason ("MCP search exhausted").
- [ ] **Dry-run mode.** Skill supports `dry_run=True` for tests: surface candidates without invoking `add-node` / `add-edge`. Pytest at `tests/test_expand_graph.py` covers dry-run candidate generation against a mocked search.
- [ ] **Album-only default.** Per the locked spec, propose album cards by default. Track cards only when there's narrative reason (e.g., a cross-artist appearance worth surfacing).

## Not in scope

- Do NOT re-implement Spotify search, card writes, or wikilink writes. Orchestrate the three existing skills only.
- Do NOT touch `lib/cards.py`, `lib/graph.py`, `app.py`, or templates.
- Do NOT add UI for browsing existing graphs (the app already does that).

## Test protocol

```bash
cd /private/tmp/mg-wt-D
.venv/bin/pytest tests/test_expand_graph.py -v 2>&1 | tee /tmp/test_results_track-d.txt
```
Confirm FAIL=0. Log path in HANDOFF.

## Handoff protocol

```
HANDOFF (Track D):
- SKILL.md path: <absolute>
- Workflow stages: <list, matching DoD>
- Candidate ceiling enforced at: <line/function>
- Dry-run flag: <how to invoke>
- /tmp/test_results_track-d.txt: FAIL=<count>
- Integration gotchas for Track H (bowie-covers dogfood): <e.g., "skill needs WebFetch tool available; without it, candidate generation degrades to Spotify-only">
- Integration gotchas for Track E (family agent): <e.g., "agent should explain ceiling and approval flow to user up front">
- Deviations: <none / list>
```

## Close-out

```
git -C /private/tmp/mg-wt-D add .
git -C /private/tmp/mg-wt-D commit -m "feat(skills): expand-graph orchestrator with candidate review"
```
Report SHA + HANDOFF to PM.
