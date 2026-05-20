# Phase 2.6 — Graph viewer UX mini-sprint

**Written:** 2026-05-19
**Parent sprint:** sprint_05172026-phase2 (Phase 2.5 still open: Tracks J + M)
**Demo target:** 2026-06-07 (shared with Phase 2.5)
**Tracks:** N (search), O (directory panel), P (panels collapse/resize), Q (editable cards), R (web notes)

---

## Why this exists

The graph viewer ships today as a graph canvas + a thin click-to-view side panel. To make it a real exploration and authoring surface — and to let Alec fix factual errors he's spotting in cards without dropping to a shell — Phase 2.6 layers five UX features on top of the Track-K canvas work.

The model is the wiki UI from `/Users/alecchapman/Code/Claude Setup/app/templates/wiki_viewer.html` (and `tools/wiki_viewer.html`). Reference it before designing layouts; do not invent new patterns where that file already has one.

---

## Tracks

### Track N — Search bar

**Goal:** Top-of-page search that finds any node by display name or slug and centers it on the canvas.

**Deliverables:**
- Sticky search input in `templates/graph.html` (above the canvas, full width of canvas area).
- Client-side fuzzy match over the node list from `/api/graph/<slug>` (or new `/api/cards/<slug>` if N+O share an index).
- Dropdown results list (max 12) with type pill + display name + dim slug.
- Keyboard: ↓/↑ to navigate, Enter to select, Esc to close.
- On select: focus + center the node on canvas (vis-network `selectNodes` + `focus`), open right panel.

**Files likely touched:** `templates/graph.html`, `static/js/graph.js`, `static/css/style.css`, optionally `app.py` (new `/api/cards/<slug>` endpoint shared with Track O).

**Reference patterns from wiki_viewer.html:**
- `#search-input` + `#search-results` styling (lines 179–209)
- `updateSearchResults()` logic (line 850 onward)

### Track O — Directory left panel

**Goal:** A persistent left-side directory listing every card in the current graph, grouped by type, click-to-select.

**Deliverables:**
- New left panel in `templates/graph.html` between the page chrome and the canvas.
- Grouped by card type (person / group / album / song / track / location / genre / note / memory). Each group is a collapsible `<details>` section.
- Row format: small color dot (matching node color) + display name. Click row → select node on canvas + open right panel + scroll into view if off-screen.
- Backed by the same JSON the search bar uses.

**Files likely touched:** `templates/graph.html`, `static/js/graph.js`, `static/css/style.css`, `app.py` (`/api/cards/<slug>` if not added in Track N).

**Reference patterns from wiki_viewer.html:**
- `.filter-section` + `<details>` group styling (lines 156–177)

### Track P — Collapsible / resizable panels

**Goal:** Both side panels (left directory, right detail) can be collapsed and resized; widths persist across page loads.

**Deliverables:**
- Chevron toggle on the outer edge of each panel (collapses to a thin strip with a re-expand chevron).
- Drag-handle on the inner edge of each panel for resize. Min width 200px, max 480px.
- State persisted in `localStorage` keyed by graph slug (or globally — pick one and document).
- Canvas reflows on collapse/resize (vis-network `redraw()`).
- ESC still closes the right panel back to its default-open state.

**Files likely touched:** `static/css/style.css`, `static/js/graph.js`, `templates/graph.html`.

**Reference patterns from wiki_viewer.html:**
- `#app.sidebar-collapsed` grid transition (lines 44–48, 144–147)
- `#sidebarToggle` button (lines 82–88)

### Track Q — Editable cards

**Goal:** Edit a card's markdown body from the right panel, save, re-lint, refresh.

**Deliverables:**
- "Edit" button in the right panel header (next to the close button).
- Click → swaps rendered body for a `<textarea>` containing the raw markdown body (frontmatter excluded — only the body after the frontmatter block).
- Save / Cancel buttons. Save: `PUT /api/cards/<graph_slug>/<card_slug>` with `{body: "..."}`.
- New endpoint `PUT /api/cards/<graph_slug>/<card_slug>` in `app.py`:
  - Reads existing file, splits frontmatter from body, writes new file with same frontmatter + new body.
  - Runs `tools/lint_graphs.py <graph_slug>` after write.
  - On lint fail: restore original file from in-memory backup, return 422 with the lint error message.
  - On success: return updated card JSON.
- Right panel auto-refreshes on save success.
- Edits are not auto-committed; user does `git commit` manually (consistent with how cards are written today).

**Files likely touched:** `app.py`, `templates/_card_panel.html`, `static/js/graph.js`, `static/css/style.css`.

**Out of scope:** Frontmatter editing (deferred — separate track or a future phase). Edge editing.

### Track R — Web note creation

**Goal:** From any selected node, create a new `note-*.md` or `memory-*.md` card with an edge back to the source.

**Deliverables:**
- "+ Note" button in the right panel header.
- Modal with: type radio (note / memory), title (text), body (textarea).
- New endpoint `POST /api/notes/<graph_slug>`:
  - Body: `{type, title, body, source_slug, source_type}`
  - Delegates to the existing `add-node` skill's Python lib (under `lib/` or wherever the skill helpers live; reuse — do not re-implement frontmatter/slug rules).
  - Then calls `add-edge` to write a wikilink from the source card body to the new note.
  - Runs lint; reverts on fail.
  - Returns the new card slug.
- After success, the directory panel refreshes and the new node appears on the canvas (re-fetch `/api/graph/<slug>`).

**Files likely touched:** `app.py`, `templates/_card_panel.html` (new modal partial), `static/js/graph.js`, `static/css/style.css`.

**Out of scope:** Editing existing notes through the web (Track Q handles that). Choosing the link verb (`add-edge` default is fine).

---

## Execution order

1. **N + O together** in worktree `mg-NO-search-directory`. Both are read-only frontend over a shared `/api/cards/<slug>` endpoint. One PR.
2. **P** in worktree `mg-P-panels` once N + O land. Pure CSS/JS polish.
3. **Q** in worktree `mg-Q-edit-cards`. First write endpoint — sets the lint-revert pattern Track R reuses.
4. **R** in worktree `mg-R-web-notes`. Builds on Q's write infra + reuses `add-node`/`add-edge` libs.

Each track:
- Branches off `main` via `EnterWorktree`.
- Reads its session prompt under `session_prompts/`.
- Signs acceptance gates in `test_registry.md` before merge.
- ff-merges to main, tears down worktree.

---

## Out of scope (this mini-sprint)

- Frontmatter editing from web (Q is body-only).
- Edge editing / deletion from web.
- Auto-commit of edits (user still commits manually).
- Mobile/responsive layout polish — desktop only for now.
- Track J (Google Form intake) and Track M (closeout) — still queued under Phase 2.5.

---

## Acceptance summary

See `test_registry.md` for the per-track gates. Demo readiness for Phase 2.6 is when N1–N2, O1–O2, P1–P3, Q1–Q3, R1–R3 are all green and Alec signs the manual rows.
