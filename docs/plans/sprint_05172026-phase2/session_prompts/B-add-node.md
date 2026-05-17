# Track B — `add-node` skill

**Sprint:** `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/`
**Branch:** `sprint/add-node`
**Worktree path (PM pre-creates):** `/private/tmp/mg-wt-B`
**Wave:** 1 (parallel with A)
**Dependencies:** none for implementation (you can mock the spotify-song skill). At integration time the family agent and dogfood tracks will call `retrieve-spotify-song` from Track A first, then pass the resulting URL to this skill.

## How to work on this branch

PM has pre-created the worktree. You do NOT call `EnterWorktree`. Use absolute paths and `git -C /private/tmp/mg-wt-B <git-op>` for every git operation. Edit at `/private/tmp/mg-wt-B/.claude/skills/add-node/...`.

## Goal

Create a repo-local skill at `.claude/skills/add-node/` that creates a new card file in a target graph with valid frontmatter and a lint-clean result. The skill is the only sanctioned path for writing a card file; no other skill or agent may write cards directly.

## Context files to read

- `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/project_spec.md` — sections "Deliverables → Skills" and "Architectural decisions" (the locked rules about going through this skill for all writes).
- `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026/project_spec.md` — Phase 1 card schema (frontmatter required fields, optional fields, slug derivation).
- `/Users/alecchapman/Code/music-graphs/lib/cards.py` — `parse_card()` is the runtime consumer; new cards must satisfy its required-field checks.
- `/Users/alecchapman/Code/music-graphs/tools/lint_graphs.py` — the gate the skill must pass before reporting success.
- Existing cards as templates: `/Users/alecchapman/Code/music-graphs/graphs/band-x/cards/person-dave-alvin.md` and `.../album-los-angeles.md`.

## Definition of done

- [ ] `.claude/skills/add-node/SKILL.md` exists with Anthropic frontmatter (`name`, `description`, triggers) and body documenting:
  - **Inputs:** graph slug (e.g., `band-x`), node type (`person`, `group`, `album`, `track`, `location`, `note`, `memory`, etc.), node name, optional `spotify_url`, optional initial body paragraph, optional list of wikilinks to insert in body.
  - **Output:** new file at `graphs/<graph>/cards/<type>-<filename-slug>.md` with valid YAML frontmatter and a body paragraph.
  - **Required frontmatter fields:** `type`, `name`. Plus `canonical_link` when the user can provide a Wikipedia URL, `spotify_url` when available.
