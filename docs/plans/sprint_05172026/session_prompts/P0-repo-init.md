# Track P0 — Repo init

**Sprint:** `~/Code/music-graphs/docs/plans/sprint_05172026/`
**Branch:** none (one-shot, runs on `main` of a fresh repo)
**Wave:** Pre-sprint

## Goal

Initialize `~/Code/music-graphs/` as a git repo with `.gitignore`, an initial commit that includes the existing `docs/plans/sprint_05172026/` content, and a `main` branch ready for Wave 1 worktrees.

## Context files to read

- `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026/project_spec.md` — sprint spec (you are implementing infrastructure that backs this).
- `/Users/alecchapman/Code/music-graphs/docs/plans/music-graphs-plan.md` — overall Phase 1 plan.

## Definition of done

- [ ] `cd ~/Code/music-graphs && git status` reports a clean working tree on `main`.
- [ ] `.gitignore` exists at repo root and contains at minimum: `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `.DS_Store`, `.pytest_cache/`, `.idea/`, `.vscode/` (but allow committing `.vscode/settings.json` if Alec adds one later — use `!.vscode/settings.json` exception).
- [ ] A `README.md` stub exists at repo root with title, one-line description, and a "Setup / Run" placeholder section. (Track A will flesh this out.)
- [ ] Initial commit subject reads: `init: music-graphs Phase 1 scaffolding`. Body lists what was committed.
- [ ] `git log --oneline` shows exactly one commit.
- [ ] `git worktree list` shows only the main worktree.

## Not in scope

- Do **not** install Python dependencies, create a venv, or write `requirements.txt`. That's Track A.
- Do **not** write any `lib/`, `templates/`, `static/`, or `graphs/` content. Those are Wave 1+.
- Do **not** create a GitHub remote.

## Handoff protocol

Before declaring done, append a HANDOFF note here:
```
HANDOFF:
- Repo initialized at <path>, initial commit <sha>.
- .gitignore contents: <one-line summary>.
- Any deviations: <none / list>.
```

## Close-out

Brief one-paragraph summary of what was committed and the commit SHA. No `end_session` call needed (no task tracking for this pre-sprint setup).
