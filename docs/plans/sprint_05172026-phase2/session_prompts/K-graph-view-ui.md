# Track K — Graph view UI polish

**Sprint:** sprint_05172026-phase2 (Phase 2.5)
**Worktree:** `/private/tmp/mg-wt-K` on branch `sprint/graph-view-ui`
**Acceptance gates:** K1, K2, K3 in `test_registry.md`; M13 manual.

## Layout model

Reference: the `/wiki-update` skill's wiki UI — graph dominates the screen, side panel collapses or overlays. Find that reference UI before starting; do not invent a layout.

## What to build

1. **K1 — Big canvas.**
   - Graph canvas ≥80% of viewport width and height.
   - Node-detail side panel becomes an overlay or off-canvas drawer that opens on node click and closes on ESC / outside click. Not a permanent column.
   - Verify on `/graph/band-x`, `/graph/bowie-covers`, `/graph/pittsburgh-jazz`.

2. **K2 — Frozen by default.**
   - Physics simulation paused on page load (nodes static at last layout).
   - Visible "Unfreeze" toggle in the graph controls (button or labeled checkbox). Toggling re-enables physics; toggling back re-freezes at current positions.
   - Persist last layout positions so a freeze-after-drag stays put.

3. **K3 — Zoom buttons.**
   - `+` and `−` buttons in a corner (bottom-right recommended), styled to match existing controls.
   - Scroll-wheel zoom continues to work.
   - Optional: a "fit-to-screen" button (nice-to-have, not required for K3 sign-off).

## Files likely touched

Start by reading:
- `app.py` (graph view route + template wiring)
- `templates/graph.html` (or wherever the graph view is rendered)
- Any JS controlling vis-network / cytoscape (look in `static/` or inline in the template)

Do not refactor unrelated UI. Surgical changes only.

## Done when

- All K-row checks pass via DOM smoke test (puppeteer / playwright if set up, otherwise manual verification documented in commit).
- 100+ pytest pass, lint clean.
- Alec signs M13.
