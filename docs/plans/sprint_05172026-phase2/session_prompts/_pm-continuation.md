# PM Continuation — sprint_05172026-phase2 (kickoff state)

**Written:** 2026-05-17 (sprint kickoff)
**Sprint folder:** `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/`
**Main branch HEAD at kickoff:** (set by the kickoff commit you're about to make)
**Demo target:** 2026-06-07 (3 weeks)
**Task tracking:** None — `music-graphs` is not registered in task_lib. Tracked via this folder + `test_registry.md`.

---

## Current state

**Sprint launched.** Spec is locked. Pre-sprint fixups done (Tony Gilkyson rename). Nirvana MTV Unplugged Spotify URL retry failed via MCP — deferred into Track H. Track prompts A–I + test registry written. No sub-agent sessions have launched yet.

| Wave | Tracks | Status |
|---|---|---|
| Pre-sprint | Tony Gilkyson rename | ✅ done by PM, ready to commit with kickoff |
| Pre-sprint | Nirvana URL retry | ✅ attempted, MCP returned no match; documented in registry (H2) and folded into Track H |
| 1 | A `retrieve-spotify-song`, B `add-node` | ⬜ prompts written, ready to launch |
| 2 | C `add-edge`, D `expand-graph` | ⬜ prompts written, depend on Wave 1 |
| 3 | E family-agent, F band-x dogfood, G pittsburgh-jazz dogfood | ⬜ prompts written, depend on Wave 2 |
| 4 | H bowie-covers via expand-graph, I cover images | ⬜ prompts written, H depends on Wave 2, I independent |

---

## Launch model (locked from Phase 1)

- **PM pre-creates worktrees** with `git worktree add /private/tmp/mg-wt-<X> -b sprint/<track-name>` from `main` before launching each wave's sub-agent.
- **Sub-agents do NOT call `EnterWorktree`.** They use `git -C <path>` for every git operation.
- **Merge order** within a wave respects dependencies; cross-wave merges happen only after all prior-wave merges complete.
- **Verification per completion:** read HANDOFF block, read `/tmp/test_results_track-<X>.txt`, confirm `FAIL=0`, run `git -C <path> log --oneline -1`, confirm branch and commit.

---

## Next actions for the resuming PM (in order)

1. **Verify pre-sprint state.** `git log --oneline -3` should show the kickoff commit at HEAD. `git worktree list` should show only `main`. `git status` should be clean.
2. **Launch Wave 1.** Create worktrees:
   ```bash
   git worktree add /private/tmp/mg-wt-A -b sprint/retrieve-spotify-song
   git worktree add /private/tmp/mg-wt-B -b sprint/add-node
   ```
   Launch two parallel sub-agent sessions (one per track) using the prompts in `session_prompts/A-retrieve-spotify-song.md` and `B-add-node.md`. Background mode is fine; they're independent.
3. **Accept Wave 1.** For each track: read HANDOFF appended to the prompt file; check test_results file; merge to main with `git rebase main` from the worktree, then `git merge --ff-only sprint/<track>` from main. Sign off the relevant rows in `test_registry.md`.
4. **Launch Wave 2 (C, D).** Same pattern. D depends on A+B+C signatures; C depends only on B's lint pattern. Launch in series or parallel based on actual signature stability.
5. **Launch Wave 3 (E, F, G).** Parallel. Family agent + the two dogfood content tracks. Track F and G each need Alec available to approve skill-proposed candidates (e.g., the Exene/Doe albums in F, the per-artist albums in G). Plan launch timing accordingly.
6. **Launch Wave 4 (H, I).** H is the `expand-graph` test case — Alec also approves candidates here. I is independent and cheap.
7. **Pre-demo gate.** Before declaring demo-ready: all automated rows in `test_registry.md` signed off, all manual rows signed off (or explicitly deferred with documentation), `tools/lint_graphs.py` clean across all 3 graphs.

---

## Open items that may need Alec mid-sprint

- **Exene Cervenka and John Doe solo album choices** (Track F). Skill proposes top Wikipedia candidate; Alec approves.
- **Most pittsburgh-jazz per-artist albums** (Track G). Skill proposes; Alec approves. Three are pre-specified; the rest are skill-discovered.
- **`expand-graph` candidate approval** (Track H). Skill surfaces 5–10 candidates per pass; Alec approves a subset before any writes.
- **claude.ai/code surface verification** (Track E). The agent and skills need to be runnable on Clare/Jeremiah's surface. Alec should validate at least once during Track E to confirm parity.

---

## Files written this session (PM)

| File | Action |
|---|---|
| `docs/plans/sprint_05172026-phase2/project_spec.md` | Created, locked |
| `docs/plans/sprint_05172026-phase2/test_registry.md` | Created |
| `docs/plans/sprint_05172026-phase2/session_prompts/{A,B,C,D,E,F,G,H,I}-*.md` | Created |
| `docs/plans/sprint_05172026-phase2/session_prompts/_pm-continuation.md` | This file |
| `graphs/band-x/cards/person-troy-gilkyson.md` → `person-tony-gilkyson.md` | Renamed (Phase 1 fixup) |
| `graphs/band-x/cards/group-x.md` | Wikilink updated to `[[person:tony-gilkyson]]` |

---

## Key files for next session

| File | Role |
|---|---|
| `docs/plans/sprint_05172026-phase2/project_spec.md` | Spec (locked). Read first. |
| `docs/plans/sprint_05172026-phase2/test_registry.md` | Pass/fail gate. |
| `docs/plans/sprint_05172026-phase2/session_prompts/*.md` | One prompt per track; launch from these. |
| `docs/plans/sprint_05172026/_sprint-closeout.md` | Phase 1 lessons + locked architectural seams. |
| `tools/lint_graphs.py`, `lib/cards.py`, `lib/graph.py`, `lib/spotify.py` | APIs Phase 2 must preserve. |
