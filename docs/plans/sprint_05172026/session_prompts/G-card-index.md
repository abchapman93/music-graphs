# Track G — Card index

**Sprint:** `~/Code/music-graphs/docs/plans/sprint_05172026/`
**Branch:** `sprint/card-index` — **use `EnterWorktree` before writing any files.**
**Wave:** 4 (parallel with F)
**Dependencies:**
- **E (graph-view) merged to `main`.**
- Track F is parallel — does NOT need to be complete; the index works against whatever cards exist (the fixture graph alone is enough to develop and test).

## Goal

Implement the `/cards` flat index: server lists every card across every graph; the page provides client-side type filter + free-text search; each row links to its graph view focused on that card.

## Context files to read

- `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026/project_spec.md` — section 8 of MVP behaviors, plus "Demo criteria" (the cards index criteria).
- `/Users/alecchapman/Code/music-graphs/app.py` — current routes; you implement the stubbed `/cards`.
- `/Users/alecchapman/Code/music-graphs/lib/cards.py`, `lib/graph.py` — reuse parsing and listing helpers.
- `/Users/alecchapman/Code/music-graphs/templates/base.html`, `templates/graph.html` — match style.

## Definition of done

- [ ] `app.py` `GET /cards` route implemented:
  - Walks `graphs/<slug>/cards/*.md` for every graph folder under `graphs/`.
  - For each card, computes: `graph_slug`, `card_slug`, `type`, `name`, optional `image`, link target `/graph/<graph_slug>#<type>:<card_slug>` (or `/graph/<graph_slug>/card/<card_slug>` for the deep-link page — pick one and use consistently).
  - Renders `templates/cards.html` with the full list as JSON embedded in a `<script>` tag for client-side filtering.
- [ ] `templates/cards.html`:
  - Extends `base.html`.
  - Top of page: an input `<input id="search">` (free-text search by name) and a `<select id="type-filter">` with options "All" + each of the nine card types.
  - Body: a `<ul id="card-list">` (or table) populated client-side from the embedded JSON.
  - Each row: card name, type badge (color-coded matching the graph node colors from the spec), graph it belongs to, and a link to the card's location in its graph.
- [ ] Client-side filtering in inline `<script>` (or `static/js/cards.js`):
  - Type filter narrows by exact type match (or "all" = no filter).
  - Search filter does a case-insensitive substring match on the card name. Combined AND with type filter.
  - Filtering is debounced 100ms on keystroke; no full re-render — toggle a `data-hidden` attribute or class.
- [ ] Type badges colored per the vis-network styling table in the spec ("Architecture decisions").
- [ ] `/cards` is reachable from a "Browse all cards" link on the home page (`templates/home.html`).
- [ ] Test at `tests/test_routes.py` (extend, don't duplicate):
  - `GET /cards` returns 200.
  - The response HTML contains at least one card name from the fixture or real graphs.
  - The response HTML contains the type-filter `<select>` with all 9 options.

## Test protocol

```bash
cd ~/Code/music-graphs
pytest tests/ -v 2>&1 | tee /tmp/test_results_<task_id>.txt
```
Confirm FAIL=0. Then manually: `python app.py`, visit `/cards`, exercise type filter and search. Capture screenshots-in-words in HANDOFF (e.g., "filtering by Person + search 'turrentine' → 1 result shown").

## Not in scope

- Do **not** modify `lib/cards.py`, `lib/graph.py`, `lib/spotify.py`, or the graph view templates.
- Do **not** author cards — Track F.
- Do **not** add server-side search / pagination. Client-side over ~45 cards is fine.
- Do **not** add tag-based filtering (deferred to Phase 3).
- Do **not** add sorting controls. Default sort by name is fine.

## Handoff protocol

```
HANDOFF:
- /cards route lists <N> cards across <M> graphs (or just the fixture if F not yet merged).
- Type filter options: <9 types + All>.
- Search behavior: case-insensitive substring on card name; debounced 100ms.
- Link target convention chosen: <e.g., "/graph/<slug>/card/<card_slug>"> — applied consistently.
- Manual interaction check: <one line confirming filter + search both work>.
- /tmp/test_results_<task_id>.txt: <path>, FAIL=<count>.
- Deviations: <none / list>.
```

## Close-out

Commit on `sprint/card-index` with subject `feat: /cards flat index + client-side filter & search`. One-paragraph summary.
