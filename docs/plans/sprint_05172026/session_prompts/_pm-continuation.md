# Sprint Manager Handoff — 2026-05-17

**Written:** 2026-05-17 (end of session)
**Sprint folder:** `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026/`
**Main branch HEAD:** `d298183 init: music-graphs Phase 1 scaffolding`
**Task tracking:** None — `music-graphs` not registered in task_lib. Sprint is informal (gift project).

---

## Current state

Sprint is fully scoped and P0 is done. Repo exists on `main` with a clean working tree. Sprint spec is locked (open questions resolved). Session prompts are written for all 7 tracks. Wave 1 (A, B, C) is cleared to launch — the previous session was interrupted just as the 3 agent calls were being assembled. **Nothing has been implemented yet beyond the repo skeleton.**

| Phase | Track | Status | Notes |
|---|---|---|---|
| Pre-sprint | P0 repo-init | ✅ | Commit `d298183`. `.gitignore`, README stub, `docs/plans/` all in. |
| Pre-sprint | Spec + prompts | ✅ | `project_spec.md` locked. All 7 prompts written. `test_registry.md` ready. |
| Wave 1 | A skeleton-flask | ⏳ | Not started. Prompt ready. |
| Wave 1 | B card-parser | ⏳ | Not started. Prompt ready. |
| Wave 1 | C spotify-embed | ⏳ | Not started. Prompt ready. |
| Wave 2 | D graph-build | ❌ | Blocked on B. |
| Wave 3 | E graph-view | ❌ | Blocked on A + D + C. |
| Wave 4 | F card-authoring | ❌ | Blocked on E. |
| Wave 4 | G card-index | ❌ | Blocked on E. |

---

## What happened this session

1. Loaded Sprint Manager role from `~/.claude/skills/agent-roles/roles/sprint-manager.md`.
2. Surveyed `~/Code/music-graphs/` — found only `docs/plans/music-graphs-plan.md`. No code, no git history.
3. Read the full implementation plan and the sprint spec template.
4. Resolved all 3 open questions from the plan (image policy, CSV export, Note/Memory cards) — recorded as architecture decisions in the spec.
5. Created `docs/plans/sprint_05172026/` sprint folder.
6. Wrote `project_spec.md` — locked, open questions empty. Includes card schema, module signatures, data contracts, dependency graph, demo criteria.
7. Wrote 8 session prompts: P0, A, B, C, D, E, F, G. Each includes goal, context files, Definition of Done, test protocol, not-in-scope, handoff protocol, and close-out.
8. Wrote `test_registry.md` — 18 automated rows + 12 manual rows. Sprint Manager signs off automated; Alec signs off manual.
9. Verified P0 completion: repo on `main`, clean worktree, single commit `d298183`, no leftover worktrees. Pre-sprint gate confirmed green.
10. Wave 1 released. Was assembling 3 parallel agent calls (A, B, C) when session was interrupted.

---

## Immediate next steps (in order)

### Step 1 — Launch Wave 1 (A, B, C in parallel)

Launch all three as background agents simultaneously. Each prompt is self-contained.

| Track | Prompt file | Branch |
|---|---|---|
| A | `session_prompts/A-skeleton-flask.md` | `sprint/skeleton-flask` |
| B | `session_prompts/B-card-parser.md` | `sprint/card-parser` |
| C | `session_prompts/C-spotify-embed.md` | `sprint/spotify-embed` |

All three use `EnterWorktree` as first move. No prep needed.

### Step 2 — Verify each Wave 1 completion

For each finished track, before merging:
1. Check `/tmp/test_results_<task_id>.txt` — confirm FAIL=0.
2. Read HANDOFF note appended to the prompt file (or task notes).
3. `git worktree list` — confirm branch exists with at least 1 commit beyond `main`.
4. For Track A specifically: also verify the manual curl check reported `HTTP/1.1 200 OK`.

### Step 3 — Merge Wave 1 to `main` (in dependency order: B first, then A and C)

From each worktree branch:
```bash
git rebase main
```
Then from `main`:
```bash
git merge --ff-only sprint/<track-name>
git worktree remove <path>
```
B must be on `main` before launching D. A and C can merge in any order.

### Step 4 — Launch Wave 2 (D only)

Gate condition: `python -c "from lib.cards import parse_card"` succeeds from repo root.
Prompt: `session_prompts/D-graph-build.md`, branch `sprint/graph-build`.

