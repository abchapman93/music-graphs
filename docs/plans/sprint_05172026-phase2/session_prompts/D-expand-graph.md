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

---

HANDOFF (Track D):
- SKILL.md path: `/private/tmp/mg-wt-D/.claude/skills/expand-graph/SKILL.md`
- Workflow stages: (1) read graph README + existing cards + `note-*.md` scope cards; (2) state inclusion criterion back to user; (3) generate candidates via injected search_fn (web + Spotify MCP); (4) verify Spotify URL per candidate via `retrieve-spotify-song` (or carry `spotify_url=None` with documented `spotify_reason`); (5) propose 1–3 wikilinks per candidate to existing slugs; (6) present numbered list (≤ ceiling); (7) wait for user approval; (8) for each approved → `add-node` then reciprocal `add-edge` on existing-target wikilinks; (9) run lint and report summary.
- Candidate ceiling enforced at: `expand_graph.py:_clamp_ceiling()` (range `[1, 10]`) called from `generate_candidates()`; list truncated before return; `overflow` count surfaced for the "more" follow-up.
- Dry-run flag: `run_expand_graph(..., dry_run=True)` — returns `ExpansionResult` with candidates populated, `created_paths=[]`, `edge_paths=[]`, `lint_returncode=None`; injected `add_node_fn` / `add_edge_fn` are not called. Test `test_dry_run_returns_candidates_without_writes` enforces this with sentinel callables that raise if invoked.
- /tmp/test_results_track-d.txt: FAIL=0 (14 passed; full suite 90 passed)
- Integration gotchas for Track H (bowie-covers dogfood):
  - The helper does NOT do live web/MCP search. Track H's session must pass `search_fn=` that wraps `WebSearch` + `mcp__68e7e171-8619-450d-bfc7-458af6964130__search`. The default search raises `NotImplementedError` on purpose so accidental "invented candidate" runs fail loud.
  - `Candidate(spotify_url=None)` requires an explicit `spotify_reason` (e.g. `"MCP search exhausted"`) — Track H's search wrapper must set this when the MCP comes up empty rather than dropping the candidate silently.
  - `add-edge` integration is best-effort: helper auto-imports `.claude/skills/add-edge/scripts/add_edge.py` if present; if Track C's helper module name or signature drifts from `add_edge(graph, src_slug, tgt_slug, ...)`, Track H may need to inject `add_edge_fn=` explicitly. The orchestrator builds reciprocal edges only — wikilinks on the new card itself are written by `add-node` from the `wikilinks=` argument at create time.
  - Reciprocal `add-edge` failures are recorded in `result.skipped` but do not stop the run — Track H should surface them.
- Integration gotchas for Track E (family agent):
  - The agent should explain the 5–10 ceiling and the approval flow to the user up front ("I'll show you up to N suggestions, you pick which to add"). Default ceiling=5.
  - The agent must pass `auto_pick=true` semantics down to `retrieve-spotify-song` per-candidate, but must still expect the song-skill to prompt when the MCP returns >1 result — that's a blocking step inside the candidate loop, not a background call.
  - `dry_run=True` is a useful preview-only mode the agent can offer Clare/Jeremiah ("want to see suggestions without writing anything?") before committing.
  - Album-only default is enforced by the helper's `Candidate.type` default (`"album"`); the agent should only propose `type="track"` when there's an explicit narrative reason and call it out in the user-facing approval list.
- Deviations: none. Track C's `add-edge` helper is not in this worktree (parallel track), so live `add-edge` wiring is exercised only via `add_edge_fn` injection in tests; real-call wiring auto-imports `add_edge.py` at runtime once Track C merges.
