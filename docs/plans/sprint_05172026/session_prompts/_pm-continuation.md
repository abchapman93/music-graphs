# Sprint Manager Handoff — 2026-05-17 (close)

**Written:** 2026-05-17 (end of session)
**Sprint folder:** `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026/`
**Main branch HEAD:** `92a4955 pm: close sprint_05172026 — Phase 1 demo-ready`
**Tag:** `v0.1-phase1-demo` (applied this session)
**Task tracking:** None — `music-graphs` is not registered in task_lib. Sprint tracked via `test_registry.md` + `_sprint-closeout.md`.

---

## Current state

**Sprint sprint_05172026 is CLOSED.** Phase 1 shipped: 3 working graphs (pittsburgh-jazz 16n/37e, band-x 13n/49e, bowie-covers 13n/28e = 42 cards total), Flask app on port 8766, `/cards` index, vis-network graph view, Spotify embeds wired at request time and verified against the real Spotify catalog. 51 pytest pass, lint_graphs reports 0 errors.

| Phase | Track | Status | Notes |
|---|---|---|---|
| Pre-sprint | P0 repo-init | ✅ | `d298183` |
| Wave 1 | B card-parser | ✅ | `8909b2b` — 14 tests |
| Wave 1 | A skeleton-flask | ✅ | `ee74a7d` — 3 tests + curl |
| Wave 1 | C spotify-embed | ✅ | `e1ac97c` — 17 tests |
| Wave 2 | D graph-build | ✅ | `0a189ec` — 7 tests |
| Wave 3 | E graph-view | ✅ | `353eb69` — 50 tests + e2e curl |
| Wave 4 | G card-index | ✅ | `3a2f454` — 51 tests |
| Wave 4 | F card-authoring | ✅ | `afc751b` — 3 graphs, lint clean |
| Post | Spotify URL repair | ✅ | `77c5836` + `84f8844` — 27/28 verified via Spotify MCP |
| Close | PM closeout + tag | ✅ | `92a4955`, tag `v0.1-phase1-demo` |

**Demo gate:** automated 18/18, manual 11/12 (M12 cover-images deferred). Demo-ready.

---

## What happened this session

1. Resumed as sprint manager from prior session's continuation prompt — found pre-sprint setup and P0 complete, Wave 1 launch interrupted with dangling worktrees.
2. **Recovered from a failed first launch:** the 3 pre-created worktrees from the prior session contained uncommitted half-done work; sub-agents had not used `EnterWorktree` properly. Stopped surviving background agents, cleaned the main branch, removed the worktrees.
3. **Switched to a safer launch model:** PM pre-creates worktrees with `git worktree add` at explicit `/private/tmp/mg-wt-*` paths; sub-agent prompts forbid `EnterWorktree`, require absolute paths and `git -C <path>` for every git op. This worked cleanly for all 7 remaining track launches.
4. Launched Wave 1 (A, B, C) in parallel as background agents. All 3 completed with HANDOFF blocks appended to their prompt files. Verified, rebased C onto B+A, merged in order B → A → C.
5. Launched Wave 2 (D). Completed, verified, merged.
6. Launched Wave 3 (E — integration track). Wired routes to `lib.cards` + `lib.graph` + `lib.spotify`, built the vis-network frontend, added the `pittsburgh-jazz-fixture` graph. End-to-end curl verified. Merged.
7. Launched Wave 4 (F + G) in parallel. F deleted the fixture and authored 3 real graphs (42 cards) + built `tools/lint_graphs.py`; G implemented `/cards` flat index with client-side filter and search. Merged G first, rebased F, merged F.
8. Ran PM smoke check: all routes 200, all 3 graph APIs return correct node/edge counts, Spotify embed wired correctly.
9. Signed off all 18 automated test_registry rows.
10. **Discovered Spotify URLs were wrong** — Alec reported the Blackstar card playing In Rainbows. Track F had drawn IDs from training data without web access. Launched a Spotify MCP lookup agent. First pass updated 18 cards in pittsburgh-jazz + bowie-covers and removed 1 unfindable, but missed band-x entirely. Second agent finished the remaining 7 band-x cards. 27/28 verified.
11. Alec signed off manual rows M1–M11; M12 (cover images on home page) deferred to Phase 2.
12. Wrote `_sprint-closeout.md` capturing Phase 2 wishlist and lessons learned. Committed and tagged `v0.1-phase1-demo`.

