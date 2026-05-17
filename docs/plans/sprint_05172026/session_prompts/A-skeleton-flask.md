# Track A — Skeleton Flask

**Sprint:** `~/Code/music-graphs/docs/plans/sprint_05172026/`
**Branch:** `sprint/skeleton-flask` — **use `EnterWorktree` before writing any files.**
**Wave:** 1 (parallel with B, C)
**Dependencies:** P0 (repo-init) complete.

## Goal

Stand up the Flask app skeleton at `~/Code/music-graphs/app.py` serving a home page on `http://127.0.0.1:8766/`, with `templates/base.html`, a placeholder `templates/home.html`, `static/css/style.css`, and a `requirements.txt`. No real graph logic yet — that's Wave 2.

## Context files to read

- `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026/project_spec.md` — Architecture decisions (Flask, port 8766, no SPA, vanilla JS), module signatures (you don't implement them but the routes will call them in Wave 2).
- `/Users/alecchapman/Code/Claude Setup/tools/dashboard_app.py` — pattern reference for Flask app structure and route organization.
- `/Users/alecchapman/Code/Claude Setup/tools/wiki_viewer_core.py` — Flask + Jinja patterns used in the closest analogous app.
- `/Users/alecchapman/Code/music-graphs/docs/plans/music-graphs-plan.md` — overall plan (sections: "Critical files to create", "Flask app — server").

## Definition of done

- [ ] `requirements.txt` exists listing exactly: `Flask`, `Markdown`, `PyYAML`, `python-frontmatter`. Pin no versions (latest at install time is fine for Phase 1).
- [ ] `app.py` exists with:
  - A Flask app object.
  - A `/` route returning `home.html` with a hard-coded list of three stub graphs (`pittsburgh-jazz`, `band-x`, `bowie-covers`) so the page is visually populated.
  - A `__main__` block running `app.run(host="127.0.0.1", port=8766, debug=True)`.
  - Stub routes for the Wave 2/3 endpoints (`/graph/<slug>`, `/api/graph/<slug>`, `/api/card/<graph_slug>/<card_slug>`, `/graph/<slug>/card/<card_slug>`, `/cards`) — each returns `("not implemented", 501)`. This locks the URL shape now so Wave 2 can fill them in without renaming.
- [ ] `templates/base.html` exists with: HTML5 doctype, viewport meta, link to `/static/css/style.css`, header with site title "music graphs" linking to `/`, single `{% block content %}` block.
- [ ] `templates/home.html` exists, extends base, renders the 3 stub graphs as cards (name + placeholder description). Plus a link to `/cards`.
- [ ] `static/css/style.css` exists with minimal styling: readable font (system-ui stack), max-width container, basic spacing. Does NOT need to be polished — just not ugly.
- [ ] `README.md` (replace stub from P0) explains: prerequisites (Python 3.11+), how to set up a venv, `pip install -r requirements.txt`, `python app.py`, and which URL to open.
- [ ] `pytest` smoke test at `tests/test_app.py` that imports `app` from `app.py` and asserts `app.test_client().get("/").status_code == 200`. Use Flask's test client; no server start required.
- [ ] Running locally: `cd ~/Code/music-graphs && python app.py` starts cleanly with no tracebacks; visiting `http://127.0.0.1:8766/` returns 200 and renders the 3 stub graphs.

## Test protocol

```bash
cd ~/Code/music-graphs
pytest tests/ -v 2>&1 | tee /tmp/test_results_<task_id>.txt
```
Confirm `FAIL=0` (or the equivalent "no failures" line). Log the path in your HANDOFF.

Additionally, manually start `python app.py` in a background shell, `curl -sI http://127.0.0.1:8766/ | head -1` should return `HTTP/1.1 200 OK`, then stop the server. Include the curl result in HANDOFF.

## Not in scope

- Do **not** implement card parsing (`lib/cards.py`) — that's Track B.
- Do **not** implement graph building (`lib/graph.py`) — that's Track D.
- Do **not** implement Spotify embed (`lib/spotify.py`) — that's Track C.
- Do **not** write any graph view JS (`static/js/graph.js`) — Track E.
- Do **not** author any cards.
- Do **not** create the `lib/` package directory at all. The stubs in app.py should not import from `lib/`.

## Handoff protocol

Before `complete_task()` (or before declaring done if no task tracking), append a HANDOFF note in the task notes or to this prompt file:
```
HANDOFF:
- Routes scaffolded: <list>.
- requirements.txt versions installed during testing: <list>.
- Any deviations from the spec: <none / list>.
- /tmp/test_results_<task_id>.txt: <path>, FAIL=<count>.
- Manual curl check: <result>.
```

## Close-out

Brief one-paragraph summary: files created, smoke test result, any decisions made (e.g., chose `python-frontmatter` over manual YAML parsing — note that here even though parsing is Track B's job). Commit on `sprint/skeleton-flask` with subject `feat: Flask skeleton + home page + route stubs`.
