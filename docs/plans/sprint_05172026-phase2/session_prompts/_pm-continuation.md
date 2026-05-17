# Sprint Manager Handoff — 2026-05-17 (end of session)

**Written:** 2026-05-17
**Sprint folder:** `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/`
**Main branch HEAD:** `5a8665d pm: Track G (pittsburgh-jazz dogfood) merged; registry signed`
**Demo target:** 2026-06-07
**Task tracking:** None — `music-graphs` is not registered in task_lib. Sprint tracked via this folder + `test_registry.md`.

---

## Current state

**8 of 9 tracks merged.** Only Track H (bowie-covers expansion via `expand-graph`) remains, plus manual M1/M2 family-agent verification by Alec. The sprint is otherwise demo-ready: 100 pytest pass, 0 lint errors across all three graphs, all four foundation skills in place, family agent + setup docs shipped, band-x dogfood (5 albums) and pittsburgh-jazz dogfood (12 albums) both complete with all Alec-specified URLs and personal notes integrated. Worktree for H is pre-created at `/private/tmp/mg-wt-H` on branch `sprint/bowie-covers-expansion`; H is the only foreground track that still needs Alec in the loop (for `expand-graph` candidate approval).

| Wave | Track | Status | Merge SHA |
|---|---|---|---|
| Pre | Tony Gilkyson rename + sprint kickoff | ✅ | `6b76576` |
| 1 | A `retrieve-spotify-song` | ✅ | `c3cccb1` |
| 1 | B `add-node` | ✅ | `6f6195c` |
| 2 | C `add-edge` | ✅ | `7999062` |
| 2 | D `expand-graph` | ✅ | `11a5d45` |
| 3 | E family-agent + setup docs | ✅ | `8a9cfa8` |
| 3 | F band-x dogfood (5 albums) | ✅ | `735e88a` |
| 3 | G pittsburgh-jazz dogfood (12 albums + notes) | ✅ | `6c9c8dd` |
| 4 | I cover images (M12) | ✅ | `b44a25f` |
| 4 | **H bowie-covers via expand-graph + Nirvana retry** | ⏳ **next** | — |

