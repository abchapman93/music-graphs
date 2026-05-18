# Sprint Manager Handoff — 2026-05-18 (end of session)

**Written:** 2026-05-18
**Sprint folder:** `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/`
**Main branch HEAD:** `f08157e pm: Track K merged (graph view UI); K1/K2/K3 + M13 signed`
**Demo target:** 2026-06-07
**Task tracking:** None — `music-graphs` is not registered in task_lib. Sprint tracked via this folder + `test_registry.md`.

---

## Current state

**Phase 2.5 planned and one of three tracks shipped.** Phase 2 closed last session with all automated tracks merged. This session: collected Alec's pre-family-share feature requests, dropped Claude-Code-based collaboration (M1/M2/M10), planned Phase 2.5 (tracks J/K/L/M), and shipped Track K (graph view UI).

| Phase / Track | Status | Notes |
|---|---|---|
| Phase 1 | ✅ | tagged v0.1 (prior sprint) |
| Phase 2 automated (Pre, A–I, H) | ✅ | all merged; H closed 2026-05-17 |
| **Phase 2.5 Track K — graph view UI** | ✅ | merged `6fe0ed2`; K1/K2/K3 + M13 signed |
| Phase 2.5 Track J — suggestion intake | ⬜ | session prompt ready |
| Phase 2.5 Track L — Wikipedia seeds | ⬜ | session prompt ready |
| Phase 2.5 Track M — closeout | ⏳ | blocked on J + L |

Graph counts unchanged from end-of-Track-H (band-x 18n/55e, pittsburgh-jazz 28n/52e, bowie-covers 36 cards). 100 pytest pass, lint clean.

---

## What happened this session

