# Track F — Card authoring (3 graphs)

**Sprint:** `~/Code/music-graphs/docs/plans/sprint_05172026/`
**Branch:** `sprint/card-authoring` — **use `EnterWorktree` before writing any files.**
**Wave:** 4 (parallel with G)
**Dependencies:**
- **E (graph-view) merged to `main`.** App must render real `graphs/<slug>/` folders end-to-end before authoring at scale.
- Verify: `python app.py` runs, `curl -sI http://127.0.0.1:8766/graph/pittsburgh-jazz-fixture | head -1` returns 200.

## Goal

Author all three real graph folders:
- `graphs/pittsburgh-jazz/` — 10–20 cards
- `graphs/band-x/` — 10–20 cards
- `graphs/bowie-covers/` — 10–20 cards

Each card conforms to the schema in the sprint spec. Biographies are drafted by Sonnet subagents (Agent tool, parallel batches) fetching Wikipedia content, then reviewed and edited by Alec before commit. Spotify links are captured by hand. The fixture graph (`graphs/pittsburgh-jazz-fixture/`) is left in place during the sprint and deleted in this track's final commit once `graphs/pittsburgh-jazz/` is in place.

## Context files to read

- `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026/project_spec.md` — "Card schema", "Architecture decisions" (image policy), "Demo criteria".
- `/Users/alecchapman/Code/music-graphs/docs/plans/music-graphs-plan.md` — "Three authored graphs" section lists the people/albums/places per graph.
- `/Users/alecchapman/Code/music-graphs/graphs/pittsburgh-jazz-fixture/cards/` — examples of schema-conforming cards from Track E. Use these as the template.
- `/Users/alecchapman/Code/music-graphs/lib/cards.py` — the parser. If you deviate from the schema, the parser will tell you (run it locally).

## Process — using Sonnet subagents for bios

For each Person card you author, spawn a Sonnet subagent in parallel batches of 3–5 via the **Agent** tool. Each subagent receives:
- The person's name and a Wikipedia URL.
- The card schema and an example Person card from the fixture folder.
- Instructions to return: YAML frontmatter (filled in) + a 150–300 word markdown body. The body should use `[[type:slug]]` wikilinks for any other people / places / groups / albums that will exist in the same graph.

Review every subagent draft before committing. Fact-check anything that looks shaky against the source Wikipedia page. Edit voice / length as needed. Wikipedia hotlinks for `image` are fine; download key images (e.g., the cover image of each graph) into `graphs/<slug>/images/` and commit.

Do not use Codex for bio drafting.

## Definition of done

**Per graph folder** (`graphs/pittsburgh-jazz/`, `graphs/band-x/`, `graphs/bowie-covers/`):

- [ ] `README.md` exists with frontmatter `name`, `description` (1–2 sentences), `cover_image` (path or URL).
- [ ] `cards/` contains 10–20 cards covering the entities listed in `docs/plans/music-graphs-plan.md` "Three authored graphs" section. (Exact count is Alec's call.)
- [ ] Every card has valid frontmatter: `type`, `name`, plus type-appropriate optional fields.
- [ ] Every Track and Album card has a `spotify_url` that resolves to a real Spotify resource (verify by pasting in browser).
- [ ] Every Person card has a `canonical_link` to Wikipedia and a body of 150–300 words.
- [ ] Each card has at least one `[[type:slug]]` wikilink connecting it to another card in the same graph (no orphan nodes).
- [ ] The graph has at least one Note or Memory card (Memory for Band X — "X at Red Butte" — is explicitly called out in the plan).
- [ ] Running `python -c "from lib.graph import build_graph; from pathlib import Path; import json; print(json.dumps(build_graph(Path('graphs/<slug>')), indent=2))"` returns a graph with no errors and zero dangling wikilinks.

**Final cleanup:**

- [ ] `graphs/pittsburgh-jazz-fixture/` deleted (its purpose served).
- [ ] Manual smoke test: `python app.py`, visit each of the three `/graph/<slug>` URLs, click ~5 nodes per graph, confirm at least one Spotify embed plays on each graph. Capture findings (or any broken cards) in HANDOFF.

## Test protocol

```bash
cd ~/Code/music-graphs
pytest tests/ -v 2>&1 | tee /tmp/test_results_<task_id>.txt
```
Confirm FAIL=0 (no regression from prior tracks).

Additionally, write a lint script at `tools/lint_graphs.py` (small, ~30 lines) that walks every graph folder and reports:
- Cards with missing required frontmatter fields.
- Dangling wikilinks.
- Orphan nodes (no inbound or outbound edges).
- Cards with `spotify_url` not matching the embed-URL regex.

Run it and append output to `/tmp/test_results_<task_id>.txt`. Zero errors required.

## Not in scope

- Do **not** modify `lib/cards.py`, `lib/graph.py`, `lib/spotify.py`, `app.py`, or any templates. If parsing or rendering breaks on any card, STOP and write a HANDOFF note describing the case.
- Do **not** implement `/cards` — Track G.
- Do **not** add new card types beyond the spec's nine.
- Do **not** invent biographical content. Subagents must cite Wikipedia. If Wikipedia is silent on a person, use a shorter body or a Note card pointing elsewhere — do not fabricate.

## Handoff protocol

```
HANDOFF:
- Cards authored: pittsburgh-jazz (<N>), band-x (<N>), bowie-covers (<N>).
- Subagent batches run: <count> Sonnet sessions, <count> bios drafted, <count> edits required.
- Manual smoke test results: <one line per graph; note any Spotify embeds that failed to play>.
- tools/lint_graphs.py: <one-line summary of output>.
- /tmp/test_results_<task_id>.txt: <path>, FAIL=<count>.
- Images downloaded vs hotlinked: <one line per graph>.
- Deviations: <none / list>.
```

## Close-out

Commit per graph (three commits minimum, plus one for the lint tool, plus one for fixture cleanup). Subjects: `content(pittsburgh-jazz): <N> cards`, `content(band-x): <N> cards`, `content(bowie-covers): <N> cards`, `tools: lint_graphs.py`, `chore: remove pittsburgh-jazz-fixture`. Final summary lists card counts and any cards Alec is unsure about.
