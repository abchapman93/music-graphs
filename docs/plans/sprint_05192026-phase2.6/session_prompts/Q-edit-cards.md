# Track Q — Editable cards

**Sprint:** sprint_05192026-phase2.6
**Worktree:** create via `EnterWorktree` (suggested branch: `sprint/edit-cards`)
**Acceptance gates:** Q1, Q2, Q3 in `test_registry.md`; M-Q manual.

## What to build

An Edit button on the right card panel that swaps the rendered body for a textarea, with Save/Cancel. Save round-trips to disk through a new write endpoint that gates on lint.

### Backend — `PUT /api/cards/<graph_slug>/<card_slug>`

In `app.py`:

```python
@app.route("/api/cards/<graph_slug>/<card_slug>", methods=["PUT"])
def api_update_card(graph_slug, card_slug):
    # 1. Locate file via _find_card_path; 404 if missing.
    # 2. Read original bytes -> in-memory backup.
    # 3. Split frontmatter + body. Replace body with request.json["body"].
    # 4. Write file.
    # 5. Run tools/lint_graphs.py on this graph (subprocess; capture stdout).
    # 6. If lint exit != 0: restore original bytes from backup, return 422 with stderr/stdout.
    # 7. Re-parse and return _build_card_payload(card).
```

Frontmatter must be preserved bit-for-bit (re-emit the original frontmatter block, do not round-trip through YAML — that would reformat). Only the body section after the closing `---` is rewritten.

Body in the request is plain markdown (not HTML). The panel JS sends the raw markdown the user edited.

### Frontend — Edit button + textarea

In `templates/_card_panel.html` and `static/js/graph.js`:

- Edit button in the panel header (top-right, next to existing close action).
- Click → fetch the raw markdown body for this card (extend the existing `/api/card/<g>/<s>` payload to include `body_md` alongside `body_html`, OR add `/api/card/<g>/<s>/source`). Choose the simpler extension; prefer adding `body_md` to the existing payload.
- Swap rendered body div for a `<textarea>` pre-filled with `body_md`. Add Save / Cancel buttons.
- Save → `PUT /api/cards/<g>/<s>` with `{body}`. On 200, re-render panel with the returned payload. On 422, show the lint error inline above the textarea; keep edits in the textarea so the user can fix.
- Cancel → revert to rendered view; no write.

### Edge cases

- If the card file was deleted between open and save: 404 from PUT → show error, keep textarea.
- If frontmatter is malformed in the original file: refuse to open the editor (button stays disabled with tooltip "frontmatter parse failed — edit manually").
- Edits are not auto-committed. Show a small "uncommitted edit on disk" notice once a save succeeds, until the user dismisses or reloads.

## Files likely touched

- `app.py` (new PUT route, optional `body_md` in `_build_card_payload`)
- `lib/cards.py` (if frontmatter-preserving split needs a helper)
- `templates/_card_panel.html`
- `static/js/graph.js`
- `static/css/style.css`
- `tests/test_app.py` (new tests for PUT happy + lint-fail-revert)

## Out of scope

- Frontmatter editing.
- Edge/wikilink graphical editing.
- Auto-commit.

## Done when

- Q1, Q2, Q3 signed.
- 126+ pytest pass (with new tests added); lint clean.
- A real factual edit demoed end-to-end.
- ff-merge to main.
