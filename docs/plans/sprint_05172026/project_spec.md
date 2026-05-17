# Sprint Spec — music-graphs Phase 1 MVP (sprint_05172026)

## Background

- **Goal:** Ship a working local Phase 1 MVP of the music-graphs app: Flask server + three hand-authored graphs (Pittsburgh jazz, Band X, Bowie covers) rendered as vis-network graphs with click-to-load card panels and embedded Spotify players.
- **Audience:** Alec's Dad. Gift use case. Browses on a laptop, no login, no instruction.
- **Demo plan:** Date TBD (no hard deadline — gift). Demo = Alec opens `http://127.0.0.1:8766/` in front of Dad, Dad clicks through all three graphs, every node and Spotify embed works.

## Description

A Python/Flask app served locally on port 8766. The user lands on a home page listing three "graphs" (curated knowledge libraries about a musical topic). Clicking into a graph shows a vis-network rendering of the graph on the left (~60%) and a card detail panel on the right (~40%). Clicking any node loads that card's markdown content; Track and Album cards include an embedded Spotify iframe. Wikilinks `[[type:slug]]` inside card bodies focus/zoom to the target node and load its card. A `/cards` page provides a flat searchable index.

Three modules sit under `lib/`:
- `cards.py` — parses markdown card files (YAML frontmatter + body + wikilinks).
- `graph.py` — builds vis-network `{nodes, edges}` JSON from a graph folder.
- `spotify.py` — converts Spotify URLs into embed iframe URLs.

Templates and static assets mirror the patterns in `/Users/alecchapman/Code/Claude Setup/tools/wiki_viewer.html` and `wiki_viewer_core.py`. Card content (~45 markdown files across the 3 graphs) is hand-authored by Alec with biography drafts delegated to Sonnet subagents.

## Architecture decisions

These are locked. Session agents must NOT re-litigate them.

- **Framework:** Python 3.11+, Flask. Single `app.py` with route handlers. No blueprint split in Phase 1.
- **Port:** `127.0.0.1:8766` (dashboard uses 8765 — must coexist).
- **Graph model:** One folder per graph at `graphs/<slug>/cards/*.md`. Edges are inferred from `[[type:slug]]` wikilinks between cards **in the same folder**. No cross-graph edges. No tag-based filtering.
- **Card schema:** YAML frontmatter (see "Card schema" below) + markdown body. One card type per file.
- **Wikilink syntax:** `[[type:slug]]` or `[[type:slug|Display Text]]`.
- **Vis-network:** Reuse from `wiki_viewer.html`. Node styling: Person=circle/blue, Group=square/blue, Album=square/green, Track=triangle/green, Song=triangle/light-green, Location=diamond/orange, Genre=hexagon/purple, Note=star/yellow, Memory=star/red.
- **Spotify:** Embed iframe only. No OAuth, no playlist creation, no API calls.
- **Markdown rendering:** `python-markdown` library, server-side rendering. Wikilinks rewritten to anchor tags during render.
- **Image policy:** Frontmatter `image:` may be a Wikipedia URL (hotlinked) or a relative path under `graphs/<slug>/images/`. Both must resolve; downloaded images are committed to the repo.
- **No auth, no DB.** Filesystem is the database.
- **JS:** Vanilla JS, no build step. Inline `<script>` plus `static/js/graph.js`.
- **CSS:** One hand-written `static/css/style.css`. No framework (no Tailwind, no Bootstrap).
- **Explicit rejections:**
  - **No React / Vue / SPA frameworks.** Server-rendered + small vanilla JS.
  - **No tag-based graph filtering.** (Phase 3.)
  - **No in-browser editing.** Markdown editing happens in Alec's text editor.
  - **No Spotify OAuth.** Embedded player only.
  - **No CSV export of playlists.** (Phase 2/3.)
  - **No tests beyond the units listed below.** No e2e/browser-driver tests in Phase 1.

## Card schema

YAML frontmatter required fields:
```yaml
type: person | group | album | song | track | location | genre | note | memory
name: "Display Name"
```

Optional fields (interpreted per type — schema stays loose in Phase 1):
```yaml
canonical_link: https://en.wikipedia.org/wiki/...
spotify_url: https://open.spotify.com/track/<id>     # person|album|track|playlist|artist
image: <https URL or relative path>
birth_date: 1934-04-05
birth_location: "[[location:pittsburgh]]"
primary_link: "[[type:slug]]"                        # note/memory cards
secondary_links: ["[[type:slug]]", "[[type:slug]]"]  # note/memory cards
```

