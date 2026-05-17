# Implementation Plan — Personalized Music App (Phase 1 MVP)

## Context

Alec wants to build a personalized music app for his Dad's birthday combining two of his hobbies — music and graph theory. The app lets users curate music libraries grounded in real-world knowledge (places, people, songwriting relationships) rather than algorithmic recommendations.

**This plan covers Phase 1 only** (local, single-user, three hand-authored use cases). Phase 2 (family sharing) and Phase 3 (collaborative graph creation) are explicitly deferred — but the architecture below is chosen to make those transitions cheap.

No hard deadline, but the spirit of the gift is "something usable he can play with" — so we lock scope to ship a polished MVP rather than half-build Phase 2.

Source spec: [specs/Personalized music app.md](specs/Personalized music app.md)

---

## Decisions locked

| Question | Decision |
|---|---|
| Authoring model | Markdown files with YAML frontmatter (mirrors wiki pattern) |
| Graph model (Phase 1) | One folder per graph; edges inferred from `[[wikilinks]]` between cards in that folder. Tag-based filtering deferred to Phase 3. |
| Spotify integration | Embedded player (iframe widget) — no OAuth in Phase 1 |
| Tech stack | Python/Flask + vis-network (reuse dashboard + wiki_viewer patterns) |
| Project home | `~/Code/music-graphs/` (new top-level repo) |
| Hosting | Local only in Phase 1; structure repo so Phase 2 GitHub Pages / Cloudflare Pages migration is straightforward |

---

## Users

- **Primary user:** Alec's Dad. Browsing on a laptop in a relaxed setting. Will spend 20-60 minutes exploring on first sit. May come back occasionally.
- **Secondary user (Phase 1):** Alec, authoring cards and verifying graphs render correctly.
- **Out of scope for Phase 1:** Family members (Phase 2), public users (Phase 3).

Implication: navigation must be obvious without instruction. No login. No "getting started" hurdle. Dad opens a URL and immediately sees something interesting.

---

## Success criteria

Phase 1 ships when Dad can:

1. Open a local URL and land on a home page listing the three graphs.
2. Click into any of the three use cases and see:
   - The graph rendered (vis-network), with nodes color-coded by card type.
   - A side panel showing the markdown content of any clicked node.
   - An embedded Spotify player on any Track or Album card.
3. Click any wikilink in a knowledge card and navigate to that card.
4. See a flat list of all knowledge cards (wiki-style index) and search/filter by name.

Implicit: nothing crashes, embedded players actually play, all three graphs are fully authored.

---

## MVP behaviors (ordered by build priority)

### 1. Repo + card schema
- `~/Code/music-graphs/` initialized as git repo.
- `graphs/<slug>/cards/*.md` — one card per file. Slugs lowercase-hyphenated.
- YAML frontmatter schema (one card type per file):
  ```yaml
  ---
  type: person | group | album | song | track | location | genre | note | memory
  name: "Stanley Turrentine"
  canonical_link: https://en.wikipedia.org/wiki/Stanley_Turrentine
  spotify_url: https://open.spotify.com/...    # optional, for person/album/track
  image: <url or relative path>                # optional
  # Type-specific fields below — kept loose for Phase 1
  birth_date: 1934-04-05
  birth_location: "[[location:pittsburgh]]"    # wikilinks resolve to other cards
  ---
  Free-text biography in markdown. Can contain [[type:slug]] wikilinks.
  ```
- Card types follow the spec: Person, Group, Album, Song, Track, Location, Genre, Note, Memory.
- Note/Memory cards: `primary_link` + `secondary_links` arrays of `[[type:slug]]`.

### 2. Three authored graphs
- `graphs/pittsburgh-jazz/` — artists: Earl Hines, Errol Garner, Billy Strayhorn, Art Blakey, Stanley Turrentine, Paul Chambers, Ray Brown, Roger Humphries, Maureen Budway, Sean Jones; place: Pittsburgh; representative albums/tracks.
- `graphs/band-x/` — X + solo work: Exene Cervenka, John Doe, Billy Zoom, D.J. Bonebrake, Dave Alvin, Troy Gilkyson; key albums; Memory: X at Red Butte.
- `graphs/bowie-covers/` — David Bowie, Life on Mars and other songs, cross-genre covers (Seu Jorge, Bad Plus, etc.).
- Each graph: 10-20 cards. Hand-authored by Alec, with biography drafts delegated to Claude Sonnet subagents (via the Agent tool) that fetch from Wikipedia and return markdown card bodies for Alec to review/edit.

