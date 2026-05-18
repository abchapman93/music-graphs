# Track J — Google Form suggestion intake

**Sprint:** sprint_05172026-phase2 (Phase 2.5)
**Worktree:** `/private/tmp/mg-wt-J` on branch `sprint/suggestion-intake`
**Acceptance gates:** J1, J2 in `test_registry.md`; M11, M12 manual.

## What to build

1. **Per-graph inbox folders.** Create `graphs/{band-x,bowie-covers,pittsburgh-jazz}/inbox/` each with:
   - `.gitkeep`
   - `README.md` (one paragraph: "Drop Google Form CSV exports here. Run `triage-suggestion` to review.")

2. **`skills/triage-suggestion/` skill.** Mirror the structure of `skills/expand-graph/` (SKILL.md + tools/ + tests/).
   - **Input:** path to a CSV file in any `graphs/*/inbox/` folder.
   - **CSV columns expected** (match the Google Form fields in `_phase-2.5-plan.md`): `timestamp, suggester, graph, suggestion, why, url, memory`.
   - **Behavior:** Process one row at a time. Present to Alec. On approval, route to `add-node` (if suggestion is a new node) and/or `add-edge` (if it's a relationship), reusing existing skills — never write cards directly.
   - **Processed rows** move to `inbox/_processed/<YYYY-MM-DD>.csv` (append). Skipped/rejected rows move to `inbox/_rejected/<YYYY-MM-DD>.csv` with reason.
   - **Fail-loud** if CSV columns missing or graph column doesn't match a known graph slug.
   - **Tests:** dry-run with injected `add_node_fn`/`add_edge_fn` (same pattern as `expand-graph`'s D2 test).

3. **`docs/family-collaboration.md`.** Explain the form → CSV → triage flow end-to-end. Leave a placeholder for the Google Form URL ("Alec to fill after publishing").

## Done when

- All J-row checks pass.
- 100+ pytest pass, lint clean across all 3 graphs.
- New skill listed in `skills/README.md` (or equivalent registry).

## Skill-bug to fix in-track

`write_card.py` `repo_root` inference wrong in worktrees — `triage-suggestion` will trip on this. Fix by always passing `repo_root=` explicitly OR by patching the inference logic so `parents[N]` resolves correctly even in worktrees. Document the fix.
