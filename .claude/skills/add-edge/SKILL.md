---
name: add-edge
description: Insert a `[[type:slug|Display]]` wikilink between two existing cards in the same graph by editing the source card body. Optionally writes the reciprocal link to the target card. Always runs the lint gate before reporting success; reverts the write on lint failure. Triggered by "add edge", "link [X] to [Y]", "connect [X] and [Y]", "add a relationship between [X] and [Y]".
triggers:
  - "add edge"
  - "add an edge"
  - "add edge between"
  - "link [X] to [Y]"
  - "connect [X] and [Y]"
  - "add a relationship between [X] and [Y]"
  - "wikilink [X] to [Y]"
---

# `add-edge` — connect two existing cards in a music-graphs graph

This skill is the **only sanctioned path for editing an existing card to add a wikilink**. It assumes both endpoints already exist as card files; if the target is missing, defer to `add-node` first.

## Inputs

| Input | Required | Notes |
|---|---|---|
| `graph` | yes | Graph slug, e.g. `band-x`, `bowie-covers`, `pittsburgh-jazz`. Must match an existing folder under `graphs/`. |
| `src_slug` | yes | Source card slug — the filename stem after the first hyphen (e.g. `dave-alvin` for `person-dave-alvin.md`). Card type is inferred from the matching filename. |
| `tgt_slug` | yes | Target card slug. Card type is inferred from the matching filename. |
| `relationship` | no | Phrase that joins the two endpoints in the inserted sentence (e.g. `"appears on"`, `"covers"`, `"member of"`). When omitted, a neutral `Related: ...` sentence is appended. |
| `symmetric` | no | If True, also writes the reciprocal wikilink into the target card. Default False. The caller picks a phrase that reads correctly in both directions; for asymmetric phrasings (e.g. "member of"), use two distinct one-way calls instead. |
| `on_dangling` | no | `"abort"` (default) or `"forward"`. Controls behavior when the target slug does not exist in the graph (see below). |

## Output

The modified card file (or both files, if `symmetric=True`). Returns a `list[Path]` of files changed and a confirmation message naming each.

## Behavior

1. **Resolve cards.** Look up `src_slug` and `tgt_slug` in `graphs/<graph>/cards/`. Card *types* are derived from the filename prefix (the part before the first hyphen).
2. **Dangling-link check.** If `tgt_slug` does not resolve to a file, the skill warns the user and asks how to proceed:
   - **(a, default)** Create the target via `add-node` first, then call `add-edge` again.
   - **(b)** Proceed and write a forward-reference wikilink anyway (`on_dangling="forward"`). The lint gate may still reject it.
   - **(c)** Cancel.
3. **Duplicate detection.** If the exact `[[<tgt-type>:<tgt-slug>]]` wikilink already appears anywhere in the source card body, the skill raises `DuplicateEdgeError`, reports "edge already exists", and exits without writing.
4. **Sentence insertion.** The skill appends a new sentence as a new paragraph at the end of the source card body — it never replaces existing content. Phrasing is driven by `relationship`:
   - With label: `"<src name> <relationship> [[<tgt-type>:<tgt-slug>|<tgt name>]]."`
   - Without label: `"Related: [[<tgt-type>:<tgt-slug>|<tgt name>]]."`
5. **Symmetric writes.** When `symmetric=True`, the same insertion logic runs on the target card with `src` and `tgt` reversed. If the target already contains the reciprocal link, the second write is skipped silently.
6. **Lint gate.** Runs `tools/lint_graphs.py <graphs_root>` (using `.venv/bin/python` if present; otherwise `sys.executable`). On non-zero exit, the original contents of *every* modified file are restored from in-memory snapshots and `LintError` is raised. The skill never reports success on a lint-dirty repo.

## Not in scope

- Creating new cards — use `add-node` for that.
- Editing frontmatter — wikilinks live in the card **body** for this skill. Frontmatter wikilinks are seeded by `add-node` at create time.
- Modifying `lib/cards.py` or `tools/lint_graphs.py` — locked Phase 1 surfaces.

## Helper module

The actual edit + lint invocation live in `scripts/add_edge.py`. Signature:

```python
add_edge(
    graph: str,
    src_slug: str,
    tgt_slug: str,
    *,
    repo_root: Path | None = None,
    graphs_root: Path | None = None,
    relationship: str | None = None,
    symmetric: bool = False,
    on_dangling: str = "abort",  # "abort" | "forward"
    run_lint: bool = True,
    lint_cmd: Sequence[str] | None = None,
) -> list[Path]
```

Raises:
- `CardNotFoundError` — source slug doesn't resolve to a file.
- `DanglingTargetError` — target missing and `on_dangling="abort"`.
- `DuplicateEdgeError` — exact wikilink already present in source body.
- `LintError` — lint failed after write; all modified files have been restored.

## How Claude should invoke this skill

1. Confirm `graph`, `src_slug`, `tgt_slug`, and (if any) `relationship`.
2. If the user describes a clearly symmetric relationship ("collaborator of", "bandmate"), pass `symmetric=True` with `relationship=None` (or a phrase that reads both ways).
3. Call `add_edge(...)` (e.g. via `python -c` or a small driver script).
4. Surface the list of modified files. On `DanglingTargetError`, default to (a): create the target via `add-node`, then retry. On `DuplicateEdgeError`, report "already linked" and stop. On `LintError`, show the lint output verbatim.

Example call from a shell:

```bash
.venv/bin/python -c "
from sys import path; path.insert(0, '.claude/skills/add-edge/scripts')
from add_edge import add_edge
paths = add_edge(
    graph='band-x',
    src_slug='dave-alvin',
    tgt_slug='ashgrove',
    relationship='appears on',
)
for p in paths:
    print(p)
"
```
