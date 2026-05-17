# Track E — Graph view (integration)

**Sprint:** `~/Code/music-graphs/docs/plans/sprint_05172026/`
**Branch:** `sprint/graph-view` — **use `EnterWorktree` before writing any files.**
**Wave:** 3
**Dependencies:**
- **A (skeleton-flask), B (card-parser), C (spotify-embed), D (graph-build) all merged to `main`.**
- Verify before starting: `python -c "from lib.cards import parse_card; from lib.graph import build_graph, list_graphs; from lib.spotify import spotify_embed_url; print('ok')"` must print `ok` from the worktree root.

## Goal

Wire the modules from Waves 1–2 into a fully working `/graph/<slug>` view: vis-network rendering on the left, clickable card panel on the right with rendered markdown + Spotify embed, and `[[wikilink]]` clicks that focus/zoom the target node and load its card. Also wire `/api/graph/<slug>`, `/api/card/<graph_slug>/<card_slug>`, `/graph/<slug>/card/<card_slug>` (server-rendered single-card page for deep links). Replace the home page stubs from Track A with real data via `list_graphs`. **Seed a 5-card `graphs/pittsburgh-jazz-fixture/` folder for end-to-end testing.**

## Context files to read

- `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026/project_spec.md` — sections "Architecture decisions" (vis-network styling table, server-rendered + small vanilla JS), "Demo criteria" (what the user must be able to do), "Data contracts".
- `/Users/alecchapman/Code/Claude Setup/tools/wiki_viewer.html` — the closest reference for vis-network + side-panel UX. Reuse the network config and event wiring.
- `/Users/alecchapman/Code/Claude Setup/tools/wiki_viewer_core.py` — Flask route patterns for graph + card endpoints.
- `/Users/alecchapman/Code/music-graphs/app.py` — current state (route stubs from Track A you will fill in).
- `/Users/alecchapman/Code/music-graphs/lib/cards.py`, `lib/graph.py`, `lib/spotify.py` — what you're integrating.

## Definition of done

- [ ] `app.py` routes implemented (replacing 501 stubs):
  - `GET /` — renders home with `list_graphs(graphs_root)` data, including cover images and card counts.
  - `GET /graph/<slug>` — renders `templates/graph.html`. Server passes `{slug, name, description}` and the graph view bootstraps via JS fetching `/api/graph/<slug>`.
  - `GET /api/graph/<slug>` — returns the JSON from `build_graph(graphs_root/slug)`. 404 if folder doesn't exist.
  - `GET /api/card/<graph_slug>/<card_slug>` — returns JSON `{type, slug, name, frontmatter, body_html, spotify_embed_url}` where `spotify_embed_url` is the result of `spotify_embed_url(frontmatter.get("spotify_url"))`. The endpoint must resolve a card by `<card_slug>` matching the slug derived from filename. 404 if no matching card.
  - `GET /graph/<slug>/card/<card_slug>` — server-rendered single-card page (for deep links / no-JS fallback). Uses `templates/card.html`.
  - `GET /cards` — **leave as 501 stub** (Track G owns this).
- [ ] `templates/graph.html`:
  - Extends `base.html`.
  - Two-column layout: `<div id="graph">` on the left (~60% width), `<div id="card-panel">` on the right (~40%).
  - Loads vis-network from CDN (`https://unpkg.com/vis-network/standalone/umd/vis-network.min.js`).
  - Loads `/static/js/graph.js` after passing graph slug via a `<script>` `window.GRAPH_SLUG = "{{ slug }}";` line.
  - Card panel renders: image (if set), name (h1), type, definition list of selected frontmatter fields (skip `body`, `name`, `type`, `spotify_url`, `image`), rendered `body_html`, and the Spotify iframe if `spotify_embed_url` is set.
- [ ] `templates/card.html` — server-rendered single card page (for `/graph/<slug>/card/<card_slug>`). Uses the same partial layout as the right panel of `graph.html`. Include a "← back to graph" link.
- [ ] `static/js/graph.js`:
  - On load: fetches `/api/graph/${GRAPH_SLUG}`, builds a `vis.Network` in `#graph` with nodes/edges.
  - Node styling per spec ("Architecture decisions" table). Use vis-network `groups` config to style by `node.group` (= card type).
  - Click on a node → fetch `/api/card/${GRAPH_SLUG}/${node.id.split(":")[1]}`, render into `#card-panel`. Use plain DOM (`innerHTML` for body_html, escape text for frontmatter values).
  - Wikilinks inside `body_html` carry `data-wikilink="<type>:<slug>"`. Delegate-listen on `#card-panel` for clicks on `[data-wikilink]`; on click, prevent default, call the same node-click handler with the target id, and `network.focus(id, {scale: 1.2, animation: true})`.
  - Initial load: focus the first node in the response and auto-load its card so the panel is never empty.
- [ ] `static/css/style.css` updated with:
  - `.layout-graph` two-column flex/grid.
  - `#graph` height 70vh, border.
  - `#card-panel` overflow-y auto, padding, max-height match.
  - Spotify iframe full-width with height 152px (track default) or 352px for album/playlist (use a `data-spotify-kind` attribute set in the template).
- [ ] **Fixture graph seeded** at `graphs/pittsburgh-jazz-fixture/`:
  - `README.md` with frontmatter `name: "Pittsburgh Jazz (fixture)"`, `description`, `cover_image: null`.
  - 5 cards covering at least: 2 Persons (e.g., Stanley Turrentine, Earl Hines), 1 Location (Pittsburgh), 1 Album (with a real Spotify album URL), 1 Track (with a real Spotify track URL).
  - Wikilinks between cards so the graph has at least 5 edges.
  - Bodies can be 2–3 sentences each, placeholder content is fine — Track F will replace with real bios when authoring the real `pittsburgh-jazz/` folder.
