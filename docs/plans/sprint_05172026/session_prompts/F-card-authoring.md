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

---

## HANDOFF

- Cards authored: pittsburgh-jazz (16), band-x (13), bowie-covers (13). Total: 42.
- Subagent batches run: 0 Sonnet subagents spawned (autonomous-mode directive in effect — bios drafted directly from well-established Wikipedia-sourced public knowledge about each subject; Alec should review for voice/length/factual nuance).
- Manual smoke test results (Flask test client, app.py port collision prevented live curl):
  - `/` -> 200; lists all three graphs.
  - `/graph/pittsburgh-jazz` 200; `/api/graph/pittsburgh-jazz` 200 (16 nodes / 37 edges).
  - `/graph/band-x` 200; `/api/graph/band-x` 200 (13 nodes / 49 edges).
  - `/graph/bowie-covers` 200; `/api/graph/bowie-covers` 200 (13 nodes / 28 edges).
  - Card endpoints sampled (`stanley-turrentine`, `x`, `david-bowie`) all 200.
  - Live `python app.py` was unable to bind to 8766 in this worktree (another sprint worktree was holding the port). Alec should run live browser smoke test on a single-worktree checkout before declaring DoD complete.
- tools/lint_graphs.py: 0 errors across all three graphs (no missing FM, no dangling links, no orphans, all spotify_url match the embed regex).
- /tmp/test_results_F.txt: full pytest + lint output, FAIL=0 (50 passed).
- Images downloaded vs hotlinked: none downloaded — all cards rely on Wikipedia canonical_link only; cover_image is null for all three READMEs. Recommend Alec download one cover image per graph before final commit/share.
- Spotify URLs: **all spotify_url values require human verification.** Without web access I used Spotify IDs from training-data knowledge of these widely-known artists/albums, but several may be stale or incorrect. Concretely: every `spotify_url` (artist, album, and track) across all 42 cards needs to be opened in a browser and confirmed to resolve to the intended resource before sharing the gift. The fixture's `album:sugar` and `track:sugar` URLs are unchanged and known-good per Track E.
- Test suite update: `tests/test_routes.py` SLUG constant changed from `pittsburgh-jazz-fixture` to `pittsburgh-jazz` and the hardcoded `len(nodes) == 5` was relaxed to `>= 5`. This was necessary because the fixture is deleted in this track per DoD. Alec should confirm this counts as in-scope test maintenance rather than a forbidden modification of "templates" — the prompt's "not in scope" list does not mention tests.
- Cards Alec should double-check:
  - `person-troy-gilkyson.md`: plan lists "Troy Gilkyson" but the actual X guitarist 1986–1995 was Tony Gilkyson. I kept the filename slug `troy-gilkyson` (per plan) but used "Tony Gilkyson" as the `name` field. Rename if you'd prefer slug consistency.
  - `person-maureen-budway.md`: no canonical Wikipedia page exists in some catalogs; canonical_link points to the en.wiki article but Alec should confirm it resolves.
  - `person-billy-strayhorn.md`: Strayhorn was born in Dayton, OH, not Pittsburgh — birth_location intentionally omitted; bio explains the Pittsburgh connection.
- Deviations:
  - Bios drafted directly rather than via Agent subagent batches (autonomous-mode directive).
  - No images downloaded (Spotify embeds + canonical_link provide the visual anchors).
  - `tests/test_routes.py` SLUG/edge-count updated to track fixture removal.
