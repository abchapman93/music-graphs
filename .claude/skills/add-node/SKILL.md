---
name: add-node
description: Create a new card file (person, group, album, track, location, note, memory, etc.) in a music-graphs graph with valid frontmatter, optional body, and optional wikilinks. Always runs the lint gate before reporting success; reverts the write on lint failure. Triggered by "add a card", "add node", "create a card for [X]", "add [X] to [graph]".
triggers:
  - "add a card"
  - "add node"
  - "add a node"
  - "create a card"
  - "create a card for"
  - "add [X] to [graph]"
  - "new card"
---

# `add-node` — create a card in a music-graphs graph

This skill is the **only sanctioned path for writing a card file** in this repo. Every other skill or agent that wants to add a node calls this skill (or the helper module it ships) and lets the lint gate decide whether the write sticks.

## Inputs

| Input | Required | Notes |
|---|---|---|
| `graph` | yes | Graph slug, e.g. `band-x`, `bowie-covers`, `pittsburgh-jazz`. Must match an existing folder under `graphs/`. |
| `type` | yes | Card type. Phase 1's loose set: `person`, `group`, `album`, `track`, `location`, `note`, `memory`, or any single lowercase word. |
| `name` | yes | Human-readable name (goes in `frontmatter["name"]` and slugifies into the filename). |
| `spotify_url` | no | Pre-validated Spotify URL. **This skill never calls the Spotify MCP.** To obtain a `spotify_url`, invoke the `retrieve-spotify-song` skill first and pass the result in. |
| `canonical_link` | no | Wikipedia URL (or similar). Recommended whenever available. |
| `body` | no | Markdown body paragraph(s). May embed wikilinks inline. If omitted, the body falls back to a single-sentence placeholder. |
| `wikilinks` | no | List of `type:slug` strings (or `(type, slug)` tuples) to append as a closing sentence to the body. |

## Output

A new file at `graphs/<graph>/cards/<type>-<filename-slug>.md` with:

- YAML frontmatter containing `type` and `name` (required), plus any of `canonical_link` and `spotify_url` that were supplied.
- A markdown body paragraph.
- Lint-clean per `tools/lint_graphs.py`.

The function returns the absolute `Path` of the new card.

## Slug derivation

- Filename: `<type>-<slug>.md` where `<slug>` is a lowercase-ASCII slugification of `name` (NFKD normalize, drop accents, collapse non-alphanumerics to hyphens).
- Card slug, as derived by `lib/cards.py:_derive_slug`, is the filename stem after the first hyphen — so the file `track-sugar.md` has slug `sugar`.
- **Collision check.** Before writing, the skill scans existing slugs in `graphs/<graph>/cards/` and, on collision, disambiguates the new slug by appending `-<type>` (e.g. `track-sugar-track.md` for a `track` named "Sugar" when an album already uses slug `sugar`). Further collisions get numeric suffixes (`-track-2`, `-track-3`, …). The skill warns the user when it disambiguates.

## Lint gate

After the file is written, the skill runs:

```
.venv/bin/python tools/lint_graphs.py graphs
```

(falling back to `sys.executable` if no `.venv` exists). If the exit code is non-zero, the new file is **deleted** and the lint stdout/stderr is surfaced to the user. The skill never reports success on a lint-dirty repo.

## No direct Spotify lookups

This skill does not call any Spotify MCP tool. If the user wants a verified Spotify URL on the new card, the assistant must invoke the `retrieve-spotify-song` skill first and pass the resulting URL into `add-node` as `spotify_url`.

## Body wikilinks

If `wikilinks` is supplied, the listed targets are appended to the body as a closing sentence like:

> Related: [[person:dave-alvin]], [[album:ashgrove]], and [[group:x]].

The skill **does not block** on wikilinks that point to slugs not yet present in the graph — the lint gate will catch any dangling links, and forward references (a card being written later in the same conversation) are a legitimate pattern. The skill warns when it detects a forward reference but lets the write proceed.

## Helper module

The actual file write + lint invocation live in `scripts/write_card.py`. Signature:

```python
write_card(
    graph: str,
    type: str,
    name: str,
    *,
    repo_root: Path | None = None,
    graphs_root: Path | None = None,
    spotify_url: str | None = None,
    canonical_link: str | None = None,
    body: str | None = None,
    wikilinks: Sequence | None = None,
    run_lint: bool = True,
    lint_cmd: Sequence[str] | None = None,
) -> Path
```

Raises `LintError` (with `.stdout`, `.stderr`, `.returncode`) when the lint gate trips; the new file is already removed before the exception is raised.

## How Claude should invoke this skill

When a user (or another skill) asks to add a node, Claude:

1. Confirm the **graph** (`band-x`, `bowie-covers`, `pittsburgh-jazz`) and the **type** + **name**.
2. If the user wants a Spotify URL on the card, invoke `retrieve-spotify-song` first and capture the returned URL.
3. Call `write_card(...)` (e.g. via `python -c` or a small driver script) with the assembled arguments.
4. Surface the new file path. On `LintError`, show the lint error verbatim and ask the user how to proceed.

Example call from a shell:

```bash
.venv/bin/python -c "
from sys import path; path.insert(0, '.claude/skills/add-node/scripts')
from write_card import write_card
p = write_card(
    graph='band-x',
    type='album',
    name='Ashgrove',
    canonical_link='https://en.wikipedia.org/wiki/Ashgrove_(album)',
    spotify_url='https://open.spotify.com/album/2At5ShihdUNDdc33Ztp7RX',
    body='Ashgrove is the 2004 album by [[person:dave-alvin]] ...',
    wikilinks=['person:dave-alvin'],
)
print(p)
"
```

## Smoke test

To verify the skill end-to-end without polluting a real graph:

1. Create a scratch graph: `mkdir -p graphs/_scratch/cards`.
2. Seed a minimal anchor card so lint can find at least one node: add a card by hand or copy one over.
3. Invoke `write_card(graph="_scratch", type="person", name="Test Person", body="Test.", wikilinks=["person:test-anchor"])`.
4. Confirm the new file at `graphs/_scratch/cards/person-test-person.md` exists.
5. Confirm lint exits 0.
6. Revert: `rm -rf graphs/_scratch`.

## Not in scope

- Adding edges between cards (that's the `add-edge` skill).
- Spotify lookups (that's `retrieve-spotify-song`).
- Modifying `lib/cards.py` or `tools/lint_graphs.py` — both are locked Phase 1 surfaces.
- New card type schemas — Phase 1's loose type set is the contract.
