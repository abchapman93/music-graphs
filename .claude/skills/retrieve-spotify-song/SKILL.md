---
name: retrieve-spotify-song
description: Look up a canonical Spotify URL for an artist/album/track query using the Spotify MCP. Use whenever a skill, agent, or user needs a verified `open.spotify.com` link — never guess Spotify IDs from training data. Triggers include "find on Spotify", "Spotify URL for [X]", "look up [album/track] on Spotify", "verify Spotify link", and any time another music-graphs skill needs a `spotify_url`.
---

# Skill: retrieve-spotify-song

## Triggers

- "find [X] on Spotify"
- "lookup [X] on Spotify" / "look up [X] on Spotify"
- "Spotify URL for [X]"
- "Spotify link for [X]"
- "verify this Spotify URL: [url]"
- "search Spotify for [X]"
- "what's the Spotify ID for [X]"
- Programmatic: invoked by `add-node`, `add-edge`, `expand-graph`, and the family-friendly graph agent whenever a card needs a `spotify_url`.

## What it does

Given an artist, album, and/or track query, this skill calls the **Spotify MCP search tool** (`mcp__68e7e171-8619-450d-bfc7-458af6964130__search`), presents the top candidates to the user, waits for the user to pick one, and returns the **canonical bare URL** in the form:

```
https://open.spotify.com/<type>/<id>
```

where `<type>` is one of `track`, `album`, `artist`, `playlist`.

This is the **foundation Spotify-lookup skill** for the music-graphs repo. Every other skill that touches Spotify links uses it. No skill embeds Spotify search logic directly, and no skill writes a Spotify URL it has not verified through this skill.

## Input

The user (or calling skill) provides one or more of:

- **artist** — e.g., "Dave Alvin"
- **album** — e.g., "Ashgrove"
- **track** — e.g., "Heartbreak Hotel"
- **type hint** — optional, one of `track`, `album`, `artist`; defaults to inferring from which fields were supplied (track present → track; album present → album; artist only → album-or-artist disambiguation).

Free-form queries like `"Ashgrove Dave Alvin"` are also accepted and passed to the MCP as-is.

## Fail-loud contract (LOCKED)

**If the Spotify MCP tool returns no results, errors out, or is unavailable, this skill returns an explicit "not found / MCP unavailable" message. It does NOT return a guessed URL, a training-data URL, or a URL constructed from any source other than a live MCP response.**

Failure modes and their literal responses:

| Failure | Response |
|---|---|
| MCP tool not registered in this session | `MCP_UNAVAILABLE: Spotify MCP tool (mcp__68e7e171-8619-450d-bfc7-458af6964130__search) is not connected in this session. Cannot verify a Spotify URL.` |
| MCP tool errors at call time | `MCP_ERROR: <error message from tool>. Cannot verify a Spotify URL.` |
| MCP returns zero results for the query | `NOT_FOUND: Spotify returned no results for query "<query>". Try a different spelling or supply an explicit Spotify URL for me to verify.` |

This rule exists because Phase 1 of this project (sprint_05172026) shipped fabricated Spotify IDs that resolved to wrong tracks. See `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026/_sprint-closeout.md`. Re-introducing training-data URLs is the single most important regression to prevent.

## Disambiguation policy

When the MCP returns multiple candidates:

1. Present up to **5** candidates as a numbered list, one per line, each showing:
   - **Title** (track name or album name)
   - **Subtitle** — artist(s), release year, and type (album/track/single)
   - **URL** — the canonical bare URL after normalization
2. **Wait for the user to pick a number** (or type `none` / `more` / a new query).
3. **Never auto-pick the first result.** Even if confidence is high, present the choices and require explicit user selection. The only exception: when invoked programmatically by another skill with an `auto_pick=true` flag AND the MCP returns exactly one result, the skill may return that one result without prompting. With more than one result, prompting is mandatory.
4. If the user types `more`, request additional results from the MCP (offset/pagination) and present the next batch.
5. If the user types `none`, return `NOT_FOUND` per the fail-loud contract.

## Output format

On success, the skill returns a **bare canonical URL**:

```
https://open.spotify.com/<type>/<id>
```

