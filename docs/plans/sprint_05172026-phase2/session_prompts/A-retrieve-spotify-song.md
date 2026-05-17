# Track A — `retrieve-spotify-song` skill

**Sprint:** `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/`
**Branch:** `sprint/retrieve-spotify-song`
**Worktree path (PM pre-creates):** `/private/tmp/mg-wt-A`
**Wave:** 1 (parallel with B)
**Dependencies:** none (foundation skill)

## How to work on this branch

PM has pre-created the worktree. You do NOT call `EnterWorktree`. Use absolute paths and `git -C /private/tmp/mg-wt-A <git-op>` for every git operation. Edit files at `/private/tmp/mg-wt-A/.claude/skills/retrieve-spotify-song/...`.

## Goal

Create a repo-local Anthropic-style skill at `.claude/skills/retrieve-spotify-song/` that takes an artist/album/track query, calls the Spotify MCP search tool, and returns a canonical `open.spotify.com` URL. This is the foundation Spotify-lookup skill used by every other skill in this sprint.

## Context files to read

- `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/project_spec.md` — sections "Deliverables → Skills" and "Architectural decisions" (the locked rules about MCP-only lookup).
- `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026/_sprint-closeout.md` — why training-data Spotify IDs are forbidden (Phase 1 incident).
- An existing skill for format reference: `/Users/alecchapman/.claude/skills/retrieve-paper/SKILL.md` (frontmatter + body structure).

## Definition of done

- [ ] `.claude/skills/retrieve-spotify-song/SKILL.md` exists with Anthropic-style frontmatter (`name`, `description`, triggers in the body).
- [ ] The skill's behavior is documented as: accept a query (artist/album/track or all three), call the Spotify MCP search tool, present top candidates to the user with title + subtitle + URL, and return the user-approved canonical URL.
- [ ] **Fail-loud contract.** If the Spotify MCP tool returns no results or is unavailable, the skill returns an explicit "not found / MCP unavailable" message. It does NOT return a guessed or training-data URL. This rule is stated verbatim in the SKILL.md.
- [ ] **Disambiguation policy.** When multiple candidates are returned, the skill presents them and waits for user choice; it does NOT auto-pick the first result.
- [ ] **Output format.** The skill returns a bare `https://open.spotify.com/<type>/<id>` URL — no tracking params, no query strings (strip `?utm_source=...` etc.).
- [ ] A helper at `.claude/skills/retrieve-spotify-song/scripts/normalize_url.py` strips Spotify URLs to canonical form. Pytest test at `tests/test_normalize_spotify_url.py` covers: with-query-params, with-fragment, already-canonical, non-spotify-URL (returns None or raises).
- [ ] Smoke test documented in SKILL.md: "lookup 'Ashgrove Dave Alvin' should return `https://open.spotify.com/album/2At5ShihdUNDdc33Ztp7RX`".

## Not in scope

- Do NOT implement card writes, edge writes, or graph mutations. This skill is read-only on the graph; it returns URLs only.
- Do NOT call `add-node` or any other sprint skill. This is a leaf.
- Do NOT modify `lib/spotify.py` (Phase 1 module; consumed at request time by `app.py`, not by skills).
- Do NOT build a CLI; the skill's interface is the Claude conversation + the MCP tool.

## Test protocol

```bash
cd /private/tmp/mg-wt-A
.venv/bin/pytest tests/test_normalize_spotify_url.py -v 2>&1 | tee /tmp/test_results_track-a.txt
```
(If the venv doesn't exist in the worktree, create it from `requirements.txt`.) Confirm FAIL=0. Log the path in HANDOFF.

## Handoff protocol

Append a HANDOFF block to the bottom of this file before declaring done:
```
HANDOFF (Track A):
- SKILL.md path: <absolute path>
- Trigger phrases registered: <list>
- Spotify MCP tool name expected: mcp__68e7e171-8619-450d-bfc7-458af6964130__search (Phase 1's tool; verify still present)
- normalize_url.py helper: <path>, public function name(s): <list>
- /tmp/test_results_track-a.txt: FAIL=<count>
- Integration gotchas for Track B (add-node): <e.g., "skill returns URL only; caller writes it into frontmatter">
- Deviations from spec: <none / list>
```

## Close-out

Commit on `sprint/retrieve-spotify-song`:
```
git -C /private/tmp/mg-wt-A add .
git -C /private/tmp/mg-wt-A commit -m "feat(skills): retrieve-spotify-song MCP-backed lookup skill"
```
Tell PM the commit SHA and HANDOFF location.