Body is markdown. May contain `[[type:slug]]` or `[[type:slug|Display Text]]` wikilinks. Both frontmatter wikilinks and body wikilinks produce edges in the graph.

**File naming:** `graphs/<graph-slug>/cards/<type>-<card-slug>.md` (e.g., `cards/person-stanley-turrentine.md`). The filename's `<card-slug>` portion (everything after the first `-`) is the canonical slug used in wikilinks.

## Data contracts

- **Graph folder:** `graphs/<slug>/cards/*.md` — cards. `graphs/<slug>/README.md` — graph description + cover image path (for home page). Optional `graphs/<slug>/images/*` — downloaded images.
- **Parsed card** (output of `lib/cards.py:parse_card`):
  ```python
  {
    "type": str,            # from frontmatter
    "slug": str,            # from filename
    "name": str,            # from frontmatter
    "frontmatter": dict,    # full frontmatter as parsed YAML
    "body_html": str,       # rendered markdown with wikilinks rewritten to anchors
    "body_md": str,         # raw markdown body
    "wikilinks": [(str, str)],  # list of (type, slug) extracted from frontmatter + body
    "spotify_embed": str | None,  # embed URL if spotify_url present
  }
  ```
- **Graph JSON** (output of `lib/graph.py:build_graph`, served by `/api/graph/<slug>`):
  ```python
  {
    "nodes": [{"id": "<type>:<slug>", "label": str, "group": <type>, "title": str}, ...],
    "edges": [{"from": "<type>:<slug>", "to": "<type>:<slug>"}, ...],
  }
  ```
  Edges are de-duplicated; self-loops dropped. An edge appears only when **both** endpoints exist as cards in the same graph folder. Dangling wikilinks (target card not in folder) are logged but not rendered as edges.

## Module signatures

```python
# lib/cards.py
parse_card(path: Path) -> dict
  # See "Parsed card" schema above. Pure function. No I/O beyond reading the file.

extract_wikilinks(text: str) -> list[tuple[str, str]]
  # Returns [(type, slug), ...] from "[[type:slug]]" or "[[type:slug|Display]]" matches.

# lib/graph.py
build_graph(graph_dir: Path) -> dict
  # See "Graph JSON" schema above. Reads all cards/*.md in folder, returns nodes+edges.

list_graphs(graphs_root: Path) -> list[dict]
  # Returns [{"slug", "name", "description", "cover_image", "card_count"}, ...]
  # by reading graphs/<slug>/README.md frontmatter.

# lib/spotify.py
spotify_embed_url(url: str) -> str | None
  # Converts open.spotify.com/<kind>/<id> → open.spotify.com/embed/<kind>/<id>.
  # Returns None if the URL doesn't match a Spotify resource.
```

All three modules are pure-Python, no Flask imports. App-level wiring lives in `app.py`.

## Dependency graph

```
                 [P0: repo-init]                  ← Pre-sprint
                       ↓
   [A: skeleton-flask]  [B: card-parser]  [C: spotify-embed]   ← Wave 1 (parallel)
              ↓                ↓                      ↓
                         [D: graph-build]                       ← Wave 2 (waits for B)
                                ↓
                         [E: graph-view]                        ← Wave 3 (waits for A + D + C)
                                ↓
              [F: card-authoring]   [G: card-index]             ← Wave 4 (parallel after E)
                          ↓                ↓
                       [Alec: verification + demo]              ← Wave 5
```

Wave gates (artifacts that must exist before the next wave):

- **A → E:** `app.py` running on 8766; `templates/base.html`; `static/css/style.css`.
- **B → D:** `lib/cards.py:parse_card` returns the schema above; tests pass.
- **C → E:** `lib/spotify.py:spotify_embed_url` returns embed URLs; tests pass.
- **D → E:** `lib/graph.py:build_graph` returns `{nodes, edges}` schema above; tests pass on a fixture.
- **E → F/G:** `/graph/<slug>` renders one demo graph end-to-end (one Pittsburgh-jazz sample folder, ~5 cards seeded by track E for testing). Clicking a node loads its card. Spotify iframe renders. Wikilink clicks focus the target node.
- **F + G → demo:** All 3 graphs authored (10–20 cards each); `/cards` index renders all; verification checklist passes.

## Pre-sprint actions

These must complete before Wave 1 launches.