- [ ] Slug derivation matches Phase 1: filename is `<type>-<slug-or-disambiguator>.md`, and `parse_card` derives slug as filename-after-first-hyphen. Skill MUST sanity-check that the resulting slug doesn't collide with an existing card's slug in the same graph; on collision it warns and proposes a disambiguated filename (e.g., `track-sugar-track.md` for slug `sugar-track`).
- [ ] **Lint gate.** After writing the file, the skill runs `python tools/lint_graphs.py <graph>` (using the repo's `.venv/bin/python` when available) and confirms exit 0. If lint fails, the skill **reverts the write** and reports the lint error to the user.
- [ ] **No direct Spotify lookups.** If the user wants a Spotify URL on the new card, the SKILL.md instructs them (and Claude) to invoke `retrieve-spotify-song` first and pass the URL in. This skill never calls the Spotify MCP directly.
- [ ] **Body wikilinks.** If wikilinks are passed in, they're inserted as a sentence at the end of the body in `[[type:slug]]` form. If the target slug doesn't exist in the same graph, the skill warns but does not block (it might be a forward reference to a card being created in the same conversation).
- [ ] Helper at `.claude/skills/add-node/scripts/write_card.py` does the actual file write + lint invocation. Pytest at `tests/test_add_node_helper.py` covers: happy-path write to a temp graph dir, collision detection, lint-failure rollback (mock lint to fail), filename slug derivation including the `-track` disambiguator case.
- [ ] Smoke test documented in SKILL.md: "add a `person` card named 'Test Person' to a scratch graph; file appears; lint passes; revert."

## Not in scope

- Do NOT add edges. That's Track C.
- Do NOT call the Spotify MCP directly. Lookup is Track A's job.
- Do NOT modify `lib/cards.py` or `tools/lint_graphs.py`.
- Do NOT introduce any new card type schema beyond Phase 1's loose type set.

## Test protocol

```bash
cd /private/tmp/mg-wt-B
.venv/bin/pytest tests/test_add_node_helper.py -v 2>&1 | tee /tmp/test_results_track-b.txt
```
Confirm FAIL=0. Log path in HANDOFF.

## Handoff protocol

Append HANDOFF block:
```
HANDOFF (Track B):
- SKILL.md path: <absolute>
- Trigger phrases: <list>
- Helper module signature: write_card.write_card(graph, type, name, spotify_url=None, body=None, wikilinks=None) -> Path
- Lint invocation pattern: <exact command the skill uses>
- /tmp/test_results_track-b.txt: FAIL=<count>
- Integration gotchas for Track C (add-edge): <e.g., "card body's last paragraph is where add-edge should append wikilinks">
- Integration gotchas for Track E (family agent): <e.g., "agent must call retrieve-spotify-song before this skill when a URL is wanted">
- Deviations: <none / list>
```

## Close-out

Commit on `sprint/add-node`:
```
git -C /private/tmp/mg-wt-B add .
git -C /private/tmp/mg-wt-B commit -m "feat(skills): add-node card-creation skill with lint gate"
```
Report SHA + HANDOFF to PM.

---

HANDOFF (Track B):
- SKILL.md path: /private/tmp/mg-wt-B/.claude/skills/add-node/SKILL.md
- Trigger phrases: "add a card", "add node", "add a node", "create a card", "create a card for [X]", "add [X] to [graph]", "new card"
- Helper module signature: `write_card.write_card(graph, type, name, *, repo_root=None, graphs_root=None, spotify_url=None, canonical_link=None, body=None, wikilinks=None, run_lint=True, lint_cmd=None) -> Path` (raises `LintError` with `.stdout`/`.stderr`/`.returncode` on lint failure; file is removed before the exception)
- Lint invocation pattern: `<repo_root>/.venv/bin/python <repo_root>/tools/lint_graphs.py <graphs_root>` (falls back to `sys.executable` if no .venv). The lint script iterates subdirs of its argument, so the skill passes the graphs **root**, not a single graph dir — this lints every graph and catches cross-graph regressions.
- /tmp/test_results_track-b.txt: FAIL=0 (14 passed; full suite 65 passed)
- Integration gotchas for Track C (add-edge):
  - Card bodies written by this skill end with an optional "Related: …" sentence containing wikilinks. `add-edge` should append new wikilinks to the body as new sentences/paragraphs, not try to rewrite that sentence. Re-running through this skill is also fine — the lint gate catches dangling/orphan results.
  - Slug derivation: filename is `<type>-<slug>.md`; slug = filename-after-first-hyphen (per `lib/cards._derive_slug`). The disambiguator suffix (`-track`, `-2`, …) becomes part of the slug, so any edge that references a disambiguated card must use the disambiguated slug.
  - `check_collision(graph_dir, card_type, name)` is exported from `write_card.py` for read-only slug inspection.
- Integration gotchas for Track E (family agent):
  - Agent MUST invoke `retrieve-spotify-song` first when a Spotify URL is wanted, then pass the URL into `add-node`. This skill never touches the Spotify MCP.
  - On `LintError`, the new file has already been removed. Surface `.stdout` verbatim to the user — don't paraphrase. Common cause: orphan node (no edges), so the agent should encourage `wikilinks=[...]` on every new card.
  - The skill writes only frontmatter keys `type`, `name`, `canonical_link`, `spotify_url` (when supplied). Other frontmatter keys present in Phase 1 cards (e.g. `birth_date`, `release_year`) are not part of this skill's input surface in v1 — extend later if needed.
- Deviations:
  - SKILL.md does not include a dedicated `wikilinks: []` frontmatter array; wikilinks live in the body, matching every Phase 1 card. This is consistent with `lib/cards.parse_card` walking both frontmatter and body for wikilinks, so either would work — body-only keeps the YAML small.
  - The smoke test in SKILL.md uses a `_scratch` graph with a hand-seeded anchor card; the spec described it loosely. The pytest suite covers the same paths automatically.