### 3. Flask app — server
- `app.py` — Flask app at `http://127.0.0.1:8766/` (different port from dashboard's 8765 to coexist).
- Routes:
  - `GET /` — Home page listing the three graphs (title, description, cover image, card count).
  - `GET /graph/<slug>` — Graph view page for one use case.
  - `GET /graph/<slug>/card/<card-slug>` — Single card page (markdown rendered).
  - `GET /api/graph/<slug>` — JSON: `{nodes: [...], edges: [...]}` for vis-network.
  - `GET /api/card/<graph-slug>/<card-slug>` — JSON: parsed frontmatter + rendered HTML body.
  - `GET /cards` — Flat wiki-style index across all graphs, with client-side search.

### 4. Markdown parsing layer
- Reuse pattern from `tools/wiki_lib.py`:
  - `parse_card(path) -> {frontmatter: dict, body_html: str, wikilinks: [(type, slug)]}`
  - `build_graph(graph_dir) -> {nodes, edges}` where nodes are cards and edges are wikilinks between cards in the same graph.
- Wikilink syntax: `[[type:slug]]` or `[[type:slug|Display Text]]`.
- Rendered cards turn wikilinks into `<a href="/graph/<current>/card/<slug>">` anchors.

### 5. Graph view UI
- Reuse vis-network setup from `tools/wiki_viewer.html` / `tools/wiki_viewer.py`.
- Layout: graph on the left (~60% width), card detail panel on the right (~40%).
- Node styling by type (color + shape): Person=circle/blue, Group=square/blue, Album=square/green, Track=triangle/green, Song=triangle/light-green, Location=diamond/orange, Genre=hexagon/purple, Note=star/yellow, Memory=star/red.
- Clicking a node loads its card into the right panel.
- Card panel: name (h1), image (if set), key frontmatter fields rendered as a definition list, biography/notes body, **embedded Spotify iframe** if `spotify_url` is set on the card.
- Wikilinks in the card body, when clicked, focus + zoom to that node in the graph and load its card.

### 6. Spotify embedded player
- Convert a Spotify URL (`https://open.spotify.com/track/<id>`) into the embed URL (`https://open.spotify.com/embed/track/<id>`).
- Render as `<iframe src="..." width="100%" height="152" frameborder="0" allow="encrypted-media"></iframe>`.
- Supports track/album/playlist/artist URLs. Helper function `spotify_embed_url(url)`.

### 7. Home page
- Lists the three graphs with a one-paragraph description (pulled from each graph's `graphs/<slug>/README.md`) and a cover image.
- Plus a link to the flat card index `/cards`.

### 8. Card index page
- Flat list of all cards across all graphs.
- Client-side filter (type + text search).
- Each row links to its graph view focused on that card.

---

## Out of scope for v1 (deferred)

| Item | Phase | Reason |
|---|---|---|
| Multi-user / family sharing | 2 | Phase 1 is a single-machine gift. Add hosting later. |
| In-browser card or note editing | 2 | Markdown editing in a text editor is fine for Alec; Dad doesn't need to edit. |
| Spotify OAuth + playlist creation | 3 | Spec lists `graph-to-playlist` as an action; defer until family is involved. Export to CSV available in Phase 1 if trivial. |
| Automated graph expansion (LLM querying) | 3 | Out of scope per spec. |
| Tag-based graph filtering | 3 | One-folder-per-graph is simpler for Phase 1. |
| Hosting (GitHub Pages / Cloudflare) | 2 | Local Flask is enough; structure routes/static paths so a static export is feasible later. |
| Image management beyond URLs / relative paths | 2 | Phase 1: paste Wikipedia URLs or drop into `graphs/<slug>/images/`. |
| Authentication, user accounts | 2-3 | N/A locally. |
| Dark mode, polish, fancy animations | Post-MVP | Functional first; polish if time allows. |

---

## Critical files to create

| File | Purpose | Pattern to reuse |
|---|---|---|
| `~/Code/music-graphs/app.py` | Flask app, routes, server-side rendering | `~/Code/Claude Setup/tools/dashboard_app.py` |
| `~/Code/music-graphs/lib/cards.py` | Parse markdown cards + wikilinks | `~/Code/Claude Setup/tools/wiki_lib.py` |
| `~/Code/music-graphs/lib/graph.py` | Build vis-network node/edge JSON from a graph folder | `~/Code/Claude Setup/tools/wiki_lib.py` (graph build logic) |
| `~/Code/music-graphs/lib/spotify.py` | URL → embed URL helper | New, ~20 lines |
| `~/Code/music-graphs/templates/base.html` | Layout, nav, styles | New |
| `~/Code/music-graphs/templates/home.html` | Graph listing | New |
| `~/Code/music-graphs/templates/graph.html` | vis-network + card panel | `~/Code/Claude Setup/tools/wiki_viewer.html` |
| `~/Code/music-graphs/templates/cards.html` | Flat card index | New |
| `~/Code/music-graphs/static/css/style.css` | Light styling | New |
| `~/Code/music-graphs/static/js/graph.js` | vis-network init, card panel loader | Adapted from `wiki_viewer.html` |
| `~/Code/music-graphs/graphs/pittsburgh-jazz/cards/*.md` | Hand-authored cards | New |
| `~/Code/music-graphs/graphs/band-x/cards/*.md` | Hand-authored cards | New |
| `~/Code/music-graphs/graphs/bowie-covers/cards/*.md` | Hand-authored cards | New |
| `~/Code/music-graphs/README.md` | Setup + run instructions | New |
| `~/Code/music-graphs/requirements.txt` | flask, markdown, pyyaml, frontmatter | New |

Total: ~10 code files + ~45 hand-authored card markdown files.

---

## Build sequence (suggested phases of execution)

1. **Skeleton (1 sitting)** — repo init, Flask app, one home route, base template, README. Verify `python app.py` serves a page.
2. **Card parsing (1 sitting)** — `lib/cards.py` parses one hand-authored test card with frontmatter + wikilinks. Unit-test wikilink extraction.
3. **Graph build + view (1-2 sittings)** — `lib/graph.py` produces vis-network JSON; graph.html renders one hand-authored graph with 5 cards. Click-to-load card panel works.
4. **Spotify embed (small)** — `lib/spotify.py` URL converter; iframe rendering in card panel.
5. **Card authoring (2-3 sittings)** — Write all 3 graphs' cards. Delegate biography drafting to Claude Sonnet subagents (Agent tool, parallel batches) — each subagent fetches a Wikipedia page and returns a markdown card body. Alec reviews/edits. Capture Spotify links by hand.
6. **Card index + polish (1 sitting)** — `/cards` page, search filter, basic styling pass.
7. **Verification** (see below).

---

## Verification

End-to-end checks before declaring Phase 1 done:

1. `cd ~/Code/music-graphs && python app.py` starts cleanly on port 8766.
2. Home page (`/`) lists three graphs with descriptions.
3. Each `/graph/<slug>` renders the graph with all expected nodes and at least the obvious edges (e.g., Stanley Turrentine → Pittsburgh; X → Exene Cervenka).
4. Clicking a node loads its card in the side panel with correct frontmatter and rendered biography.
5. At least one Track/Album card per graph has a working Spotify embedded player that actually plays a preview when clicked.
6. Clicking a `[[wikilink]]` inside a card body navigates to that node within the same graph view.
7. `/cards` lists every authored card; type filter and text search work.
8. No console errors in browser devtools. No tracebacks in Flask logs during normal navigation.
9. Repo is committed to git with a clean history; README explains how to run.

Optional stretch: deploy a read-only version to a local network IP so Dad can browse from the living room.

---

## Open questions

- **Image hosting:** Wikipedia hotlinks are fine for now, but they can rot or get rate-limited. Decide before authoring whether to download to `graphs/<slug>/images/` and commit. *Recommend: download key images, hotlink the rest.*
- **CSV export:** Spec mentions "Export to CSV" alongside Spotify playlists. Is this needed for the gift, or defer with playlist creation? *Recommend: defer.*
- **User notes in Phase 1:** Spec lists user notes as "nice to have" in Phase 1. Decide whether to support read-only Memory/Note cards (yes — already in MVP card schema) vs. in-browser note creation (no — Phase 2).
- **Biography drafting:** Delegate to Claude Sonnet subagents via the Agent tool (parallel batches of 3-5). Each subagent fetches a Wikipedia page via WebFetch and returns a markdown card body conforming to the schema. Alec reviews/edits before commit. Not Codex.
