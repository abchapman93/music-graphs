---
name: expand-graph
description: Orchestrated, multi-phase graph expansion. Given a music-graphs graph slug, develop a plan (stopping rule, candidate sources, probe), delegate knowledge retrieval to a subagent, delegate Spotify linking to a subagent, then present candidates for approval and write cards via `add-node` + `add-edge`. Reads `resources:` declared on the graph root README to seed discovery (Wikipedia categories, Spotify playlists, etc.). Album-first by default; never writes card files directly. Triggers include "expand [graph]", "find more [X] for [graph]", "grow the [graph] graph", and any request to add multiple related nodes at once.
triggers:
  - "expand [graph]"
  - "expand graph [graph]"
  - "find more [X] for [graph]"
  - "grow the [graph] graph"
  - "add more [X] to [graph]"
  - "find candidates for [graph]"
  - "extend [graph] with [criterion]"
---

# Skill: expand-graph

A **four-phase orchestrator** for growing an existing graph. Replaces the prior one-shot candidate-generation flow with explicit Planning → Knowledge Retrieval → Spotify Linking → Card Creation phases. Phases 2 and 3 are delegated to subagents (`Agent` with `subagent_type: general-purpose`) so the orchestrator's context stays clean and each subagent has a narrow, single-purpose prompt.

## Locked rules

- **No direct card writes.** Every new node goes through `add-node`; every wikilink through `add-edge`. The orchestrator never touches a card file directly.
- **No embedded Spotify search.** All Spotify URL verification goes through `retrieve-spotify-song`. NOT_FOUND stays NOT_FOUND; no training-data fallbacks.
- **No HTML scraping of Wikipedia.** All Wikipedia category lookups go through `retrieve-wikipedia-category`.
- **Candidate ceiling 5–10 per approval batch.** Never present more than 10 in one batch to the user. If the planning yield exceeds 10, batch and offer "more" after each approval pass.
- **Album-only default.** Propose album cards by default. Track cards only when the criterion explicitly motivates a single song.
- **Resource-first scope.** If the graph root README declares `resources:`, those drive Phase 1 probing — don't fall back to model-knowledge candidate generation until the declared resources have been probed.

## Inputs

| Input | Required | Notes |
|---|---|---|
| `graph` | yes | Graph slug under `graphs/`. |
| `criterion` | yes | Free-text expansion goal — usually includes an implicit or explicit stopping rule. |
| `stopping_rule` | no | Inline rule, e.g. `"every artist has ≥1 linked track, target 10 new artists"`. If omitted, Phase 1 proposes one via `AskUserQuestion`. |
| `ceiling` | no | Max candidates per approval batch. Default 5; capped at 10. |
| `dry_run` | no | Skip the Spotify-linking and write phases; return after Phase 2. |

## Phase 1 — Planning (orchestrator, main session)

1. **Read the graph.** Open `graphs/<graph>/README.md` for `name`, `description`, `cover_image`, and `resources:`. Enumerate `graphs/<graph>/cards/*.md` for existing slugs and any `note-*.md` scope cards. Use the helpers in `scripts/expand_graph.py`:
   - `_read_scope(graphs_root, graph)` — existing helper.
   - `lib.resources.parse_resources(readme_path)` — new — returns typed `Resource` entries.

2. **Resolve the stopping rule.**
   - If the caller passed `stopping_rule` inline, parse it and confirm with one user-facing sentence ("Plan: keep adding artists until every artist has ≥1 linked track, target ~10 new artists. Continue?").
   - Otherwise, propose a rule based on graph state and ask via `AskUserQuestion` with 2–4 options (e.g. "target N new nodes" vs "coverage rule: every X has ≥1 Y" vs "saturate the Wikipedia category").

3. **Probe each declared resource.** For each `Resource` returned by `parse_resources`:
   - **`wikipedia-category`** → call `retrieve-wikipedia-category`. Take the first 200 members, compute approximate dedupe count against existing graph slugs (slugify each title; compare to `scope.existing_slugs`).
   - **`spotify-playlist`** → resolver not yet implemented; note "(playlist resolver deferred)" and skip.
   - **`website`** → no resolver; surface the URL to the model as free-text seed during Phase 2.
   - **No resources declared** → propose using the Spotify MCP free-text search (existing Phase-1 behavior) and confirm with the user.

   Report counts per resource: "Resource <label>: 247 members, ~219 net-new after dedupe." If projected net-new < target, propose a supplementary strategy (additional category, fallback Spotify search) and confirm.

4. **Output a plan dict** and present it to the user for explicit confirmation before continuing:

   ```python
   plan = {
       "graph": "pittsburgh-jazz",
       "stopping_rule": "every artist has ≥1 linked track, target ~10 new artists",
       "target_n": 10,
       "batch_size": 5,
       "sources": [
           {"type": "wikipedia-category",
            "url": "https://en.wikipedia.org/wiki/Category:Jazz_musicians_from_Pittsburgh",
            "estimated_net_new": 28},
       ],
       "existing_slugs": [...],
       "scope_summary": "Mid-20th-century jazz musicians from Pittsburgh ...",
   }
   ```

   Wait for the user to say "go" (or accept the proposed rule) before entering Phase 2.

## Phase 2 — Knowledge Retrieval (delegated subagent)

Invoke `Agent` with:

- `subagent_type: general-purpose`
- `description: "Music-graphs knowledge retrieval"`
- `prompt`: a **self-contained** brief built from the plan dict. Include:
  - The full plan dict (serialized JSON) so the subagent knows the stopping rule, target_n, batch_size, and existing slugs.
  - For each `wikipedia-category` source: paste the full member list (titles + URLs) from the Phase-1 probe. The subagent uses this as the seed list rather than the model's training data.
  - For each `website` source: paste the URL and a one-line note.
  - For "no resources" graphs: state the criterion and tell the subagent to use WebSearch + WebFetch.
  - **Output contract**: return JSON only, no card writes, no Spotify lookups. Schema:

    ```json
    {
      "candidates": [
        {
          "name": "Stanley Turrentine",
          "type": "person",
          "slug_hint": "stanley-turrentine",
          "bio": "1–2 sentence biographical note tied to the graph's scope.",
          "canonical_link": "https://en.wikipedia.org/wiki/Stanley_Turrentine",
          "source_refs": ["https://en.wikipedia.org/wiki/Category:Jazz_musicians_from_Pittsburgh", "..."],
          "suggested_wikilinks": ["place:pittsburgh", "album:..."]
        }
      ]
    }
    ```

  - The subagent **must not** invoke `add-node`, `add-edge`, or `retrieve-spotify-song`. Spotify linking is Phase 3.

The orchestrator validates the JSON shape, dedupes against `scope.existing_slugs` (slugify `slug_hint`), enforces the per-batch ceiling (5–10), and surfaces overflow as a "more" follow-up.

## Phase 3 — Spotify Linking (delegated subagent)

Invoke `Agent` with:

- `subagent_type: general-purpose`
- `description: "Music-graphs Spotify linking"`
- `prompt`: the candidate list from Phase 2 + the instruction to call `retrieve-spotify-song` (with `auto_pick=true`) for each candidate. The subagent's only job is to augment each candidate with one of:
  - `spotify_url: "https://open.spotify.com/<type>/<id>"` (verified via MCP), **or**
  - `spotify_url: null` + `spotify_reason: "NOT_FOUND ..." | "MCP_UNAVAILABLE ..." | "MCP_ERROR ..."` (preserving the literal fail-loud tags from `retrieve-spotify-song`).

The subagent returns the augmented candidate list as JSON. Fail-loud is preserved verbatim from `retrieve-spotify-song/SKILL.md` — NOT_FOUND stays NOT_FOUND, no training-data guesses.

If `dry_run=True`, skip this phase entirely and surface candidates with `spotify_url: null` + `spotify_reason: "dry-run skipped Spotify linking"`.

## Phase 4 — Card Creation (orchestrator)

1. **Present the candidate list** to the user (≤ `ceiling`). Each row shows:
   - Name, type
   - 1-sentence bio (truncated)
   - Spotify URL (or explicit "null — <reason>")
   - Proposed wikilinks
   - Source refs

   Accept: numbered subset / `all` / `none` / `more` (next batch — re-enter Phase 2 with new exclude list).

2. **For each approved candidate:**
   - Call `write_card` from [.claude/skills/add-node/scripts/write_card.py](../add-node/scripts/write_card.py) with `repo_root` explicitly set to the worktree root (avoids the `_infer_repo_root` fallback).
   - For each suggested wikilink that targets an **existing** card, call `add_edge` from [.claude/skills/add-edge/scripts/add_edge.py](../add-edge/scripts/add_edge.py) to add a reciprocal link from the target back to the new card. Forward links (new card → existing) are written by `add-node` via the `wikilinks=` parameter.

3. **Run lint** via `tools/lint_graphs.py graphs`. Report counts: cards created, edges added, candidates skipped (with reasons — especially Spotify-NOT_FOUND).

4. **Check stopping rule.** If the rule is unmet, offer "more" (returns to Phase 2 with the new slugs excluded).

## Helper module

`scripts/expand_graph.py` provides:

- `Candidate`, `ExpansionResult` (unchanged dataclasses).
- `_read_scope(graphs_root, graph)` (unchanged).
- `generate_candidates(...)` (existing — kept for back-compat tests; the new flow's per-phase logic lives in the orchestrator + subagents).
- **NEW** `build_plan(graph, *, repo_root, stopping_rule=None, target_n=None, batch_size=5, fetch_resource_fn=None) -> dict` — runs Phase 1 logic (scope read + resources parse + probe). The `fetch_resource_fn` seam is the test hook: pass a callable `(Resource) -> list[dict]` that returns canned member lists; default uses `retrieve-wikipedia-category`'s `fetch_category_members`.
- **NEW** `dedupe_against_existing(candidates: list[dict], existing_slugs: list[str]) -> list[dict]` — slug-hint-based dedupe used in Phase 2.
- **NEW** `enforce_ceiling(candidates: list[dict], ceiling: int) -> tuple[list[dict], int]` — clamps to the per-batch ceiling and returns overflow count, mirroring `generate_candidates`.

## How Claude should invoke this skill

When the user says "expand [graph]" (or similar):

1. **Confirm the graph and criterion.** State what you understand back to the user.
2. **Run Phase 1.** Read the graph, parse `resources:`, probe each, propose/confirm the stopping rule, present the plan dict, wait for "go".
3. **Run Phase 2 via Agent.** Build a self-contained prompt with the plan + probe results. Validate the returned JSON.
4. **Run Phase 3 via Agent.** Hand the candidate list to the Spotify-linking subagent. Validate the augmented list.
5. **Run Phase 4 in this session.** Present, gate on approval, call `add-node` + `add-edge`, lint, report. Loop back to Phase 2 if the stopping rule is not yet met and the user wants more.

## Out of scope

- No new card types beyond the loose Phase 1 set.
- No automated category-tree traversal — if a Wikipedia subcategory looks useful, the user adds it to `resources:` explicitly.
- No persistent state between full invocations. Each session re-reads the graph.
- No automatic edits to `lib/cards.py`, `app.py`, `tools/lint_graphs.py`, or `lib/resources.py`.