1. **Re-oriented as sprint manager** from `_pm-continuation.md` dated 2026-05-17 (Track H closeout). Verified main at `a4da7d1`.
2. **Collected Phase 2.5 feature requests** from Alec:
   - **Goal 1 (scope cut):** family will NOT use Claude Code. Suggestions arrive via Google Form; UI work may happen via a Claude Design project. "Embarrassing if they see it" bar is satisfied by current state.
   - **Goal 2 (UI):** graph view needs big canvas (like wiki-update skill's wiki UI), physics frozen by default, zoom buttons.
   - **Goal 3 (seeds):** Wikipedia Category pages are the primary new resource type for candidate discovery (`Category:Songs_written_by_David_Bowie`, `Category:Jazz_musicians_from_Pittsburgh`).
3. **Wrote Phase 2.5 plan** at `_phase-2.5-plan.md` + session prompts `J-suggestion-intake.md`, `K-graph-view-ui.md`, `L-wikipedia-seeds.md`. Updated `test_registry.md`: marked M1/M2/M10 ⛔ DROPPED; added J1/J2/K1–3/L1–3/Z3/Z4 automated rows and M11–M14 manual rows. Committed `51ee9af`.
4. **Track K driver decision:** Alec said "I drive in a worktree here" (not Claude Design). Intake storage: per-graph `inbox/` (decision baked into J spec).
5. **Track K implementation** in worktree `mg-K-graph-view`:
   - `templates/base.html`: added `{% block body_class %}` so graph view can opt into full-bleed layout.
   - `templates/graph.html`: replaced `.layout-graph` two-column with `.graph-shell > .graph-stage > .graph-canvas-wrap` + side panel.
   - `static/css/style.css`: full-bleed override for `body.graph-page main.container`; grid `minmax(0, 1fr) clamp(280px, 22vw, 380px)`; controls top-right of canvas; explicit `height: calc(100vh - 53px)` on `.graph-shell` (fix for vis-network zero-height-init bug).
   - `static/js/graph.js`: physics freeze on `stabilizationIterationsDone`; "Frozen" checkbox toggle; zoom in/out/fit handlers using `network.moveTo({ scale })` and `network.fit()`.
   - `tests/test_routes.py`: added DOM assertions for `graph-page`, `zoom-in`, `zoom-out`, `zoom-fit`, `freeze-toggle`.
6. **Pre-merge friction (worth noting):** Initial Edit calls used absolute paths to `/Users/alecchapman/Code/music-graphs/...` instead of the worktree path. Caught by smoke-check returning old HTML. Fixed by copying files from main → worktree and `git checkout`-ing main. **Lesson for next worktree session: in a worktree, use relative paths or verify `pwd` before editing.**
7. **Live UI eyeball:** Killed a stale Flask server (PID 10436 from main repo) that was bound to port 8766 and serving the old templates. Restarted from the worktree. After hard-refresh Alec confirmed UI: "really good. I feel satisfied with the UI changes."
8. **Merge + sign-off:** Committed `6fe0ed2`, ff-merged to main, removed worktree. Updated `test_registry.md` (K1/K2/K3 + M13 ✅), committed `f08157e`.

---

## Immediate next steps (in order)

### Step 1 — Track L (Wikipedia seeds) — recommended next

**Why first:** Lightest blocker, pure additive, no UI risk. Result is immediately useful for `expand-graph` and for Track J's eventual triage flow.

**Session prompt:** `docs/plans/sprint_05172026-phase2/session_prompts/L-wikipedia-seeds.md`

**Worktree:** `mg-L-wikipedia-seeds` on a fresh branch from main.

**Deliverables (full detail in session prompt):**
- New skill `skills/retrieve-wikipedia-category/` (mirror `retrieve-spotify-song/` structure)
- `expand-graph` enhancement: reads `seed_sources:` from graph root card, augments Spotify-MCP candidates with Wikipedia-sourced ones, dedupes against existing slugs
- Update root cards: bowie-covers (`Category:Songs_written_by_David_Bowie`), pittsburgh-jazz (`Category:Jazz_musicians_from_Pittsburgh`); skip band-x unless Alec provides a category
- Document the seed-source pattern

**Acceptance gates:** L1, L2, L3 automated + M14 manual.

### Step 2 — Track J (Google Form suggestion intake)

**Session prompt:** `docs/plans/sprint_05172026-phase2/session_prompts/J-suggestion-intake.md`

**Worktree:** `mg-J-suggestion-intake`.

**Deliverables (full detail in session prompt):**
- `graphs/{band-x,bowie-covers,pittsburgh-jazz}/inbox/` folders with `.gitkeep` + README
- New skill `skills/triage-suggestion/` (one-row-at-a-time CSV review → `add-node`/`add-edge` reuse; processed/rejected rotation)
- `docs/family-collaboration.md` documenting the form → CSV → triage flow (Alec to fill in actual Google Form URL after publishing)
- Fix `write_card.py` `repo_root` inference bug while in this track (it will trip on `triage-suggestion`)

**Acceptance gates:** J1, J2 automated + M11, M12 manual.

### Step 3 — Track M (sprint closeout)

**Blocked on:** Tracks J and L merged AND manual M3, M4, M5, M6, M7, M8, M9, M11, M12, M14 signed by Alec.

**Deliverables:**
- Sign Z3, Z4 (final pytest + lint after Phase 2.5 merges)
- `_sprint-closeout.md` covering both Phase 2 and Phase 2.5 (template: `docs/plans/sprint_05172026/_sprint-closeout.md`)
- `git tag v0.2-phase2-demo`

---

## Key decisions (do not re-litigate)

- **M1, M2, M10 are dropped, not deferred.** Family won't use Claude Code. The collaboration model is Google Form → CSV → `triage-suggestion`. Don't re-add Claude-Code-onboarding scope.
- **Track K side-panel width:** kept right-side panel at `clamp(280px, 22vw, 380px)`. Alec explicitly rejected the slide-out drawer mid-implementation in favor of always-visible side panel with a wider graph share. Don't revisit.
- **K controls position:** top-right corner of canvas (Alec said "prefer the zoom tools to be placed at the top of the graph view instead of the bottom"). Don't move to bottom.
- **`.graph-shell` explicit height (`calc(100vh - 53px)`)** is intentional — vis-network needs a non-zero canvas at init. Don't remove in favor of pure flex sizing without testing.
- **Intake storage is per-graph (`graphs/{slug}/inbox/`)**, not top-level. The Google Form must ask which graph the suggestion is for.
- **Track L uses Wikipedia API** (`?action=query&list=categorymembers&...`), not HTML scraping. Same fail-loud contract as `retrieve-spotify-song`.

---

## Blocking questions

- **band-x Wikipedia seed:** No obvious Category URL for the band X (1980s LA punk). Track L's L3 row says "skip band-x unless Alec provides one." Either Alec hands over a URL during the L session, or band-x stays without `seed_sources:` and L3 is signed as "n/a for band-x."

---

## Files written this session

| File | Action |
|---|---|
| `docs/plans/sprint_05172026-phase2/_phase-2.5-plan.md` | created |
| `docs/plans/sprint_05172026-phase2/session_prompts/J-suggestion-intake.md` | created |
| `docs/plans/sprint_05172026-phase2/session_prompts/K-graph-view-ui.md` | created |
| `docs/plans/sprint_05172026-phase2/session_prompts/L-wikipedia-seeds.md` | created |
| `docs/plans/sprint_05172026-phase2/test_registry.md` | updated (M1/M2/M10 dropped; J/K/L/Z3/Z4/M11–M14 added; K1/K2/K3/M13 signed) |
| `templates/base.html` | updated (`{% block body_class %}`) |
| `templates/graph.html` | rewritten (graph-shell layout) |
| `static/css/style.css` | updated (full-bleed + controls + drawer-less side panel) |
| `static/js/graph.js` | updated (freeze + zoom controls; freeze on stabilization) |
| `tests/test_routes.py` | updated (DOM assertions for new controls) |
| `docs/plans/sprint_05172026-phase2/session_prompts/_pm-continuation.md` | **this file — overwritten** |

---

## Skill-bug backlog (carry-forward — unchanged from Phase 2)

1. **`write_card.py` `repo_root` inference wrong in worktrees** — fix during Track J.
2. **No "add free-text body addendum" op** — consider splitting `add-memory` / `append-body` helper out of Track J if cleanest.
3. **Spotify `ALL_CONTENT_LICENSOR_RESTRICTED` user-facing message** — minor copy fix, do during L if touching candidate review.
4. **`add-edge` relationship verb taxonomy** — defer to Phase 3.

---

## Key files

| File | Role |
|---|---|
| `docs/plans/sprint_05172026-phase2/_phase-2.5-plan.md` | Full Phase 2.5 track briefs |
| `docs/plans/sprint_05172026-phase2/test_registry.md` | Pass/fail gate — K row signed; J/L/M outstanding |
| `docs/plans/sprint_05172026-phase2/session_prompts/L-wikipedia-seeds.md` | Next-track launch prompt |
| `docs/plans/sprint_05172026-phase2/session_prompts/J-suggestion-intake.md` | Following-track launch prompt |
| `docs/plans/sprint_05172026-phase2/session_prompts/_pm-continuation.md` | This file — re-entry point for next PM session |
| `templates/graph.html`, `static/css/style.css`, `static/js/graph.js` | Phase 2.5 K deliverables — reference for any future graph view work |
| `tools/lint_graphs.py` | Always green — run before any commit |