- **No** query parameters (`?si=...`, `?utm_source=...`).
- **No** URL fragments (`#play`).
- **No** locale prefix (`/intl-fr/...` is stripped).
- **No** trailing slash.
- **Always** `https://` (not `http://`).

All URLs returned by this skill pass through `scripts/normalize_url.py` (function: `normalize_spotify_url`) before being returned to the caller.

## Workflow

### Step 1 — Verify the MCP tool is available

Confirm that the tool `mcp__68e7e171-8619-450d-bfc7-458af6964130__search` is registered in this session. If not, return `MCP_UNAVAILABLE` per the fail-loud contract and stop.

### Step 2 — Build the query string

Concatenate the supplied fields into a single query string, in this priority order:

```
"<track>" artist:"<artist>" album:"<album>"
```

If a field is missing, omit its segment. If only an artist is provided, the query is just `artist:"<artist>"`. The Spotify search API accepts these field qualifiers natively.

If the user provided a free-form query string, pass it through unchanged.

### Step 3 — Call the MCP search tool

Invoke `mcp__68e7e171-8619-450d-bfc7-458af6964130__search` with the query string and a `type` parameter matching the most specific field supplied (`track` if track present, else `album` if album present, else `artist`). Request up to 5 results.

If the tool errors, return `MCP_ERROR: <message>` and stop.
If the tool returns an empty list, return `NOT_FOUND: ...` and stop.

### Step 4 — Normalize and present candidates

For each candidate in the MCP response:

1. Extract the result URL (or build it from the `id` and `type` fields).
2. Pass it through `normalize_spotify_url()` from `scripts/normalize_url.py`. If normalization returns `None`, drop that candidate (it is not a usable Spotify URL).
3. Build the display row: `<n>. <title> — <artists>, <year> (<type>) → <canonical-url>`.

Present the numbered list to the user.

### Step 5 — Wait for user selection

Block on the user response. Accept:

- A number (1–N) → return the canonical URL for that candidate.
- `none` → return `NOT_FOUND`.
- `more` → page forward (re-call the MCP with an offset) and present the next batch.
- A new query string → restart at Step 2 with the new query.

### Step 6 — Return the canonical URL

Return the selected canonical URL as a bare string. Do not wrap it in markdown, JSON, or prose unless the caller explicitly asked for a formatted response.

## Smoke test

A successful lookup for `Ashgrove Dave Alvin` (type: album) MUST return:

```
https://open.spotify.com/album/2At5ShihdUNDdc33Ztp7RX
```

If the MCP returns a different ID for this query, surface it to the user and stop — do not silently substitute. This is the canonical regression check from the sprint plan.

## Helper

`scripts/normalize_url.py` exposes one public function:

```python
from scripts.normalize_url import normalize_spotify_url

normalize_spotify_url("https://open.spotify.com/album/2At5ShihdUNDdc33Ztp7RX?si=abc")
# → "https://open.spotify.com/album/2At5ShihdUNDdc33Ztp7RX"

normalize_spotify_url("spotify:track:7qiZfU4dY1lWllzX7mPBI3")
# → "https://open.spotify.com/track/7qiZfU4dY1lWllzX7mPBI3"

normalize_spotify_url("https://example.com/foo")
# → None
```

Tested by `tests/test_normalize_spotify_url.py`. Run with:

```bash
.venv/bin/pytest tests/test_normalize_spotify_url.py -v
```

## Integration notes for other skills

- `add-node` calls this skill when a new card needs a `spotify_url`. The caller writes the returned URL into the card's frontmatter; this skill does NOT touch any card or graph files.
- `expand-graph` calls this skill once per candidate before presenting candidates to the user for approval. If this skill returns `NOT_FOUND` for a candidate, `expand-graph` drops that candidate from the suggestion list.
- This skill is **read-only on the graph**. It does not write cards, edges, or any graph state.

## Out of scope

- No CLI. The skill's interface is the Claude conversation plus the MCP tool.
- No batching API. Callers loop over items themselves.
- No caching layer. Each lookup hits the MCP fresh; cheap and correct beats clever.
- No automatic fallback to web search if the MCP fails. Fail loud per the contract.
