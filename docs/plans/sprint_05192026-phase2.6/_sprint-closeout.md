# Phase 2.6 — Sprint closeout

**Written:** 2026-05-20
**Sprint folder:** `docs/plans/sprint_05192026-phase2.6/`
**Duration:** scaffolded 2026-05-19 evening; closed 2026-05-20
**Demo target:** 2026-06-07 (still ahead of schedule)

## What shipped

| Track | Feature | Commit | Tests |
|---|---|---|---|
| N | Top-of-page search bar (ranked, keyboard-nav) | `05ba0ef` | +3 |
| O | Left directory panel (grouped by type, click-to-select) | `05ba0ef` (with N) | — |
| P | Collapsible + drag-resizable panels (localStorage-persisted) | `1b1707d` + `b33527d` + `dbd57ca` | — |
| Q | Editable card bodies (PUT /api/cards, lint-revert atomic) | `d60f741` | +5 |
| R | Web-based note + memory creation (POST /api/notes) | `5c31183` | +4 |

**Test count:** 126 → 141 (12 new tests added across N/Q/R).
**Lint:** clean throughout.
**All automated gates** (N1, N2, O1, O2, P1, P2, P3, Q1, Q2, Q3, R1, R2, R3) **signed.**
**All manual gates** (M-N, M-O, M-P, M-Q, M-R, M-Z) **signed by Alec.**

## Architectural patterns established

1. **In-process lint-revert.** Track Q introduced and Track R reused the pattern: in-memory backup → write → `lib.graph.lint_graph()` → on fail, restore byte-identical original + return 422. Replaces the spec's "subprocess `tools/lint_graphs.py <slug>`" approach because the CLI takes a graphs-root, not a slug, and would lint unrelated graphs.
2. **Skill libs as direct imports, not subprocesses.** Track R imports `add-node/scripts/write_card.py` and `add-edge/scripts/add_edge.py` directly, passing `run_lint=False` and running one combined lint after both writes. Confirms the foundation-skill scripts are reusable as Python libs from the Flask app.
3. **Panel content wrapper.** `#card-panel` and `#directory-panel` `<aside>` elements wrap their dynamic content in `.panel-content` child divs so render functions (`renderCard`, `renderDirectory`) target the inner div without clobbering sibling chrome (collapse chevrons, resize handles).
4. **Byte-level frontmatter preservation.** `lib.cards.split_frontmatter_bytes` splits raw bytes around the second `---\n` so frontmatter is re-emitted verbatim on save — no YAML round-trip, no reformatting.

## Real cards edited or created via the new UI during M sign-off

- `graphs/pittsburgh-jazz/cards/album-no-need-for-words.md` — factual edit (Track Q live test)
- `graphs/pittsburgh-jazz/cards/person-sean-jones.md` — factual edit (Track Q live test)
- (Track R live test) — note created from the UI; recorded in main commit history.

The Track Q manual test was the feature working as designed: Alec used the new editor to fix two real factual errors he'd been carrying.

## Carry-forward (deferred)

From Phase 2.5, still open:
- **Track J — Google Form suggestion intake.** Session prompt ready at `docs/plans/sprint_05172026-phase2/session_prompts/J-suggestion-intake.md`.
- **Track M (Phase 2.5) — sprint closeout.** Blocked on Track J merge + Phase 2.5 manual signs.

From this sprint, intentionally out of scope:
- Frontmatter editing from web.
- Edge editing / deletion from web.
- Mobile/responsive layout polish.
- Auto-commit of edits.

From the skill-bug backlog (carry from earlier handoff):
- `retrieve-spotify-album` foundation skill (album-first expansion blocker).
- `retrieve-spotify-playlist` foundation skill.
- `add-node` slug-collision disambiguator polish.
- Slug spell-check lint pass.
- `ALL_CONTENT_LICENSOR_RESTRICTED` Spotify error copy.
- `add-edge` relationship verb taxonomy.

## Tag

After merge: `git tag v0.2.6-graph-viewer-ux`.

## Next session

The graph viewer is now a real exploration + light-authoring surface. The next natural move is Phase 2.5 Track J (Google Form intake) — that closes Phase 2.5 and clears the road to the 2026-06-07 family share.