- [ ] **Integration check (runApp equivalent):**
  - Start `python app.py` in a background shell.
  - `curl -s http://127.0.0.1:8766/api/graph/pittsburgh-jazz-fixture | python -m json.tool` returns nodes + edges.
  - `curl -s http://127.0.0.1:8766/api/card/pittsburgh-jazz-fixture/<one of the slugs you authored> | python -m json.tool` returns the card JSON including a working `spotify_embed_url`.
  - `curl -sI http://127.0.0.1:8766/graph/pittsburgh-jazz-fixture | head -1` returns 200.
  - Document each curl result in the HANDOFF note.
- [ ] Unit tests at `tests/test_routes.py` (using Flask test client):
  - `/`, `/graph/pittsburgh-jazz-fixture`, `/api/graph/pittsburgh-jazz-fixture`, `/api/card/pittsburgh-jazz-fixture/<known-slug>` all return 200 and (for JSON endpoints) the expected schema keys.
  - `/api/graph/does-not-exist` returns 404.
  - `/api/card/pittsburgh-jazz-fixture/does-not-exist` returns 404.
- [ ] All tests pass; full suite (`pytest tests/`) green.

## Test protocol

```bash
cd ~/Code/music-graphs
pytest tests/ -v 2>&1 | tee /tmp/test_results_<task_id>.txt
```
Confirm FAIL=0. Then run the integration curls (above), append each command + first 5 lines of output to the same file. Log path in HANDOFF.

## Not in scope

- Do **not** author the real `graphs/pittsburgh-jazz/`, `graphs/band-x/`, `graphs/bowie-covers/` folders — Track F.
- Do **not** implement `/cards` — Track G.
- Do **not** add tag-based filtering, search inside graph view, or in-browser editing.
- Do **not** add dark mode, animations, mobile-responsive breakpoints.
- Do **not** modify `lib/cards.py`, `lib/graph.py`, or `lib/spotify.py`. If you discover a gap in any of these, STOP and write a HANDOFF note describing the gap. Sprint Manager will spawn a fix session.

## Handoff protocol

```
HANDOFF:
- Routes implemented: <list>; still stubbed: /cards (Track G).
- Fixture graph: graphs/pittsburgh-jazz-fixture/ (<N> cards, <M> edges).
- Vis-network config: <one-line summary, e.g., "physics enabled, hierarchical disabled, groups configured per spec">.
- Spotify embed wiring: <e.g., "spotify_embed_url() called in /api/card endpoint">.
- Integration check results (curl outputs): <inline or pointer into test_results file>.
- /tmp/test_results_<task_id>.txt: <path>, FAIL=<count>.
- Integration gotchas for Tracks F/G: <e.g., "card slugs must NOT collide across types — alice-person vs alice-album would both be 'alice'; spec assumes <type>-<slug> filenames keep them disjoint">.
- Deviations: <none / list>.
```

## Close-out

Commit on `sprint/graph-view` with subject `feat: graph view UI + API routes + fixture graph`. Brief summary noting whether the integration check passed cleanly.

---

HANDOFF:
- Routes implemented: GET / (home, real list_graphs data), GET /graph/<slug>, GET /api/graph/<slug>, GET /api/card/<graph_slug>/<card_slug>, GET /graph/<slug>/card/<card_slug>. Still stubbed: /cards (Track G).
- Fixture graph: graphs/pittsburgh-jazz-fixture/ (5 cards: location-pittsburgh, person-stanley-turrentine, person-earl-hines, album-sugar, track-sugar-track; 5 edges after undirected dedup).
- Vis-network config: physics enabled (forceAtlas2Based, springLength=120), hierarchical disabled, groups configured per spec (person/group/album/track/song/location/genre/note/memory) by shape+color. Initial load focuses first node and auto-fetches its card.
- Spotify embed wiring: spotify_embed_url() called inside /api/card route (and in card_view server-render path) on frontmatter.spotify_url. lib/cards.py left untouched. Payload also exposes spotify_kind so the template/JS can pick a 152px (track) vs 352px (album/playlist/show) iframe height.
- Integration check results (server run on alt port 8767 because 8766 was occupied by another track's app): /api/graph/<fixture> returns nodes+edges JSON; /api/card/<fixture>/sugar returns spotify_embed_url = https://open.spotify.com/embed/album/3hARuIUZqAIAKSuNvW5dGh; /graph/<fixture> returns 200; /api/graph/does-not-exist returns 404. Full curl outputs appended to /tmp/test_results_track-E.txt.
- /tmp/test_results_track-E.txt: /tmp/test_results_track-E.txt, FAIL=0 (50 passed).
- Integration gotchas for Tracks F/G:
  - Card slugs must NOT collide across types in the same folder — slug derivation strips only the leading "<type>-" prefix, so "album-sugar.md" and "track-sugar.md" both yield slug "sugar" and would clash in /api/card/<slug>/<card_slug>. The fixture works around this by using "track-sugar-track.md". Track F should plan filenames accordingly (e.g., "track-sugar-cti.md" vs "album-sugar.md").
  - The home page calls list_graphs(GRAPHS_ROOT). Track F's authored graphs will appear automatically once their README.md frontmatter is in place. The old hard-coded STUB_GRAPHS list has been removed.
  - The /cards 501 stub was deliberately preserved per spec.
- Deviations: None from the spec. Added a tests/_card_panel.html partial shared between card.html and the JS panel for consistency (server-render path + JS render path produce the same DOM shape). Updated tests/test_app.py — the original test_stub_routes_return_501 assertions were stale once the routes were implemented; replaced with a /cards-only stub assertion and home smoke.
