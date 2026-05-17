# Track D — Graph builder

**Sprint:** `~/Code/music-graphs/docs/plans/sprint_05172026/`
**Branch:** `sprint/graph-build` — **use `EnterWorktree` before writing any files.**
**Wave:** 2
**Dependencies:**
- **B (card-parser) must be merged to `main`.** `lib/cards.py:parse_card` must return the schema in the spec.
- Test by running `python -c "from lib.cards import parse_card"` from the worktree root after pulling main.

## Goal

Implement `lib/graph.py` with `build_graph(graph_dir) -> {nodes, edges}` and `list_graphs(graphs_root) -> [...]` per the spec. Pure-Python, no Flask. Backed by unit tests over a small fixture graph.

## Context files to read

- `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026/project_spec.md` — sections "Module signatures", "Data contracts" (the "Graph JSON" output shape is the contract).
- `/Users/alecchapman/Code/music-graphs/lib/cards.py` — the upstream parser you call into.
- `/Users/alecchapman/Code/Claude Setup/tools/wiki_lib.py` — reference for `build_graph` pattern; reuse the dedup / dangling-edge logic structure.

## Definition of done

- [ ] `lib/graph.py` exports:
  - `build_graph(graph_dir: pathlib.Path) -> dict` returning `{"nodes": [...], "edges": [...]}` matching the Graph JSON schema in the spec.
  - `list_graphs(graphs_root: pathlib.Path) -> list[dict]` returning entries with keys `slug`, `name`, `description`, `cover_image`, `card_count`.
- [ ] `build_graph` behavior:
  - Reads every `*.md` file in `<graph_dir>/cards/`.
  - For each card, computes node id as `"<type>:<slug>"` (use the type from frontmatter and the slug from the parsed card).
  - Node fields: `id`, `label` (= card name), `group` (= type, used for vis-network styling), `title` (= short tooltip: name + type).
  - Edges: for each wikilink `(type, slug)` in a card, emit an edge from the source card's id to `"<type>:<slug>"` **only if a card with that id exists in the same folder**.
  - Drops self-loops (source id == target id).
  - De-duplicates edges (an edge is identified by the unordered pair `frozenset({from, to})` — so A→B and B→A collapse to one edge).
  - Dangling wikilinks (target card not in folder) are NOT included as edges. Log them via `logging.getLogger(__name__).debug(...)` — do not print.
  - Returns deterministic ordering: nodes sorted by id, edges sorted by (from, to).
- [ ] `list_graphs` behavior:
  - Iterates subfolders of `<graphs_root>` that contain a `cards/` subfolder.
  - For each, reads `<graphs_root>/<slug>/README.md` for frontmatter `name`, `description`, `cover_image`. Falls back gracefully: missing README → name=slug, description="", cover_image=None.
  - `card_count` = number of `*.md` files in `cards/`.
  - Returns the list sorted by slug.
- [ ] Test fixture at `tests/fixtures/graphs/fixture-graph/`:
  - `README.md` with frontmatter `name`, `description`, `cover_image`.
  - `cards/person-alice.md` linking to `[[person:bob]]` and `[[location:wonderland]]`.
  - `cards/person-bob.md` linking back to `[[person:alice]]` (tests dedup).
  - `cards/location-wonderland.md` (no outbound links).
  - `cards/person-charlie.md` linking to `[[person:nonexistent]]` (tests dangling).
- [ ] Tests at `tests/test_graph.py`:
  - `build_graph` on fixture returns 4 nodes (alice, bob, wonderland, charlie).
  - Edges count = 2 (alice↔bob deduped to 1, alice→wonderland = 1). Charlie's dangling link produces 0 edges.
  - Self-loop test: add a temp card with `[[type:self-slug]]` pointing to itself; assert it's dropped.
  - `list_graphs` on `tests/fixtures/graphs/` returns at least the fixture-graph entry with correct fields.
- [ ] All tests pass.

## Test protocol

```bash
cd ~/Code/music-graphs
pytest tests/test_graph.py -v 2>&1 | tee /tmp/test_results_<task_id>.txt
```
Confirm FAIL=0. Also re-run the full suite to confirm no regression in tests from Tracks B and C:
```bash
pytest tests/ -v 2>&1 | tee -a /tmp/test_results_<task_id>.txt
```
Log path in HANDOFF.

## Not in scope

- Do **not** touch `app.py`, templates, or static assets.
- Do **not** modify `lib/cards.py` or `lib/spotify.py`. If you discover the cards.py contract is broken or insufficient, STOP and add a HANDOFF note describing the gap — do not patch cards.py from this track. The Sprint Manager will spawn a fix session for B.
- Do **not** read or build real `graphs/<slug>/` content. Only the fixture under `tests/fixtures/graphs/`.

## Handoff protocol

```
HANDOFF:
- lib/graph.py exports: build_graph, list_graphs.
- Edge semantics: undirected (A→B and B→A dedupe to a single edge). Confirmed deterministic ordering.
- Dangling wikilinks logged at DEBUG, not rendered. Track E may want to surface a /api/lint endpoint later — not in scope here.
- Fixture: tests/fixtures/graphs/fixture-graph/ (4 cards, 2 expected edges).
- /tmp/test_results_<task_id>.txt: <path>, FAIL=<count>.
- Integration notes for Track E: <e.g., "list_graphs returns cover_image as a raw path/URL from frontmatter; templates must resolve relative paths to /static/graphs/...">.
- Deviations: <none / list>.
```

## Close-out

Commit on `sprint/graph-build` with subject `feat(lib): build vis-network graph + list_graphs`. One-paragraph summary.

---

HANDOFF:
- lib/graph.py exports: build_graph, list_graphs.
- Edge semantics: undirected (A→B and B→A dedupe to a single edge via frozenset key). Self-loops dropped. Nodes sorted by id; edges sorted by (from, to) for deterministic output.
- Dangling wikilinks logged at DEBUG via logging.getLogger(__name__), not rendered. Track E may want to surface a /api/lint endpoint later — not in scope here.
- Consumed Track B's `card["wikilinks"]` directly (already deduped/merged from frontmatter + body); did not re-extract.
- Fixture: tests/fixtures/graphs/fixture-graph/ — 4 cards (person-alice, person-bob, person-charlie, location-wonderland), 2 expected edges. README.md carries name/description/cover_image frontmatter for list_graphs coverage.
- /tmp/test_results_track-D.txt: FAIL=0 (7 graph tests + 41 full-suite tests pass).
- Integration notes for Track E:
  - `list_graphs` returns `cover_image` as the raw value from README frontmatter (string path or None). Track E's templates must resolve relative paths to `/static/graphs/<slug>/<cover_image>` or similar.
  - Node `title` is a short tooltip `"<name> (<type>)"` — Track E can override or extend at render time but vis-network will pick it up by default.
  - `build_graph` tolerates a missing `cards/` subdir (returns empty graph) and an unparseable card file (skipped with DEBUG log) — safe to call on real graph folders.
- Deviations: none.
