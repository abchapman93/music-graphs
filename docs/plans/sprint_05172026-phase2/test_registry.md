# Test Registry — sprint_05172026-phase2

**Sprint:** music-graphs Phase 2
**Demo target:** 2026-06-07
**Sign-off:** PM signs automated rows after `/tmp/test_results_<task>.txt` shows FAIL=0; Alec signs manual rows after end-to-end exercise.

---

## Automated (PM signs off)

| # | Track | Check | Verification | Status |
|---|---|---|---|---|
| A1 | A | `retrieve-spotify-song` skill smoke test: lookup "Ashgrove Dave Alvin" returns the verified album URL | Documented smoke test in SKILL.md; canonical URL is the locked value | ✅ (merge c3cccb1) |
| A2 | A | Skill fails loudly when MCP unavailable (does not return a guess) | Fail-loud contract stated verbatim in SKILL.md; sentinel-prefix policy for callers | ✅ (merge c3cccb1) |
| B1 | B | `add-node` skill produces a lint-clean card | 14 helper tests pass; lint gate runs `tools/lint_graphs.py` and confirms exit 0 | ✅ (merge 6f6195c) |
| B2 | B | `add-node` refuses to write a card that fails lint | `LintError` raised with file pre-removed (rollback contract); covered in tests | ✅ (merge 6f6195c) |
| C1 | C | `add-edge` adds a wikilink in the correct card body | 10 helper tests pass; happy-path + symmetric both covered | ✅ (merge 7999062) |
| C2 | C | `add-edge` warns on dangling wikilinks (target slug doesn't exist) | `DanglingTargetError` raised by default (`on_dangling="abort"`); `"forward"` mode opt-in; covered in tests | ✅ (merge 7999062) |
| D1 | D | `expand-graph` surfaces 5–10 candidates and pauses for approval | Ceiling clamp `[1,10]` enforced in `_clamp_ceiling()`; overflow count returned; 14 helper tests pass | ✅ (merge 11a5d45) |
| D2 | D | Approved candidates flow through `add-node` + `add-edge` (no direct file writes) | Default `search_fn` raises `NotImplementedError`; injected `add_node_fn`/`add_edge_fn` are the only write path; dry-run sentinel test guarantees no side effects | ✅ (merge 11a5d45) |
| E1 | E | Family-agent definition exists and loads in both Claude Code and claude.ai/code | `.claude/agents/music-graphs-builder.md` + `docs/family-setup.md` present; rehearsal node+edge add executed cleanly against scratch graph. Real-session M1/M2 deferred to Alec. | ✅ (merge 8a9cfa8) |
| F1 | F | 5 new band-x album cards exist (Cervenka/Somewhere Gone, Doe/A Year in the Wilderness, Alvin/Ashgrove, Bonebrake/Coleman, Zoom/Johny Walk Don't Run Paulene) | All 5 cards present; band-x graph 13→18 nodes, 49→55 edges | ✅ (merge 735e88a) |
| F2 | F | All 5 albums have verified `spotify_url` in frontmatter | 3 provided URLs (Alvin/Bonebrake/Zoom) verified via WebFetch+MCP cross-check; 2 (Cervenka/Doe) MCP-sourced and Alec-approved | ✅ (merge 735e88a) |
| F3 | F | Tony Gilkyson rename complete and lint-clean (pre-sprint; just confirm still good) | `lint_graphs.py band-x` exits 0; no `troy-gilkyson` references remain | ✅ (pre-sprint) |
| G1 | G | pittsburgh-jazz has ≥1 album per person card | Count person cards vs album cards with person wikilinks | ⬜ |
| G2 | G | Gene Harris Trio Plus One card exists, linked to both Turrentine and Ray Brown | grep wikilinks in album card | ⬜ |
| G3 | G | Sean Jones album card exists with Duquesne note | grep "Duquesne" in card body | ⬜ |
| G4 | G | Maureen Budway album card has notes about Alec's accompaniment, recording-before-death, "Hard Times" significance | grep for all three in card body | ⬜ |
| G5 | G | Sean Jones ↔ Maureen Budway album edge (on "Sweet Lover No More") exists | wikilink in Maureen album card body referencing Sean Jones | ⬜ |
| H1 | H | bowie-covers has ≥5 new cards added via `expand-graph` | `git log` shows new cards from H session | ⬜ |
| H2 | H | Nirvana MTV Unplugged Spotify URL resolved OR documented as unresolvable | Card has verified URL, or explicit note `spotify_url: null  # MCP search exhausted` | ⬜ |
| I1 | I | All 3 graph READMEs have non-null `cover_image` with verified URL or local path | All 3 READMEs reference `images/<file>.jpg`; files downloaded from Wikimedia Commons | ✅ (merge b44a25f) |
| I2 | I | Cover images render on home page (no broken-image icons) | `/graph-images/<slug>/<file>` route added in app.py; home page returns 3 `<img class="cover">` tags; HEAD requests return 200 for all three | ✅ (merge b44a25f) |
| Z1 | all | Phase 1 pytest still passes (51 tests, FAIL=0) | `pytest` from repo root, sink to `/tmp/test_results_z1.txt` | ⬜ |
| Z2 | all | `lint_graphs.py` reports 0 errors across all 3 graphs | Run lint at end of sprint | ⬜ |

---

## Manual (Alec signs off)

| # | Check | Status |
|---|---|---|
| M1 | Family-agent end-to-end on local Claude Code: add one new node + one new edge to any graph without ever seeing YAML or being asked to write markdown | ⬜ |
| M2 | Family-agent end-to-end on claude.ai/code (cloud): same as M1 in the cloud surface | ⬜ |
| M3 | Cover images render correctly on `/` for all 3 graphs (no broken images, sensible crop) | ⬜ |
| M4 | All 3 graph views still load (`/graph/band-x`, `/graph/bowie-covers`, `/graph/pittsburgh-jazz`) with correct node/edge counts | ⬜ |
| M5 | Click a new band-x solo-album card — Spotify embed plays | ⬜ |
| M6 | Click the Gene Harris Trio Plus One card — Spotify embed plays; both Turrentine + Ray Brown wikilinks navigate | ⬜ |
| M7 | Sean Jones card and Maureen Budway album card both surface Alec's personal Duquesne notes | ⬜ |
| M8 | New bowie-covers additions are accurate (no hallucinated covers; each has Wikipedia or Spotify backing) | ⬜ |
| M9 | `expand-graph` skill workflow feels right: candidate list is sensible, approve/reject UX is clear | ⬜ |
| M10 | Setup docs for Clare/Jeremiah make sense — Alec can follow them as if he were a non-technical user | ⬜ |

---

## Deferred / accepted gaps

- **Nirvana MTV Unplugged in New York Spotify URL.** Pre-sprint retry via MCP again returned no match (consistent with Phase 1 closeout). Track H attempts via `expand-graph` + web search. If still unfindable, card stays `spotify_url: null` with documenting comment — does not block demo (H2).

---

## Demo-ready gate

All automated rows ✅ + all manual rows ✅ (or explicitly deferred with documentation). PM flags **"Demo-ready: NO — N rows outstanding"** until both columns clear.
