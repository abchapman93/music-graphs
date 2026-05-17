---
name: expand-graph
description: Given a music-graphs graph slug and an expansion criterion (e.g., "find more Bowie covers", "find one album per Pittsburgh-jazz artist"), search the web and Spotify MCP for 5–10 candidate node additions, present them to the user for approval, and call `add-node` + `add-edge` on the accepted candidates. Album-first by default; never writes card files directly. Triggers include "expand [graph]", "find more [X] for [graph]", "grow the [graph] graph", and any request to add multiple related nodes at once.
triggers:
  - "expand [graph]"
  - "expand graph [graph]"
  - "find more [X] for [graph]"
  - "grow the [graph] graph"
  - "add more [X] to [graph]"
  - "find candidates for [graph]"
---

# Skill: expand-graph

Orchestrator skill: searches for candidate nodes to add to an existing graph, surfaces them for user approval (5–10 per pass, hard ceiling 10), and routes accepted candidates through `add-node` and `add-edge`. This skill is the **only sanctioned multi-node expansion workflow** in the music-graphs repo.

## Locked rules (from project_spec.md)

- **No direct card writes.** Every new node goes through `add-node`; every wikilink through `add-edge`. The helper module never touches a card file. This is architectural — do not work around it.
- **No embedded Spotify search.** All Spotify URL verification goes through `retrieve-spotify-song`.
- **Candidate ceiling 5–10 per pass.** Never present more than 10 in one batch. If more candidates exist, surface the first batch and offer to continue after approval.
- **Album-only default.** Propose album cards by default. Track cards only when there's a narrative reason (e.g., a cross-artist appearance worth surfacing).
- **Scope respect.** Read the graph's `README.md` and any `note-*.md` scope cards before searching. State the inclusion criterion back to the user before generating candidates.

## Inputs

| Input | Required | Notes |
|---|---|---|
| `graph` | yes | Graph slug under `graphs/`. |
| `criterion` | yes | Free-text expansion goal, e.g. `"find more Bowie covers from outside rock"`. |
| `ceiling` | no | Max candidates to present in one pass. Default 5; capped at 10. |
| `dry_run` | no | If true, generate + present candidates only. Do not call `add-node` / `add-edge`. Defaults to false. |

## Workflow

1. **Read the graph's scope.**
   - Open `graphs/<graph>/README.md` for the description.
   - Enumerate existing card files: `graphs/<graph>/cards/*.md`. These are the "already-in-the-graph" anchors used both as scope context and as wikilink targets.
   - If a `note-*.md` card exists (e.g., `note-bowie-songbook.md`), read it — Phase 1 uses these as inline scope statements.
2. **State the inclusion criterion** back to the user, derived from the README + scope notes + the supplied `criterion`. Wait for confirmation or correction before searching.
3. **Generate candidates.** Use web search (`WebSearch` / `WebFetch`) and/or the Spotify MCP search tool to assemble a pool of candidates that fit the scope. Default node type is **album**; only propose `track` when the criterion explicitly motivates a single song (e.g., "Sean Jones plays on Sweet Lover No More").
4. **For each candidate, verify Spotify.** Invoke `retrieve-spotify-song` (passing `auto_pick=true` for the orchestrated case where exactly one MCP result returns). If the skill returns `NOT_FOUND` / `MCP_ERROR` / `MCP_UNAVAILABLE`, either drop the candidate or carry it forward with `spotify_url=None` and a documented reason (e.g., `"MCP search exhausted"`). Per spec, every candidate surfaced to the user must have either a verified URL or a stated reason it lacks one.
5. **Propose wikilinks.** For each candidate, examine the existing card slugs in the graph and suggest 1–3 `type:slug` wikilinks that connect the new node to the existing graph (e.g., a new Bowie cover album → `[[person:david-bowie]]` and the relevant `[[song:...]]`).
6. **Present a numbered candidate list** (≤ `ceiling`, hard max 10). Each row shows: name, type, proposed wikilinks, Spotify URL (or the explicit `null + reason`), and a one-sentence rationale tied to the scope.
7. **Wait for user approval.** Accept a subset (numbers), `none`, `all`, or `more` (next batch — restart at step 3 with already-presented candidates excluded).
8. **For each approved candidate** (skipped entirely if `dry_run=True`):
   - Call `add-node` with `graph`, `type`, `name`, `spotify_url`, optional `canonical_link`, and the proposed wikilinks.
   - For each proposed wikilink that targets an **existing** card, call `add-edge` to add a reciprocal link from that target back to the new card (so the graph is bidirectional where natural).
