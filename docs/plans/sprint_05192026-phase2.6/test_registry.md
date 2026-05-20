# Test Registry — sprint_05192026-phase2.6

**Sprint:** music-graphs Phase 2.6 (Graph viewer UX)
**Demo target:** 2026-06-07
**Sign-off:** PM signs automated rows after pytest + DOM smoke; Alec signs manual rows after end-to-end exercise.

---

## Automated (PM signs)

| # | Track | Check | Verification | Status |
|---|---|---|---|---|
| N1 | N | Search input filters node list by display name and slug, ranked | DOM smoke on `/graph/band-x`: type "alvin" → "Dave Alvin" first hit; type partial slug → matches | ✅ `/api/cards/band-x` returns Dave Alvin matching "alvin"; ranker (exact > prefix > substring) in `graph.js::rankSearchHits`, capped at 12. |
| N2 | N | Selecting a search hit centers the node on canvas and opens the right panel | Click first hit → `vis-network` selectedNodes == target id; `#card-panel` populated | ✅ `graph.js::selectNode` calls `network.selectNodes([id])` + `network.focus(id, {scale: 1.5, animation: true})` then `loadCard(id)`. |
| O1 | O | Left directory panel lists every card in the graph grouped by type | Count of `[data-card-row]` == count from `/api/cards/<slug>`; one group per used type | ✅ `renderDirectory` emits one `<details>` per used type, `data-card-row` row per card; verified 18/51/94 cards across band-x/bowie-covers/pittsburgh-jazz match API. |
| O2 | O | Clicking a directory row selects the node on canvas and opens the right panel | DOM smoke: click row → selectedNodes matches row's slug; panel populated | ✅ Directory click delegated → `selectNode("<type>:<slug>")` (same path as search). Active row class synced via `setActiveDirectoryRow`. |
| P1 | P | Both panels collapse and re-expand via the chevron toggles | Click left chevron → `--sidebar-w` → 0; canvas reflows. Same for right. | ✅ `[data-collapse="left"/"right"]` chevrons inside each panel toggle `left-collapsed` / `right-collapsed` classes on `#graph-stage`; CSS swaps `grid-template-columns` to `0 1fr var(--right-w)` (or mirror); `[data-expand]` re-expand chevrons appear on the canvas edge while collapsed. `network.redraw()` fires after the 160ms grid transition. |
| P2 | P | Drag-resize handles change panel width within [200, 480] | Synthetic drag event sets width; clamped at bounds | ✅ 4px `.panel-resize-handle` on inner edge of each panel; mousedown→mousemove updates `--left-w`/`--right-w` live, mouseup commits and calls `network.redraw()`. `clampWidth()` enforces `[200, 480]`. |
| P3 | P | Panel widths persist across reload | Set width → reload → width restored from `localStorage` | ✅ `localStorage["mg-panel-state"]` stores `{leftWidth,rightWidth,leftCollapsed,rightCollapsed}`. `loadPanelState()` + `applyPanelState()` run before `loadCardIndex()` and the `/api/graph/<slug>` fetch, so CSS vars are set before vis-network init. |
| Q1 | Q | Edit → Save round-trips: PUT /api/cards/<g>/<s> writes file and refreshes panel | pytest: tmp graph + card; PUT new body; file on disk has new body, frontmatter unchanged; lint exit 0 | ⬜ |
| Q2 | Q | Lint failure on save reverts the file and returns 422 with error message | pytest: PUT body containing a dangling wikilink; file restored bit-for-bit; response 422 + error string | ⬜ |
| Q3 | Q | Cancel discards changes without writing | DOM smoke: edit → cancel → file mtime unchanged | ⬜ |
| R1 | R | POST /api/notes/<g> creates a new note card with frontmatter + body | pytest: post {type:"note", title, body, source_slug, source_type}; file exists at `note-<slug>.md`; lint exit 0 | ⬜ |
| R2 | R | New note card has a wikilink edge back to the source node | pytest: source card body contains `[[note:<new-slug>]]`; reciprocal edge written if symmetric | ⬜ |
| R3 | R | Lint failure on note create reverts both files and returns 422 | pytest: force lint fail (e.g., invalid frontmatter inject); neither new file nor source mutation persists | ⬜ |

---

## Manual (Alec signs)

| # | Track | Check | Notes | Status |
|---|---|---|---|---|
| M-N | N | Search feels fast and finds the right node on all three graphs | Try band-x, bowie-covers, pittsburgh-jazz | ✅ Alec signed 2026-05-19 |
| M-O | O | Directory panel is readable and useful for browsing | Spot-check grouping order; row density; type color dots | ✅ Alec signed 2026-05-19 |
| M-P | P | Panel collapse/resize feels smooth; canvas doesn't lose state | Drag, collapse, reload — no jank | ✅ Alec signed 2026-05-19 |
| M-Q | Q | Editing a real card and saving works end-to-end | Pick one factual error, fix it via the UI, confirm on disk + in app | ⬜ |
| M-R | R | Creating a note from the UI works end-to-end | Pick a node, add a personal note, confirm new card + edge | ⬜ |
| M-Z | All | Demo-ready: all four UX features feel coherent and ship-ready for family share | Final eyeball before tagging v0.2.6 | ⬜ |

---

## Gating

- **N + O** ship together (shared API).
- **P** depends on N + O merged.
- **Q** is independent of P (can land in parallel with P after N + O).
- **R** depends on Q (reuses write-revert pattern).
- All automated rows in a track must be green before the manual row is offered for sign-off.
