# Tracks N + O — Search bar + Directory left panel

**Sprint:** sprint_05192026-phase2.6
**Worktree:** create via `EnterWorktree` (suggested branch: `sprint/search-directory`)
**Acceptance gates:** N1, N2, O1, O2 in `test_registry.md`; M-N, M-O manual.

## Why these ship together

Both features read the same listing of cards-in-graph. Build the shared API once.

## Reference UI

`/Users/alecchapman/Code/Claude Setup/app/templates/wiki_viewer.html`:
- Search input + dropdown: `#search-input` / `#search-results` / `.search-result-item` (lines ~179–209, JS ~850–880)
- Collapsible grouped lists: `.filter-section` + `<details>` (lines ~156–177)

Open that file first. Lift styling cues; do not invent new patterns where it already has one.

## What to build

### Shared API

Add to `app.py`:

```python
@app.route("/api/cards/<graph_slug>")
def api_cards(graph_slug):
    """JSON list of every card in a graph for client-side search + directory."""
```

Returns `[{slug, type, name, image_url|null}, ...]` sorted by `(type, name.lower())`. Use `parse_card` so we get the same data the panel uses; skip files that fail to parse.

### Track N — Search

In `templates/graph.html`, add a sticky search input above the canvas (full canvas-area width). In `static/js/graph.js`:

- On graph load, fetch `/api/cards/<slug>` once and cache in memory.
- Input handler: filter case-insensitively against `name` and `slug`; rank exact > prefix > substring; cap at 12 hits.
- Render results as a dropdown beneath the input (absolutely positioned). Each row: color dot (from existing type→color map), display name, dim slug, type pill.
- Keyboard: ↓/↑ navigate, Enter selects, Esc clears.
- Selection: call existing `selectNode(slug)` (or equivalent) — must center node on canvas (`network.focus(nodeId, {scale: 1.5, animation: true})`) and open right panel via the existing click path.

### Track O — Directory panel

Add a new left panel in `templates/graph.html`. Use a CSS grid so the layout is `directory | canvas | detail`. Default left width 240px.

- Render groups in this order: person, group, album, song, track, location, genre, note, memory.
- Each group is `<details open>` with summary "TYPE (N)".
- Row: color dot + display name. `data-slug` + `data-type` attributes so click selects the node.
- Click handler: same `selectNode(slug)` path as search.

## Files likely touched

- `app.py` (new `/api/cards/<slug>` route)
- `templates/graph.html` (search input, left panel markup)
- `static/js/graph.js` (fetch + search + directory click handlers)
- `static/css/style.css` (layout grid, search dropdown, directory styling)

## Done when

- N1, N2, O1, O2 all signed in `test_registry.md`.
- 126+ pytest pass; lint clean.
- Visually verified on all three graphs.
- ff-merge to main.