### Step 5 — Verify D, merge, launch Wave 3 (E)

Gate for E: A, B, C, D all merged. Verify with:
```bash
python -c "from lib.cards import parse_card; from lib.graph import build_graph, list_graphs; from lib.spotify import spotify_embed_url; print('ok')"
```
Prompt: `session_prompts/E-graph-view.md`, branch `sprint/graph-view`.
E is the integration track — most likely to surface cross-track issues. Budget extra review time.

### Step 6 — Verify E, merge, launch Wave 4 (F + G in parallel)

Gate for F/G: `python app.py` runs and `/graph/pittsburgh-jazz-fixture` loads end-to-end. Verify via integration curls documented in E's HANDOFF.

### Step 7 — Demo-readiness gate

After F + G are merged:
- Fill in all 18 automated rows in `test_registry.md`.
- Alec fills in all 12 manual rows.
- Tag `v0.1-phase1-demo` on `main` only when both columns are fully green.

---

## Key decisions (do not re-litigate)

- **Image policy:** Hotlink Wikipedia URLs in `image:` frontmatter. Download key images (graph covers) to `graphs/<slug>/images/` and commit. This is locked — no discussion needed.
- **CSV export:** Deferred (not in Phase 1 scope).
- **Note/Memory cards:** Read-only only. No in-browser creation (Phase 2).
- **Port 8766:** Fixed. Dashboard is 8765. Both must coexist.
- **No task_lib tracking:** `music-graphs` is not registered in `projects/index.json`. Sprint is tracked in `test_registry.md` + HANDOFF notes only. Register if standup/dashboard visibility is wanted — not required.
- **Model:** Sonnet 4.6 for all tracks. Upgrade Track E to Opus 4.7 only if the integration gets stuck.
- **`spotify_embed` key:** Omitted from `lib/cards.py` output. Wired in `app.py` at request time using `spotify_embed_url(frontmatter.get("spotify_url"))`. Track E is responsible.

---

## Files written this session

| File | Action |
|---|---|
| `docs/plans/sprint_05172026/project_spec.md` | Created |
| `docs/plans/sprint_05172026/test_registry.md` | Created |
| `docs/plans/sprint_05172026/session_prompts/P0-repo-init.md` | Created (+ HANDOFF appended by P0 session) |
| `docs/plans/sprint_05172026/session_prompts/A-skeleton-flask.md` | Created |
| `docs/plans/sprint_05172026/session_prompts/B-card-parser.md` | Created |
| `docs/plans/sprint_05172026/session_prompts/C-spotify-embed.md` | Created |
| `docs/plans/sprint_05172026/session_prompts/D-graph-build.md` | Created |
| `docs/plans/sprint_05172026/session_prompts/E-graph-view.md` | Created |
| `docs/plans/sprint_05172026/session_prompts/F-card-authoring.md` | Created |
| `docs/plans/sprint_05172026/session_prompts/G-card-index.md` | Created |
| `docs/plans/sprint_05172026/session_prompts/_pm-continuation.md` | Created (this file) |

---

## Key files

| File | Role |
|---|---|
| `docs/plans/sprint_05172026/project_spec.md` | Locked spec — architecture decisions, data contracts, module signatures. Read before any session. |
| `docs/plans/sprint_05172026/test_registry.md` | Sprint acceptance gate. Fill in as tracks complete. |
| `docs/plans/sprint_05172026/session_prompts/A-skeleton-flask.md` | Wave 1 — Flask skeleton |
| `docs/plans/sprint_05172026/session_prompts/B-card-parser.md` | Wave 1 — card parser |
| `docs/plans/sprint_05172026/session_prompts/C-spotify-embed.md` | Wave 1 — Spotify embed |
| `docs/plans/sprint_05172026/session_prompts/D-graph-build.md` | Wave 2 — graph builder |
| `docs/plans/sprint_05172026/session_prompts/E-graph-view.md` | Wave 3 — integration |
| `docs/plans/sprint_05172026/session_prompts/F-card-authoring.md` | Wave 4 — 3 graphs of cards |
| `docs/plans/sprint_05172026/session_prompts/G-card-index.md` | Wave 4 — /cards index |
| `docs/plans/music-graphs-plan.md` | Source of truth for people/albums/places per graph (Track F needs this) |