Graph counts after merges:
- band-x: 13n/49e → 18n/55e (+5 nodes, +6 edges)
- pittsburgh-jazz: 16n/37e → 28n/52e (+12 nodes, +15 edges)
- bowie-covers: unchanged (Track H's job)

---

## What happened this session

1. **Resumed sprint kickoff.** Drafted, then locked the Phase 2 project spec at `docs/plans/sprint_05172026-phase2/project_spec.md` after Alec resolved all 5 open questions (cloud-primary agent surface, demo 2026-06-07, album-only default, skill-proposed picks for Exene/Doe, candidate ceiling 5–10).
2. **Pre-sprint setup.** Renamed `person-troy-gilkyson.md` → `person-tony-gilkyson.md` and updated the wikilink in `group-x.md`. Retried Nirvana MTV Unplugged Spotify lookup via MCP — still no match, deferred into Track H.
3. **Wrote 9 track prompts + test registry + this PM continuation file** in the new sprint folder. Committed as `6b76576` (kickoff).
4. **Wave 1 (A + B) launched parallel as background sub-agents.** Both completed clean: A produced `.claude/skills/retrieve-spotify-song/` with fail-loud MCP contract and URL normalizer; B produced `.claude/skills/add-node/` with lint-gate-and-rollback. 11 + 14 helper tests respectively, FAIL=0 in both. Merged B then A.
5. **Wave 2 (C + D) launched parallel.** C produced `.claude/skills/add-edge/` (10 tests, dangling-target detection, duplicate-edge detection); D produced `.claude/skills/expand-graph/` (14 tests, candidate ceiling clamp, dry-run mode, default `search_fn` raises so no training-data candidates leak). Rebased D onto C, merged in order.
6. **Wave 3 launched in stages.** Track E (family agent) ran as a background sub-agent — produced `.claude/agents/music-graphs-builder.md` + `docs/family-setup.md` for both claude.ai/code (cloud, primary) and local Claude Code (fallback), with a rehearsed-against-scratch-graph end-to-end transcript. M1/M2 real-session checks explicitly deferred to Alec.
7. **Track F (band-x dogfood) ran foreground with Alec.** I used the skill helpers directly to write 5 album cards: Ashgrove (Dave Alvin), The Bonebrake Syncopators Play Coleman, Johny Walk Don't Run Paulene (Billy Zoom), Somewhere Gone (Exene Cervenka), A Year in the Wilderness (John Doe). Alec confirmed verified Spotify URLs for the three pre-specified albums and approved my MCP-sourced picks for Exene and John Doe.
8. **Track I (cover images) ran in parallel background.** Picked one image per graph (X 1979 LA; Bowie 2002; Erroll Garner 1947), downloaded from Wikimedia Commons, added a `/graph-images/<slug>/<file>` route to `app.py`. Three `<img>` tags on home page, all return 200.
9. **Track G (pittsburgh-jazz dogfood) ran foreground with Alec.** 12 albums written through the skills: Gene Harris Trio Plus One, No Need for Words, Sweet Candor, Concert by the Sea, Piano Moods, The Peaceful Side, Bass on Top, Song for My Father, Keep the Faith, Kind of Blue (Legacy Edition), ...And His Mother Called Him Bill, Passion Flower. Alec added 4 additional Spotify URLs mid-session (Roger Humphries leader album, Paul Chambers as sideman on Kind of Blue, plus two Strayhorn tribute albums). Three person cards (Sean Jones, Maureen Budway) received hand-appended personal notes via Edit tool because the skills lack a "free-text body addendum" operation. All 10 person cards now have ≥1 album/track wikilink — coverage requirement met.
10. **Did NOT start Track H.** Worktree was created and Alec was about to approve the first batch of expand-graph candidates; Alec interrupted and asked for a session handoff instead.

---

## Immediate next steps (in order)

### Step 1 — Resume as sprint manager
Read this file. Verify repo state with `git log --oneline -3` (expect `5a8665d` at HEAD) and `git worktree list` (expect `main` + `/private/tmp/mg-wt-H` on `sprint/bowie-covers-expansion`). If the worktree is gone (it lives in `/private/tmp/` which clears on reboot), recreate it:
```bash
git worktree add /private/tmp/mg-wt-H -b sprint/bowie-covers-expansion main
ln -sf /Users/alecchapman/Code/music-graphs/.venv /private/tmp/mg-wt-H/.venv
```
(If the branch already exists, drop `-b sprint/bowie-covers-expansion` and add `sprint/bowie-covers-expansion` as the last arg instead.)

### Step 2 — Track H, in foreground (Alec must be present)
Track H prompt: `docs/plans/sprint_05172026-phase2/session_prompts/H-bowie-covers-expansion.md`. The mid-session approach the prior PM was taking:
- Read `graphs/bowie-covers/cards/note-bowie-songbook.md` to state the inclusion criterion back to Alec.
- Generate 5–10 candidate Bowie covers that extend the existing cross-genre diversity (Brazilian acoustic / jazz piano trio / grunge are covered; aim for classical, glam, soul, indie, etc.).
- Verify each candidate's Spotify URL via MCP (`mcp__68e7e171-8619-450d-bfc7-458af6964130__search`). Where MCP can't surface (e.g., licensor-restricted), document `spotify_url: null  # MCP search exhausted` in the frontmatter.
- Surface the candidate list to Alec with proposed wikilinks to existing songs/persons. Wait for approval.
- For approved candidates, write a Python driver script (pattern: `/tmp/track-f-driver.py` and `/tmp/track-g-driver.py`) that calls `write_card` + `add_edge` with explicit `repo_root=` arguments.
- Retry Nirvana MTV Unplugged URL during this session: search Spotify for "About a Girl Unplugged Nirvana" (track) or "Nirvana Unplugged" (different query phrasing). If still no match, write `spotify_url: null  # MCP search exhausted 2026-05-17` into the frontmatter of `graphs/bowie-covers/cards/album-unplugged-in-new-york.md` and call it done.
- Lint + pytest + smoke check (use `app.test_client()` via `import app as a`, not a real Flask process — port 8766 was already bound on Alec's machine earlier).
- Append HANDOFF block to `H-bowie-covers-expansion.md`, commit, rebase onto main, ff-merge, tear down worktree, sign off rows H1/H2 in the test registry, commit the PM signoff.

Candidate ideas the prior PM had in flight (verify before proposing):
- Mott the Hoople — All the Young Dudes (1972) — Bowie-written glam handover
- Lulu — The Man Who Sold the World (1974) — Bowie-produced UK #3
- Phillip Glass — Symphony No. 4 "Heroes" (1996) — classical adaptation
- Peter Gabriel — Heroes (Scratch My Back, 2010) — orchestral solo voice
- Beck — Sound and Vision (2013) — viral 360° orchestra
- Bauhaus — Ziggy Stardust (1982) — goth single
- TV on the Radio — Heroes — indie rock
- Cat Power — Space Oddity — sparse indie folk
Surface these (or your own picks) to Alec; he overrides freely.

### Step 3 — Manual M1/M2 verification (Alec)
After H merges, the only remaining items in the test registry are M1 (family-agent end-to-end on local Claude Code) and M2 (same on claude.ai/code). The PM can't do these — they need Alec to actually run a fresh chat with the music-graphs-builder agent in both environments and add at least one node + one edge to a graph without ever seeing YAML. Surface these to Alec after H merges and ask him when he wants to schedule them.

### Step 4 — Close the sprint
Once H is merged and M1/M2 are signed off, write `_sprint-closeout.md` following the Phase 1 pattern (`docs/plans/sprint_05172026/_sprint-closeout.md`). Tag with a Phase 2 version tag (e.g., `v0.2-phase2-demo`). The closeout should capture: phase-2 delivered scope, the skill-friction notes from F and G's HANDOFFs (especially the `write_card.py` `repo_root` inference bug, the missing free-text-body-addendum operation, and the album-only default the spec locked), and any Phase 3 wishlist (cloud hosting? new graphs?).

---

## Key decisions (do not re-litigate)

- **Sprint folder name:** `sprint_05172026-phase2` (hyphenated form, not the standard `sprint_MMDDYYYY`) — Alec requested explicitly at kickoff.
- **Family-agent surface:** claude.ai/code primary, local Claude Code fallback. Agent + skills must be environment-identical (no env-specific branches). Spotify MCP setup is the one per-machine/per-account dependency.
- **Spotify URL policy:** verified-via-MCP only. Alec-provided URLs are treated as verified once their title/artist is confirmed via WebFetch on the open.spotify.com page. `spotify_url: null` with a documented reason is the locked fallback when MCP can't surface a track.
- **Album-only default for new content.** Track cards only when there's a narrative reason (e.g., Sean Jones cross-appearance on Maureen Budway's "Sweet Lover No More" — handled as a body wikilink with an add-edge call, not a separate track card).
- **Exene/John Doe albums:** picked via MCP top-results, Alec approved at the moment of writing. Somewhere Gone (Cervenka, 2009) and A Year in the Wilderness (Doe, 2007).
- **Pittsburgh-jazz scope override:** the G prompt's "Not in scope" said "no albums for artists not already in the graph", but Alec explicitly approved 4 additional albums whose *leader* isn't in the graph (Horace Silver, Miles Davis, Duke Ellington, Fred Hersch). Treated as in-scope because each album's wikilinks point to existing-in-graph people; the leader is incidental. Loosen the spec wording in Phase 3.
- **Worktree launch model from Phase 1 carried forward:** PM pre-creates worktrees at `/private/tmp/mg-wt-<X>`, sub-agents do NOT call `EnterWorktree` and use `git -C <path>` for every git op. Workflow rule reaffirmed across all 6 sub-agent launches this session — no incidents.
- **F and G ran as foreground PM-driven dogfood**, not background sub-agents. The PM (me) wrote one-shot Python drivers (`/tmp/track-f-driver.py`, `/tmp/track-g-driver.py`) calling the skill helpers directly. This was the right call — Alec needed to be in the loop for album-choice approvals, and the dogfood is more honest when the PM uses the same skill API a family-member agent would.
- **`spotify_url: null` insertion in frontmatter** happens after `write_card` returns, via a small lines-array edit that inserts the `null  # <reason>` line before the closing `---`. The skill's frontmatter writer omits a key when its value is None — that's the right default for the family agent, but Track H needs to keep documenting the null reason when applicable.

---

## Blocking questions

None for the next PM session. Track H can proceed as soon as Alec is available to approve `expand-graph` candidates. The 4 manual rows (M1, M2, plus H's own M-rows) are the only items that can't be PM-resolved.

---

## Skill-bug backlog (surfaced during dogfood, deferred from this sprint)

These are real bugs the F and G HANDOFFs documented. None blocked merging — workarounds exist — but they should be fixed before Phase 3 or before non-Alec users actually run the family agent against the real skills.

1. **`write_card.py` `repo_root` inference is wrong.** `Path(__file__).resolve().parents[3]` resolves to `.claude/` instead of the worktree. Fix: `parents[4]`. Workaround until then: every caller passes explicit `repo_root=`.
2. **No "add free-text body addendum" operation.** The personal-notes additions on `person-sean-jones.md` and `person-maureen-budway.md` had to be hand-edited via the Edit tool. `add-edge` only writes relationship-shaped sentences between two slugs. A future `add-note` / `append-body` skill closes this gap and is high-value for the family agent (which will hit this constantly).
3. **Spotify MCP `ALL_CONTENT_LICENSOR_RESTRICTED` errors are frequent for older catalog.** The skill correctly falls back to null + reason, but the family agent should explain this category in plain English rather than relaying the raw error code.
4. **add-edge relationship verb requires per-call thinking.** "recorded" vs "appears on" vs "honored on" — caller has to vary by case. Family agent should hide this behind a small relationship taxonomy ("leader" / "sideman" / "tribute").

---

## Files written this session

| File | Action |
|---|---|
| `docs/plans/sprint_05172026-phase2/project_spec.md` | Created, locked |
| `docs/plans/sprint_05172026-phase2/test_registry.md` | Created; all rows except H1/H2 and M1–M10 signed off |
| `docs/plans/sprint_05172026-phase2/session_prompts/{A,B,C,D,E,F,G,H,I}-*.md` | Created (track prompts) + HANDOFF blocks appended by each track |
| `docs/plans/sprint_05172026-phase2/session_prompts/_pm-continuation.md` | This file (overwritten as continuation) |
| `graphs/band-x/cards/person-tony-gilkyson.md` | Renamed from `person-troy-gilkyson.md`; `group-x.md` wikilink updated |
| `.claude/skills/{retrieve-spotify-song,add-node,add-edge,expand-graph}/` | Created (Wave 1+2 deliverables) |
| `.claude/agents/music-graphs-builder.md`, `docs/family-setup.md` | Created (Track E) |
| `graphs/band-x/cards/album-*.md` (5 new) | Created (Track F) |
| `graphs/band-x/cards/person-*.md` (5 modified) | Modified (reciprocal edges, Track F) |
| `graphs/pittsburgh-jazz/cards/album-*.md` (12 new) | Created (Track G) |
| `graphs/pittsburgh-jazz/cards/person-*.md` (9 modified) | Modified (reciprocal edges + 2 personal-notes additions, Track G) |
| `graphs/{band-x,bowie-covers,pittsburgh-jazz}/README.md` | Updated `cover_image:` field (Track I) |
| `graphs/{band-x,bowie-covers,pittsburgh-jazz}/images/<file>.jpg` | Created (3 new image files, Track I) |
| `app.py` | Added `/graph-images/<slug>/<file>` route + `_resolve_cover_image` helper (Track I) |

---

## Key files

| File | Role |
|---|---|
| `docs/plans/sprint_05172026-phase2/project_spec.md` | Locked spec; the source of truth for what Phase 2 is. |
| `docs/plans/sprint_05172026-phase2/test_registry.md` | Pass/fail gate. Two rows (H1, H2) and ten manual rows (M1–M10) outstanding. |
| `docs/plans/sprint_05172026-phase2/session_prompts/H-bowie-covers-expansion.md` | Track H prompt — read first thing in the next session. |
| `docs/plans/sprint_05172026/_sprint-closeout.md` | Phase 1 closeout — the template for Phase 2's closeout (Step 4 above). |
| `.claude/skills/expand-graph/SKILL.md` and `scripts/expand_graph.py` | The skill Track H exercises; read its HANDOFF in Track D's prompt for integration gotchas. |
| `.claude/skills/add-node/scripts/write_card.py` | Note the `repo_root` bug — always pass `repo_root=REPO` explicitly until fixed. |
| `tools/lint_graphs.py` | Always green at sprint close — run before any commit. |
| `/tmp/track-f-driver.py`, `/tmp/track-g-driver.py` | Reference one-shot drivers from F and G — Track H's driver should follow the same pattern. (These live in /tmp and may be cleared; the patterns are what matters.) |
