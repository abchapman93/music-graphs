# Track C — Spotify embed helper

**Sprint:** `~/Code/music-graphs/docs/plans/sprint_05172026/`
**Branch:** `sprint/spotify-embed` — **use `EnterWorktree` before writing any files.**
**Wave:** 1 (parallel with A, B)
**Dependencies:** P0 (repo-init) complete.

## Goal

Implement `lib/spotify.py` with `spotify_embed_url(url: str) -> str | None`, converting Spotify resource URLs into embed URLs. Tiny module (~30 lines including docstring + tests). Pure-Python, no Flask.

## Context files to read

- `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026/project_spec.md` — section "Module signatures" (the spotify_embed_url contract) and "Architecture decisions" (Spotify section: embed iframe only, no OAuth, no API calls).
- `/Users/alecchapman/Code/music-graphs/docs/plans/music-graphs-plan.md` — section "Spotify embedded player" for the iframe usage downstream.

## Definition of done

- [ ] `lib/__init__.py` exists (may already exist from Track B; do NOT delete or modify any contents Track B placed there).
- [ ] `lib/spotify.py` exports:
  - `spotify_embed_url(url: str) -> str | None`
  - `SPOTIFY_KINDS: frozenset[str]` containing exactly `{"track", "album", "playlist", "artist", "episode", "show"}`.
- [ ] `spotify_embed_url` behavior:
  - Input `https://open.spotify.com/track/<id>` (or `/album/`, `/playlist/`, `/artist/`, `/episode/`, `/show/`) → returns `https://open.spotify.com/embed/<kind>/<id>`.
  - Strips query strings (`?si=...`) from the input before producing output. The output does NOT carry any query string.
  - Accepts `http://` and `https://`; output always uses `https://`.
  - Accepts trailing slashes; output has no trailing slash.
  - Returns `None` for `None`, empty string, non-Spotify URLs, Spotify URLs of unknown kind, and any malformed Spotify URL.
  - Does NOT raise on bad input — returns `None`.
- [ ] Unit tests at `tests/test_spotify.py` cover, at minimum:
  - Track URL with `?si=...` query string → correct embed URL, no query string.
  - Album, playlist, artist, episode, show URLs each → correct embed URL.
  - http:// input → https:// output.
  - Trailing slash input → no trailing slash output.
  - `None`, `""`, `"not a url"`, `"https://example.com/track/xyz"`, `"https://open.spotify.com/unknown/xyz"`, `"https://open.spotify.com/track/"` (missing id) → all return `None`.
- [ ] All tests pass.

## Test protocol

```bash
cd ~/Code/music-graphs
pytest tests/test_spotify.py -v 2>&1 | tee /tmp/test_results_<task_id>.txt
```
Confirm FAIL=0. Log path in HANDOFF.

## Not in scope

- Do **not** make any HTTP requests to Spotify. URL transformation only.
- Do **not** authenticate, fetch metadata, or call the Spotify API.
- Do **not** generate the iframe HTML — that lives in `templates/graph.html` (Track E).
- Do **not** touch `app.py`, `lib/cards.py`, `lib/graph.py`, or templates.

## Handoff protocol

```
HANDOFF:
- lib/spotify.py exports: spotify_embed_url, SPOTIFY_KINDS.
- URL forms handled: track, album, playlist, artist, episode, show.
- Edge cases (None, malformed, unknown kind): all return None.
- Integration note for Track E: call `spotify_embed_url(frontmatter.get("spotify_url"))` at render time in app.py or in the template via a Jinja filter.
- /tmp/test_results_<task_id>.txt: <path>, FAIL=<count>.
- Deviations: <none / list>.
```

## Close-out

Commit on `sprint/spotify-embed` with subject `feat(lib): Spotify URL → embed URL helper`. One-sentence summary.

HANDOFF:
- lib/spotify.py exports: spotify_embed_url, SPOTIFY_KINDS.
- URL forms handled: track, album, playlist, artist, episode, show.
- Edge cases (None, malformed, unknown kind, missing id, non-https scheme, wrong host): all return None.
- Integration note for Track E: call `spotify_embed_url(frontmatter.get("spotify_url"))` at render time in app.py or in the template via a Jinja filter.
- /tmp/test_results_track-C.txt: /tmp/test_results_track-C.txt, FAIL=0.
- Deviations: none.
