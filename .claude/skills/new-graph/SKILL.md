---
name: new-graph
description: Scaffold a new music-graphs graph from a theme. Creates the folder + README with declared Wikipedia/Spotify resources, writes seed person/group cards with verified Spotify URLs (via retrieve-spotify-song), runs lint, then offers to chain into expand-graph and graph-to-playlist. Triggered by "new graph", "create a new graph", "start a graph about [X]", "scaffold a graph for [X]", "add a graph".
triggers:
  - "new graph"
  - "create a new graph"
  - "scaffold a graph"
  - "start a graph"
  - "start a graph about"
  - "add a graph"
  - "make a graph for"
---

# `new-graph` — scaffold a new music-graphs graph

This skill is the sanctioned path for **creating a brand-new graph folder** under `graphs/`. It produces a lint-clean scaffold (README + seed cards) that other skills (`add-node`, `add-edge`, `expand-graph`, `graph-to-playlist`) can build on.

## Locked rules

- **No direct card writes.** Every seed card goes through `add-node` (or its `write_card` helper). The orchestrator never writes a card file directly.
- **No Spotify guessing.** Every seed card's `spotify_url` comes from `retrieve-spotify-song`. If a lookup returns `NOT_FOUND` or errors, omit the field — never fabricate IDs.
- **Resources are declarative, not scraped here.** The README's `resources:` block lists Wikipedia category/page URLs that `expand-graph` will probe later. This skill does not fetch them.
- **Seeds only.** This skill writes the graph's *anchor nodes* (typically 1 group + N members, or 1 person + N collaborators). Album/track expansion is `expand-graph`'s job.

## Inputs

| Input | Required | Notes |
|---|---|---|
| `theme` | yes | Free-text description of the graph's scope, e.g. `"One Direction members and their solo acts"` or `"Pittsburgh-born jazz musicians"`. |
| `slug` | no | Graph folder slug (kebab-case). If omitted, propose one derived from the theme and confirm. |
| `seed_nodes` | no | Inline list of `{name, type}` pairs to bootstrap. If omitted, propose a seed set from the theme and confirm via `AskUserQuestion`. |
| `resources` | no | Inline list of Wikipedia URLs (typed as `wikipedia-category`, `wikipedia-page`, `spotify-playlist`, or `website`) to declare on the README. If omitted, propose 1–5 based on the seed nodes and confirm. |

## Workflow

### Phase 1 — Confirm scope (orchestrator)

1. **Restate the theme** back to the user in one sentence.
2. **Propose a slug** (kebab-case, ≤30 chars). Confirm or accept user override.
3. **Check for collision** — abort if `graphs/<slug>/` already exists.
4. **Propose seed nodes.** For most graphs this is 1 anchor (group or person) plus 3–8 closely related nodes (members, frequent collaborators, etc.). Present as a numbered list and gate on approval via `AskUserQuestion`.
5. **Propose `resources:`** — typically the Wikipedia main article for the anchor + the most relevant `*_discography` pages or a `Category:*` URL. Confirm.

In auto mode with a clear theme, the orchestrator may skip explicit confirmation and proceed to Phase 2, summarizing decisions in one user-facing sentence.

### Phase 2 — Verify Spotify URLs (orchestrator)

For each seed node of type `person` or `group`:

- Call `retrieve-spotify-song` with `auto_pick=true` and a query of `"<name> artist"`.
- Capture the returned `spotify_url`, or record `null` + the literal failure tag (`NOT_FOUND`, `MCP_UNAVAILABLE`, `MCP_ERROR`).

Seed nodes of other types (`album`, `track`, `location`) follow the same pattern with their appropriate query shape, but the default seed set should be people/groups — album/track seeding is unusual.

### Phase 3 — Write the scaffold (orchestrator)

1. **Create the folder**: `graphs/<slug>/` and `graphs/<slug>/cards/`.
2. **Write the README** at `graphs/<slug>/README.md` with YAML frontmatter:

   ```yaml
   ---
   name: "<Display Name>"
   description: "<1–2 sentence scope statement>"
   resources:
     - type: wikipedia-page
       url: https://en.wikipedia.org/wiki/...
       label: "..."
   ---

   <1-paragraph body explaining the graph's scope, inclusion criteria, and any
   notable exclusions. This mirrors the README body convention used by the
   existing brad-mehldau-covers and pittsburgh-jazz graphs.>
   ```

   Do **not** set `spotify_playlist_url` here — that's `graph-to-playlist`'s job.

3. **Write each seed card** via `add-node`'s `write_card` helper (from `.claude/skills/add-node/scripts/write_card.py`). Pass:
   - `graph=<slug>`, `type`, `name`
   - `spotify_url=<from Phase 2 or None>`
   - `canonical_link=<Wikipedia URL>`
   - `body=<1–2 sentence bio mentioning the anchor>`
   - `wikilinks=[...]` — for member cards, include the anchor group/person's slug
   - `repo_root=<repo root>` (explicit, to skip the inference fallback)
   - `run_lint=False` — batch the lint at the end

4. **Add reciprocal edges** via `add-edge`'s `add_edge` helper. For each member → anchor wikilink written by Phase 3.3, add the reverse anchor → member edge. Use a `relationship` like `"includes"` or `"collaborated with"` when natural; omit for generic `Related: ...` sentences.

5. **Run lint** once via `tools/lint_graphs.py graphs`. On failure, surface the error and stop — do not silently delete the scaffold.

### Phase 4 — Offer follow-ups (orchestrator)

After the scaffold passes lint, prompt the user with the two natural next steps:

- **Expand the graph.** Suggest invoking `/expand-graph <slug>` with a one-line proposed criterion (e.g. `"pull all solo studio albums for each member"`). The user can accept, modify, or skip.
- **Generate a playlist.** Note that this only makes sense once track or album cards exist with verified `spotify_url`s. Usually deferred until after `expand-graph`.

The orchestrator does **not** auto-chain these — the user explicitly opts in.

## Output

A new directory `graphs/<slug>/` containing:

- `README.md` (with `name`, `description`, `resources:`)
- `cards/<type>-<slug>.md` for each seed node
- Bidirectional wikilinks between the anchor and each member
- Lint-clean per `tools/lint_graphs.py`

Plus a short report summarizing:

- Slug, anchor, seed-node count
- Which seeds got verified Spotify URLs vs which were NOT_FOUND
- Suggested next commands (`/expand-graph`, `/graph-to-playlist`)

## Common patterns

| Theme shape | Anchor | Typical seeds |
|---|---|---|
| Band + solo acts | the group | each band member as `person` |
| Composer + interpreters | the composer (`person`) | notable performers as `person` |
| Regional scene | a `location` card | 3–8 key figures from the scene |
| Songbook / covers | the originator (`person` or `group`) | each principal coverer as `person` |

## Out of scope

- Album/track expansion (use `expand-graph`).
- Playlist creation (use `graph-to-playlist`).
- Edits to existing graphs — this skill aborts on slug collision rather than overwriting.
- Automatic git commits — the user commits when they're ready.
- New card types or schema changes.

## How Claude should invoke this skill

When the user says "create a new graph", "start a graph about [X]", "add a graph for [X]", or similar:

1. Restate theme, propose slug + seed nodes + resources, gate on approval (or proceed in auto mode with a single summary sentence).
2. Run Phase 2 (Spotify lookups) in parallel where possible.
3. Run Phase 3 (scaffold write + edges + lint) in one orchestrator pass.
4. Report what was created and suggest `/expand-graph <slug>` as the natural next step.
