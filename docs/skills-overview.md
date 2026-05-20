# music-graphs skills

A short catalog of the skills under `.claude/skills/` and how they
compose. See each skill's `SKILL.md` for the full contract.

## Foundation lookups (single-source-of-truth)

| Skill | What it does |
|---|---|
| `retrieve-spotify-song` | Spotify MCP search → canonical `open.spotify.com/<type>/<id>` URL. Fail-loud: never returns a training-data URL. |
| `retrieve-wikipedia-category` | MediaWiki API → list of `{title, url, pageid, ns}` for a `Category:` page on `en.wikipedia.org`. Paginated, fail-loud on HTTP/API errors. |

## Graph writes

| Skill | What it does |
|---|---|
| `add-node` | Write one card to `graphs/<graph>/cards/<type>-<slug>.md`. Lint-and-revert on failure. |
| `add-edge` | Add a wikilink sentence to an existing card. Duplicate detection + dangling-link guard. |

## Orchestrator

`expand-graph` is the only sanctioned multi-node expansion workflow. It runs four phases:

1. **Planning** — read the graph + `resources:` (see below), probe each resource, propose/confirm a stopping rule, present a plan dict.
2. **Knowledge Retrieval** — delegated subagent (`Agent`, `subagent_type: general-purpose`) returns candidate JSON: `{name, type, slug_hint, bio, canonical_link, source_refs, suggested_wikilinks}`.
3. **Spotify Linking** — delegated subagent calls `retrieve-spotify-song` per candidate; returns the list augmented with `spotify_url` or `spotify_url: null + spotify_reason`.
4. **Card Creation** — orchestrator presents the list, gates on user approval, calls `add-node` + `add-edge`, lints, reports.

## Declaring graph resources

A graph's root `graphs/<slug>/README.md` may declare external resources used by `expand-graph` in Phase 1:

```yaml
---
name: "Bowie Covers"
description: "..."
cover_image: "images/david-bowie.jpg"
resources:
  - type: wikipedia-category
    url: https://en.wikipedia.org/wiki/Category:Songs_written_by_David_Bowie
    label: "Bowie-written songs"
  - type: spotify-playlist             # resolver deferred
    url: https://open.spotify.com/playlist/...
  - type: website                      # no resolver; free-text seed
    url: https://example.com/scope-page
---
```

Recognized `type:` values are listed in `lib/resources.py::RESOLVERS`. Unknown types fail loud at parse time so typos surface immediately.

### Creating a new graph

1. `mkdir -p graphs/<slug>/cards`
2. Write `graphs/<slug>/README.md` with `name`, `description`, optional `cover_image`, and optional `resources:` (see above).
3. (Optional) Seed one or two anchor cards by hand or via `add-node`.
4. Run `expand-graph` — Phase 1 will probe your declared `resources:` and propose a candidate-discovery plan you can iterate on.
