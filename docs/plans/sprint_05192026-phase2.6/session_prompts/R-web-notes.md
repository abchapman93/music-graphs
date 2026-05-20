# Track R — Web note creation

**Sprint:** sprint_05192026-phase2.6
**Depends on:** Track Q merged (reuses write/lint-revert pattern)
**Worktree:** create via `EnterWorktree` (suggested branch: `sprint/web-notes`)
**Acceptance gates:** R1, R2, R3 in `test_registry.md`; M-R manual.

## What to build

From any selected node, open a modal that creates a new `note-*.md` or `memory-*.md` card and writes a wikilink edge from the source card body.

### Backend — `POST /api/notes/<graph_slug>`

In `app.py`:

```python
@app.route("/api/notes/<graph_slug>", methods=["POST"])
def api_create_note(graph_slug):
    # body: {type: "note"|"memory", title, body, source_slug, source_type}
    # 1. Validate type in {"note","memory"}.
    # 2. Resolve graph dir; 404 if missing.
    # 3. Delegate to add-node skill's Python helper (see .claude/skills/add-node/)
    #    to compute slug + write the card. Reuse — do not re-implement.
    # 4. Delegate to add-edge skill's helper to insert a wikilink from
    #    source_type:source_slug -> new note. Symmetric link policy: same default
    #    as the skill's CLI behavior.
    # 5. Run lint_graphs.py on this graph.
    # 6. On lint fail: revert BOTH writes (delete new file; restore source body
    #    from in-memory backup) and return 422 with the lint error.
    # 7. On success: return {slug, type, name, url} for the new card.
```

**Reuse rule:** import from the skill libs. The skills already handle slug collisions, frontmatter, and lint-revert atomicity. Do not duplicate that logic in the route.

### Frontend — "+ Note" button + modal

In `templates/_card_panel.html` and `static/js/graph.js`:

- "+ Note" button in the panel header.
- Click → modal with:
  - Type radio: ⦿ Note  ◯ Memory
  - Title input (text)
  - Body textarea (markdown)
  - Create / Cancel buttons.
- Create → `POST /api/notes/<g>` with `{type, title, body, source_slug, source_type}`.
- On 200: close modal; re-fetch `/api/graph/<slug>` so the new node appears; refresh the left directory; auto-select the new node (opens its panel).
- On 422: show lint error inline in the modal; keep inputs.

### Validation

- Title required, ≥3 chars.
- Body required, ≥1 char.
- Block if source node has no card on disk (unlikely but defensive).

## Files likely touched

- `app.py` (new POST route)
- `templates/_card_panel.html` (modal partial)
- `static/js/graph.js` (modal open + submit + post-success refresh)
- `static/css/style.css` (modal styling)
- `tests/test_app.py` (R1, R2, R3 tests)

## Out of scope

- Editing existing notes through this flow (Track Q handles that).
- Choosing the link verb (use the `add-edge` skill default).
- Creating non-note/non-memory card types from web (deferred to a future phase).

## Done when

- R1, R2, R3 signed.
- 126+ pytest pass; lint clean.
- A real note created from the UI on one of the three graphs.
- ff-merge to main.
