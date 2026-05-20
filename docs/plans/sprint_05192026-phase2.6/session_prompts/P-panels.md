# Track P — Collapsible / resizable panels

**Sprint:** sprint_05192026-phase2.6
**Depends on:** Tracks N + O merged
**Worktree:** create via `EnterWorktree` (suggested branch: `sprint/panels`)
**Acceptance gates:** P1, P2, P3 in `test_registry.md`; M-P manual.

## Reference UI

`/Users/alecchapman/Code/Claude Setup/app/templates/wiki_viewer.html`:
- `#app.sidebar-collapsed` grid-template-columns transition (lines ~44–48, 144–147)
- `#sidebarToggle` chevron button (lines ~82–88)

## What to build

### Collapse toggles

A chevron button (◀ / ▶) on the inner edge of each panel — clicking flips a class on `#app` that drives `grid-template-columns` to collapse that panel. A re-expand chevron stays visible on the outer edge when collapsed (or on a thin strip).

### Resize handles

A 4px-wide drag handle on the inner edge of each panel. Mouse-down → mouse-move updates a CSS custom property (`--left-w`, `--right-w`); mouse-up commits.

- Clamp width to `[200, 480]`.
- On resize end and on collapse/expand, call `network.redraw()` so vis-network re-fits.

### Persistence

State stored in `localStorage`:

```
{
  "leftWidth": 240,
  "rightWidth": 320,
  "leftCollapsed": false,
  "rightCollapsed": false
}
```

Key: `mg-panel-state` (global, not per-graph — keep it simple). Restore on load before first render.

### ESC behavior

ESC still closes the right panel back to its default state (this exists today via Track K — preserve it, but make sure ESC reverts to the user's saved width, not a hard-coded width).

## Files likely touched

- `static/css/style.css` (CSS vars, transitions, collapsed states)
- `static/js/graph.js` (drag handlers, localStorage, redraw)
- `templates/graph.html` (chevron + handle markup)

## Done when

- P1, P2, P3 signed.
- 126+ pytest pass; lint clean.
- Drag + collapse + reload feels smooth on all three graphs.
- ff-merge to main.