- [ ] **P0 / repo-init:** `git init` in `~/Code/music-graphs/`, write `.gitignore` (Python venv, `__pycache__`, `.DS_Store`), commit empty initial. Also commits `docs/plans/` content (this spec + prompts) as the initial sprint scaffolding.
- [ ] **Spec lock:** This file. ✅
- [ ] **Test fixture seed:** Track E (graph-view) prompt will require a tiny `graphs/pittsburgh-jazz-fixture/` folder with 5 cards for integration testing. Track F replaces/extends this once the view works.
- [ ] **Repo state verified:** Clean working tree on `main` before any session launches.

## Roles

- **Project management** *(Sprint Manager — this session)* — task tracking, prompt authorship, merges, demo-readiness gate.
- **Pre-sprint setup** *(Claude SWE session, branch `sprint/repo-init`)* — git init + .gitignore.
- **Skeleton Flask** *(Claude SWE session, branch `sprint/skeleton-flask`)* — Track A.
- **Card parser** *(Claude SWE session, branch `sprint/card-parser`)* — Track B.
- **Spotify embed** *(Claude SWE session, branch `sprint/spotify-embed`)* — Track C.
- **Graph build** *(Claude SWE session, branch `sprint/graph-build`)* — Track D.
- **Graph view** *(Claude SWE session, branch `sprint/graph-view`)* — Track E. The integration track — combines A, B, C, D.
- **Card authoring** *(Alec + Sonnet subagents, branch `sprint/card-authoring`)* — Track F. Alec drives; subagents draft biographies in parallel batches.
- **Card index** *(Claude SWE session, branch `sprint/card-index`)* — Track G.
- **Verification + demo** *(Alec)* — end-to-end clickthrough, Spotify playback, console-error check.

## Scope

### In scope (Phase 1 MVP)

- Flask app on `127.0.0.1:8766` with home, graph, card-detail, card-index, and JSON API routes.
- `lib/cards.py`, `lib/graph.py`, `lib/spotify.py` modules with unit tests.
- vis-network graph rendering with type-based node styling.
- Click-node-to-load-card side panel.
- Embedded Spotify player on cards with `spotify_url`.
- Three authored graphs (Pittsburgh jazz, Band X, Bowie covers), 10–20 cards each.
- `/cards` flat index with client-side type filter + text search.
- README with run instructions.
- Git history with logical commits per track.

### Out of scope

- Family sharing, hosting, deployment (Phase 2).
- Authentication, user accounts.
- In-browser editing of cards.
- Spotify OAuth, playlist creation, CSV export.
- Automated graph expansion / LLM-querying for cards (Phase 3).
- Tag-based graph filtering (Phase 3).
- Dark mode, animations, fancy polish.
- Browser-automation / e2e tests.
- Mobile-responsive layout (laptop only).

## Demo criteria

Observable actions Dad (or Alec, dry-run) must be able to perform:

- [ ] Open `http://127.0.0.1:8766/`; home page lists 3 graphs with covers + descriptions.
- [ ] Click "Pittsburgh Jazz" → graph view loads with all cards as nodes; obvious edges present (Stanley Turrentine → Pittsburgh; Earl Hines → Pittsburgh; at least one album → artist).
- [ ] Click a Person node → right panel shows name, image, biography, key frontmatter fields.
- [ ] Click an Album node with `spotify_url` → side panel shows working Spotify embed; pressing play actually plays.
- [ ] Click a `[[wikilink]]` in a card body → graph focuses/zooms to the target node and loads it.
- [ ] Navigate back to home, repeat for Band X and Bowie covers. Each works identically.
- [ ] Open `/cards` → all ~45 cards listed; type filter narrows the list; text search narrows further.
- [ ] No console errors at any step. No Flask tracebacks.

## Version / tagging

- Target tag: `v0.1-phase1-demo` on `main` after Wave 5 sign-off.

## Guidance

- **Reuse first.** `wiki_viewer.html`, `wiki_viewer_core.py`, `wiki_lib.py` are the closest reference implementations. Sessions should read them before designing equivalents.
- **Server-rendered HTML for navigability** (home, card detail page, cards index). **JSON API only for the graph view** (`/api/graph/<slug>`, `/api/card/...`) where vis-network needs structured data.
- **No premature abstraction.** Three Flask apps' worth of routes total. Don't add a route registry, plugin system, or class hierarchy. Functions in `app.py` calling into `lib/*` is the whole architecture.
- **Sonnet subagents for bios** (Track F): each subagent gets one person, fetches the Wikipedia page, returns a 150–300 word markdown body in the card schema. Alec reviews/edits before commit. Don't use Codex for this — biographies are nuanced and require fact-checking sensibility.

## Open questions

*(empty — pre-sprint gate green)*