---

## Deferred to Phase 2 (next sprint scope)

From `_sprint-closeout.md`:

### Fixups from this sprint
1. **Cover images on home page (M12).** All 3 graph READMEs have `cover_image: null`. Per spec: hotlink Wikipedia URLs in frontmatter, download key images to `graphs/<slug>/images/`.
2. **Troy/Tony Gilkyson naming.** `graphs/band-x/cards/person-troy-gilkyson.md` filename says "troy-gilkyson" but `name: "Tony Gilkyson"`. Tony is correct (real X guitarist 1986–1995). Rename file to `person-tony-gilkyson.md` and update any wikilinks pointing to it.
3. **One missing Spotify URL.** `graphs/bowie-covers/cards/album-unplugged-in-new-york.md` (Nirvana MTV Unplugged) — manual lookup needed; the Spotify MCP couldn't surface it.

### New scope
4. **Reusable skills.** `add-node`, `retrieve-spotify-song`, likely `add-edge`/`add-wikilink`. Lets Alec (and family) build graphs without hand-editing YAML.
5. **Specialized Claude agent for non-technical collaborators.** Audience: Alec's family via Claude Code. Hide the markdown/frontmatter mechanics behind conversational UX; agent should suggest wikilinks to existing nodes, find Spotify links, scaffold card files.
6. **Expand album/song selection.** Alec to provide specific success criteria at Phase 2 kickoff — likely more graphs or denser coverage.

---

## Key decisions (do not re-litigate)

- **Sub-agents do NOT call `EnterWorktree`.** PM pre-creates worktrees with `git worktree add` and gives the sub-agent an explicit `/private/tmp/mg-wt-<X>` path with `git -C <path>` discipline. This is the launch model for any future parallel track sprint.
- **Spotify URLs must be verified via MCP at authoring time.** Training-data IDs are useless — some are invalid, some point to random other entities. The Spotify MCP (`mcp__68e7e171-8619-450d-bfc7-458af6964130__search`) works and should be the canonical lookup in Phase 2 skills.
- **`app.py` attaches `spotify_embed_url` at request time** — `lib/cards.py` stays free of a `lib/spotify` dependency. Preserve this seam.
- **Card slug derivation = filename-after-first-hyphen.** This is a load-bearing API quirk. Collision-prone names get disambiguated by filename (e.g., `track-sugar-track.md` so the slug is `sugar-track` and doesn't collide with `album-sugar.md`'s slug `sugar`).
- **`parse_card()` returns deduped `card["wikilinks"]`** from frontmatter + body. Consumers must not re-extract.
- **Demo-ready threshold:** automated all-green + manual all-green minus explicitly deferred rows. M12 was deferred with documentation, so the tag still applied.

---

## Files written this session

| File | Action |
|---|---|
| `docs/plans/sprint_05172026/session_prompts/_pm-continuation.md` | Overwritten (this file) |
| `docs/plans/sprint_05172026/_sprint-closeout.md` | Created |
| `docs/plans/sprint_05172026/test_registry.md` | Updated (18 automated rows signed off; M1–M11 ✅) |
| `docs/plans/sprint_05172026/session_prompts/{A,B,C,D,E,F,G}-*.md` | HANDOFF blocks appended by each track agent |
| `app.py`, `lib/*.py`, `tests/*.py`, `templates/*`, `static/*`, `graphs/**`, `tools/lint_graphs.py` | Created/expanded by track agents |
| Git tag `v0.1-phase1-demo` | Applied on `92a4955` |

---

## Key files for the next sprint

| File | Role |
|---|---|
| `docs/plans/sprint_05172026/_sprint-closeout.md` | Phase 2 wishlist + lessons learned. Read FIRST for next-sprint kickoff. |
| `docs/plans/sprint_05172026/project_spec.md` | Phase 1 locked spec — Phase 2 builds on top, not around. |
| `docs/plans/sprint_05172026/test_registry.md` | Final demo gate status (M12 deferred row visible). |
| `docs/plans/music-graphs-plan.md` | Original Phase 1 plan + Phase 2/3 ideas at the bottom. |
| `tools/lint_graphs.py` | Pre-merge content check for any new graphs. |
| `lib/cards.py`, `lib/graph.py`, `lib/spotify.py` | Existing module APIs Phase 2 should preserve. |
