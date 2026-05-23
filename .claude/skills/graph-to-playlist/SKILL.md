---
name: graph-to-playlist
description: Build a Spotify playlist from a music-graphs graph. Walks the graph's track and album cards, gathers their verified `spotify_url`s, and calls the Spotify MCP `create_playlist` tool with a descriptive prompt naming the tracks. Triggered by "make a playlist from [graph]", "graph to playlist", "spotify playlist for [graph]", "build a playlist from the [X] graph".
triggers:
  - "make a playlist from [graph]"
  - "build a playlist from [graph]"
  - "graph to playlist"
  - "spotify playlist for [graph]"
  - "playlist from the [X] graph"
  - "/graph-to-playlist [slug]"
---

# Skill: graph-to-playlist

## What it does

Given a music-graphs graph slug, this skill:

1. Reads every card under `graphs/<slug>/cards/`.
2. Collects `track` cards (and optionally `album` cards) whose frontmatter carries a `spotify_url`.
3. Dedupes URIs (same `spotify_url` may appear under multiple card types).
4. Asks the user to confirm scope (which types, all-or-subset, ordering).
5. Calls `mcp__68e7e171-8619-450d-bfc7-458af6964130__create_playlist` with a descriptive prompt that names the graph theme and lists the specific tracks.
6. Writes a sidecar verification file at `graphs/<slug>/playlist.md` recording the URIs that were submitted, so the user can audit which tracks Spotify's NL creator actually honored.

## Important constraint

The Spotify MCP only exposes a natural-language `create_playlist` tool. There is **no API to add specific Spotify URIs to a playlist directly**. This means:

- Spotify's playlist generator interprets the prompt and may include tracks the prompt does **not** mention, and may **omit** tracks the prompt **does** mention.
- For best fidelity, this skill builds a prompt that explicitly names every selected track with `"Track Name" by Artist` form, plus the canonical `spotify:track:<id>` URIs. Spotify generally honors specific track mentions, but does not guarantee it.
- The skill always writes a `playlist.md` sidecar listing the URIs that were intended, so the user can verify and supplement manually inside the Spotify app.

If/when Spotify exposes a precise "add tracks by URI" tool via MCP, this skill should switch to it and drop the NL prompt path.

## Inputs

| Input | Required | Notes |
|---|---|---|
| `graph` | yes | Graph slug — must match a folder under `graphs/`. |
| `types` | no | Card types to include. Default: `["track"]`. May also include `"album"` (album cards' `spotify_url` becomes an album reference in the prompt). |
| `name` | no | Playlist name. Defaults to the graph's display name from `graphs/<slug>/README.md` or the slug. |
| `description` | no | Short description for the prompt. Defaults to a one-liner derived from the README. |
| `limit` | no | Max number of tracks. Default: no limit, but warn at >100 (Spotify NL prompts get unreliable past that). |

## Workflow

### Step 1 — Verify the Spotify MCP is available

Confirm `mcp__68e7e171-8619-450d-bfc7-458af6964130__create_playlist` is registered. If not, return:

```
MCP_UNAVAILABLE: Spotify MCP create_playlist tool is not connected in this session. Cannot create a playlist.
```

### Step 2 — Gather candidate cards

Run `scripts/collect_tracks.py <graph> [--types track,album]`. The script:

- Walks `graphs/<graph>/cards/*.md`.
- Parses YAML frontmatter via `lib/cards.py:parse_card`.
- Selects cards whose `type` is in the requested types and whose `spotify_url` is non-empty.
- Normalizes URLs via `scripts/normalize_url.py:normalize_spotify_url` (rejects malformed).
- Dedupes by URI.
- Returns a JSON list of `{type, name, slug, spotify_url, spotify_uri}` objects.

### Step 3 — Present the candidates for approval

Show the user:

- Total count, grouped by card type.
- A bulleted preview (first ~20 tracks) with name + URI.
- Ask: "Submit all to Spotify, pick a subset, or cancel?"

Wait for explicit user confirmation before calling the MCP. Never auto-submit.

### Step 4 — Build the `create_playlist` prompt

Compose a single English-language prompt of the form:

```
Create a playlist titled "<name>": <description>. Include these specific tracks:
- "Blackbird" by Brad Mehldau (spotify:track:0DiwteTBKNrcWW0w6RcS9c)
- "Paranoid Android" by Brad Mehldau (spotify:track:…)
…
```

Rules for the prompt:

- Start with the verb "Create" (per the MCP tool's "MUST start with intents" rule).
- Quote track titles exactly.
- Include both human-readable `"Title" by Artist` and the bare `spotify:track:<id>` URI — the URI helps Spotify resolve to the exact recording.
- Keep the prompt under ~6000 characters; if longer, split into batches (see Step 6).

### Step 5 — Call `create_playlist`

Invoke the MCP tool with `prompt=<prompt>` and `language="en"`. Surface the tool's response (which typically contains a Spotify deep link) verbatim to the user.

### Step 6 — Batch fallback (only if >50 tracks)

If the prompt is too long or contains too many tracks, the skill MAY split into multiple playlists named `<name> (Part 1)`, `<name> (Part 2)`, etc., and submit each. Confirm with the user before splitting.

### Step 7 — Write the sidecar verification file

Write `graphs/<graph>/playlist.md` (overwriting any prior copy) with frontmatter:

```yaml
---
generated_at: <ISO timestamp>
graph: <slug>
playlist_name: <name>
track_count: <n>
spotify_playlist_url: <url-from-mcp-response-if-present>
---
```

…followed by a markdown list of every URI submitted, so the user can:

- Open the playlist in Spotify and check which tracks landed.
- Manually add any tracks the NL creator missed (paste URIs into the Spotify search bar inside the playlist).

This sidecar is **not** required to be lint-clean — it is metadata, not a card. The lint rule `graphs/<slug>/cards/*.md` only governs files under `cards/`.

## Output

On success, the skill:

1. Reports the playlist name, track count, and the Spotify deep link returned by the MCP.
2. Notes the path to `playlist.md` and reminds the user that NL generation may not be 1:1.

On failure (MCP unavailable, no tracks found, user cancels), return a single short message explaining what happened. Do not write the sidecar.

## Out of scope

- Editing existing playlists. The MCP has no "update playlist" tool.
- Adding tracks one-by-one to a known playlist ID. Same reason.
- Generating playlists from anything other than a music-graphs graph.
- Public/collaborative playlist toggles. The MCP creates private playlists only.

## Helper script

`scripts/collect_tracks.py` is the only code this skill ships. It is a thin wrapper around `lib/cards.py` parsing — no new card-parsing logic, no Spotify network calls. See the script's docstring for usage.
