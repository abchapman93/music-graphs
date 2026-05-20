# Session starter — Tracks N + O (search + directory)

You're picking up Tracks N and O of music-graphs Phase 2.6 (Graph viewer UX mini-sprint).

**Read first, in order:**
1. `docs/plans/sprint_05192026-phase2.6/project_spec.md` — sprint shape and scope boundaries.
2. `docs/plans/sprint_05192026-phase2.6/test_registry.md` — acceptance gates N1/N2/O1/O2.
3. `docs/plans/sprint_05192026-phase2.6/session_prompts/N-O-search-directory.md` — full track plan, files, reference UI pointers.
4. **Reference UI:** `/Users/alecchapman/Code/Claude Setup/app/templates/wiki_viewer.html` — lift styling cues from the search + sidebar patterns.

**Then read the files you'll modify:**
- `app.py` (current routes — you'll add `/api/cards/<slug>`)
- `templates/graph.html` (current layout — you'll restructure to `directory | canvas | detail`)
- `static/js/graph.js` (current click handlers — you'll add search + directory)
- `static/css/style.css`

**Setup:**
- Use `EnterWorktree` to branch off main (suggested name `sprint/search-directory`).
- Branch from current main HEAD.
- Run `pytest` and `python tools/lint_graphs.py` to confirm green baseline before changing anything.

**Done when** N1/N2/O1/O2 sign in `test_registry.md`, tests + lint clean, all three graphs visually verified, and ff-merged to main with the worktree torn down.

Hand back to the PM (Alec) when ready for Track P kickoff.