9. **Run lint and report.** After all writes, run `.venv/bin/python tools/lint_graphs.py graphs` and surface the result. Summarize which cards were created, which edges were added, and any candidates that were rejected or deferred.

## Candidate ceiling enforcement

Enforced in `scripts/expand_graph.py` inside `generate_candidates(..., ceiling=...)`:

- The `ceiling` argument is clamped to the range `[1, 10]`.
- The returned candidate list is truncated to `ceiling` items before returning.

The skill **never** surfaces more than 10 candidates in a single pass. If the search produced more, the helper returns the first batch and exposes an `overflow` count so the caller can offer a "more" follow-up after approval.

## Dry-run mode

Pass `dry_run=True` to `run_expand_graph()` (helper) to:

- Generate and return the candidate list.
- Skip every `add-node` / `add-edge` call.
- Skip the final lint pass.

This is the test surface — the pytest at `tests/test_expand_graph.py` covers dry-run candidate generation against a mocked search function. In a real session, `dry_run=True` is also useful as a "preview my candidates without committing" step.

## Helper module

`scripts/expand_graph.py` exposes:

```python
generate_candidates(
    graph: str,
    criterion: str,
    *,
    graphs_root: Path | None = None,
    ceiling: int = 5,
    search_fn: Callable[[str, str, list[str]], list[Candidate]] | None = None,
) -> tuple[list[Candidate], int]   # (candidates_truncated_to_ceiling, overflow_count)

run_expand_graph(
    graph: str,
    criterion: str,
    *,
    graphs_root: Path | None = None,
    ceiling: int = 5,
    dry_run: bool = False,
    search_fn: Callable[..., list[Candidate]] | None = None,
    approved_indices: Sequence[int] | None = None,   # which candidates the user said yes to
    add_node_fn: Callable | None = None,             # injected for tests; default wires to add-node skill helper
    add_edge_fn: Callable | None = None,             # injected for tests; default wires to add-edge skill helper
) -> ExpansionResult
```

`Candidate` is a dataclass: `name`, `type` (default `"album"`), `wikilinks: list[str]`, `spotify_url: str | None`, `spotify_reason: str | None`, `rationale: str`.

`ExpansionResult` collects: `criterion`, `candidates` (presented), `overflow`, `created_paths`, `edge_paths`, `skipped` (with reasons), `lint_returncode`.

The `search_fn` injection is the seam tests use to avoid network. In a real session, callers either pass a closure that wraps `WebSearch` / MCP calls, or do the search themselves and pass a precomputed list as the `search_fn` return value.

## How Claude should invoke this skill

1. Confirm graph + criterion with the user. State the derived inclusion criterion back to them.
2. Drive `generate_candidates()` (passing a search function that calls `WebSearch` and `mcp__68e7e171-8619-450d-bfc7-458af6964130__search` for each candidate it finds).
3. Present the numbered candidate list. Wait for approval.
4. For each approved candidate, call `add-node` (and `add-edge` for proposed wikilinks).
5. Run lint and report.

## Integration notes

- **`retrieve-spotify-song`:** invoked once per candidate. With more than one MCP result, that skill blocks for user choice — the orchestrator must allow that interactive step inside the loop.
- **`add-node`:** lint-and-revert on failure. If `add-node` raises `LintError` on a candidate, `expand-graph` records it in `ExpansionResult.skipped` and continues with the remaining candidates.
- **`add-edge`:** the wikilinks passed to `add-node` are written into the new card's body at creation time. `add-edge` is used to add reciprocal edges from existing cards back to the new node — the orchestrator decides per-relationship whether a reciprocal edge is natural.
- **Track H (bowie-covers dogfood)** is the acceptance test for this skill. If the ergonomics force Alec to paste YAML, the skill failed.

## Out of scope

- No new card types (album/track/person/group/note/etc. — Phase 1's loose type set).
- No template engine for body prose. The skill assembles a short rationale-derived body sentence and lets `add-node` handle the rest.
- No persistent state between passes. Each invocation re-reads the graph.
- No automatic edits to `lib/cards.py`, `app.py`, or `tools/lint_graphs.py`.
