# Phase 2.5 — Pre-family-share polish

**Written:** 2026-05-17
**Parent sprint:** sprint_05172026-phase2
**Demo target:** 2026-06-07 (unchanged)
**Tracks:** J (suggestion intake), K (graph view UI), L (Wikipedia seeds), M (closeout)

---

## Why this exists

Phase 2 closed with all automated tracks merged. Before sharing with Clare/Jeremiah, Alec changed the collaboration model: instead of Claude Code, family contributes via Google Form. That moots M1/M2/M10 and adds three new feature areas:

1. **Intake from Google Form** (replaces family-agent UX)
2. **Graph view UI polish** (big canvas, frozen-by-default, zoom buttons)
3. **Wikipedia categories as candidate seed sources** (for `expand-graph` and new-graph setup)

---

## Track J — Google Form suggestion intake

**Goal:** Family members submit suggestions via Google Form → CSV exports drop into per-graph `inbox/` folders → Alec runs `triage-suggestion` skill to review and accept/reject candidates.

**Deliverables:**
- `graphs/{slug}/inbox/` folder for all 3 graphs with `.gitkeep` + short README explaining the drop-CSV-here flow.
- New skill `skills/triage-suggestion/`:
  - Reads one CSV row at a time from a specified inbox path.
  - Presents the suggestion to Alec (suggester, suggested item, why, optional URL).
  - Calls `add-node`/`add-edge` on approval (reusing existing skills — no direct writes).
  - Moves processed rows to `inbox/_processed/<date>.csv` (append-only log) so they don't get re-triaged.
- `docs/family-collaboration.md`: explains the form → CSV → triage flow; holds the Google Form URL once Alec publishes it.

**Form fields (Alec to create the actual form):**
- Your name (suggester)
- Which graph? (dropdown: band-x / bowie-covers / pittsburgh-jazz)
- What are you suggesting? (free text: "Add album X by Y", "Add a memory about Z")
- Why / what's the connection? (free text)
- Optional: Spotify or Wikipedia URL
- Optional: any memory or personal note to attach

**Out of scope:** Auto-polling the form. Alec exports CSV manually and drops it in the right inbox folder.

**Acceptance:** J1, J2 automated + M11, M12 manual.

---

## Track K — Graph view UI polish

**Goal:** Make the graph view feel like a real exploration surface instead of a thumbnail.

**Driver:** Alec drives in a worktree here (not Claude Design).

**Model:** The `/wiki-update` skill's wiki UI is the layout reference — graph dominates the screen.

**Deliverables:**
- **K1 — Big canvas:** Graph canvas ≥80% of viewport. Side panel (node details) collapses to an overlay or off-canvas drawer, not a permanent column.
- **K2 — Frozen by default:** Physics simulation paused on load. Visible "Unfreeze" toggle (button or checkbox) in the graph controls. Re-freeze available.
- **K3 — Zoom buttons:** `+` / `−` buttons in a corner (probably bottom-right). Scroll-zoom continues to work alongside.

**Files likely touched:** `app.py` (graph view template), `templates/graph.html` (or wherever the graph view lives), any JS controlling the vis-network / cytoscape instance.

**Acceptance:** K1, K2, K3 automated (visual smoke + DOM checks) + M13 manual.

---

## Track L — Wikipedia category as seed source

**Goal:** When creating a new graph or expanding an existing one, the workflow knows to look at relevant Wikipedia Category pages for candidate additions.

**Seed pattern:**
```yaml
# in graphs/<slug>/cards/README.md frontmatter (or graph root card)
seed_sources:
  - https://en.wikipedia.org/wiki/Category:Songs_written_by_David_Bowie
  - https://en.wikipedia.org/wiki/Category:Jazz_musicians_from_Pittsburgh
```

**Deliverables:**
- New skill `skills/retrieve-wikipedia-category/`:
  - Input: a Wikipedia Category URL.
  - Output: list of member pages `[{title, url}, ...]`, paginated if needed.
  - Fail-loud on 404 / non-category URLs (same contract pattern as `retrieve-spotify-song`).
- `expand-graph` enhancement:
  - Reads `seed_sources:` from the graph root card.
  - For each Wikipedia category URL, calls `retrieve-wikipedia-category` and dedupes against existing graph slugs.
  - Surfaces top N new candidates alongside (or instead of) Spotify-MCP candidates.
- Update existing graph root cards:
  - bowie-covers: `Category:Songs_written_by_David_Bowie`
  - pittsburgh-jazz: `Category:Jazz_musicians_from_Pittsburgh`
  - band-x: skip unless Alec points to a category (no obvious one).
- Document the seed-source pattern in `docs/skills-overview.md` (or wherever the skill catalog lives) so new graphs start with seed URLs.

**Acceptance:** L1, L2, L3 automated + M14 manual.

---

## Track M — Sprint closeout

**Goal:** Sign off remaining manual rows, write closeout, tag release.

**Deliverables:**
- Sign off M3, M4, M5, M6, M7, M8, M9 (carried from Phase 2) plus M11–M14 (Phase 2.5).
- Sign off Z3, Z4.
- `_sprint-closeout.md` covering both Phase 2 and Phase 2.5:
  - Delivered scope (all tracks A–L).
  - Scope cuts (M1, M2, M10 dropped — explain why).
  - Skill-friction notes from F, G, H HANDOFFs + any new ones from J/K/L.
  - Phase 3 wishlist (cloud hosting? new graphs from scratch using Wikipedia seeds? `add-memory` skill split out from `triage-suggestion`?).
- `git tag v0.2-phase2-demo` on the final merge commit.

---

## Execution order

Tracks are roughly independent. Recommended order (lightest blockers first):
1. **L** (Wikipedia seeds) — pure additive, no UI risk.
2. **J** (intake) — depends on inbox folder convention but otherwise additive.
3. **K** (UI) — touches app.py / templates; do last to avoid merge conflicts with L if L touches templates.
4. **M** (closeout) — after all of the above.

Each track runs in its own worktree (`/private/tmp/mg-wt-{J,K,L}`), follows the Phase 2 merge pattern: branch → implement → lint → pytest → commit → rebase onto main → ff-merge → tear down worktree → sign registry rows.

---

## Skill-bug backlog (carry-forward from Phase 2)

Still open; fix opportunistically inside the relevant track:
1. `write_card.py` `repo_root` inference wrong in worktrees → fix during J (the new triage skill will trip on this).
2. No "add free-text body addendum" op → consider splitting an `add-memory` or `append-body` helper out of J if it's the cleanest path.
3. Spotify `ALL_CONTENT_LICENSOR_RESTRICTED` user-facing message → minor copy fix, do during L if touching candidate review.
4. `add-edge` relationship verb taxonomy → defer to Phase 3 unless J needs it.
