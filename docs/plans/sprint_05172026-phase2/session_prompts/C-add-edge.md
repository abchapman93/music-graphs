# Track C — `add-edge` skill

**Sprint:** `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/`
**Branch:** `sprint/add-edge`
**Worktree path (PM pre-creates):** `/private/tmp/mg-wt-C`
**Wave:** 2
**Dependencies:** Track B (`add-node`) merged to main — same lint-and-revert pattern; same `tools/lint_graphs.py` invocation.

## How to work on this branch

PM has pre-created the worktree off the latest `main` (after Track B merge). You do NOT call `EnterWorktree`. Use `git -C /private/tmp/mg-wt-C <git-op>`.

## Goal

Create `.claude/skills/add-edge/` — adds a `[[type:slug]]` wikilink between two existing cards in the same graph by editing the appropriate card body. Handles symmetric relationships (member-of / has-member) by writing to both sides when appropriate.

## Context files to read

- `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/project_spec.md` — sections on skills + locked rules.
- `/Users/alecchapman/Code/music-graphs/lib/cards.py` — wikilink format (`[[type:slug]]` and `[[type:slug|Display]]`) and `extract_wikilinks()` extraction logic.
- `/Users/alecchapman/Code/music-graphs/.claude/skills/add-node/SKILL.md` (from Track B) — reuse its lint-gate and rollback pattern.
- Existing cards with edges as templates: `/Users/alecchapman/Code/music-graphs/graphs/band-x/cards/group-x.md` (group → members) and `.../person-dave-alvin.md` (person → group).

## Definition of done

- [ ] `.claude/skills/add-edge/SKILL.md` documents:
  - **Inputs:** graph slug, source card slug, target card slug (with type prefixes inferred from filenames), optional relationship label ("member of", "appears on", "covers", etc.), optional `symmetric: bool`.
  - **Behavior:** edits the source card body to insert a `[[type:slug|Display]]` wikilink in a natural-sounding sentence. If `symmetric=True`, also edits the target card to add the reciprocal link.
  - **Output:** modified card file(s); confirmation message listing each file changed.
- [ ] **Sentence insertion policy.** The skill appends to the card body — never replaces existing content. If the body ends with a paragraph, the new sentence is appended to that paragraph (or to a new paragraph if the relationship label is best stated standalone). Phrasing comes from the relationship label, e.g., "Dave Alvin appears on [[album:ashgrove|Ashgrove]]."
- [ ] **Dangling-link detection.** Before writing, the skill checks that the target slug exists in `graphs/<slug>/cards/<type>-*.md`. If not found, warns the user and asks: (a) create the target via `add-node` first, (b) write the wikilink anyway as a forward reference, (c) cancel. Default to (a).
- [ ] **Lint gate** matches Track B: run `tools/lint_graphs.py <graph>`; revert on failure; report the lint error.
- [ ] **Duplicate detection.** If the exact wikilink `[[type:target-slug]]` already appears in the source card's body, the skill reports "edge already exists" and exits without writing.
- [ ] Helper at `.claude/skills/add-edge/scripts/add_edge.py`; pytest at `tests/test_add_edge.py` covers: happy path (one-way), symmetric edge (both files updated), dangling target (warn + default behavior), duplicate detection, lint-failure rollback.

## Not in scope

- Do NOT create new cards. If the target doesn't exist, defer to `add-node`.
- Do NOT modify frontmatter — wikilinks live in card *body* for this skill. (Frontmatter wikilinks are a separate concern handled by `add-node` at create time.)
- Do NOT touch `lib/cards.py` or `tools/lint_graphs.py`.

## Test protocol

```bash
cd /private/tmp/mg-wt-C
.venv/bin/pytest tests/test_add_edge.py -v 2>&1 | tee /tmp/test_results_track-c.txt
```
Confirm FAIL=0. Log path in HANDOFF.

## Handoff protocol

Append HANDOFF block:
```
HANDOFF (Track C):
- SKILL.md path: <absolute>
- Helper signature: add_edge(graph, src_slug, tgt_slug, relationship=None, symmetric=False) -> list[Path]
- Default behavior on dangling target: <a/b/c>
- /tmp/test_results_track-c.txt: FAIL=<count>
- Integration gotchas for Track D (expand-graph): <e.g., "add-edge does not create nodes; expand-graph must sequence add-node calls first">
- Deviations: <none / list>
```

## Close-out

```
git -C /private/tmp/mg-wt-C add .
git -C /private/tmp/mg-wt-C commit -m "feat(skills): add-edge wikilink writer with dangling detection"
```
Report SHA + HANDOFF to PM.
