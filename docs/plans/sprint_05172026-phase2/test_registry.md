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
| G1 | G | pittsburgh-jazz has ≥1 album per person card | All 10 person cards have ≥1 album/track wikilink; pittsburgh-jazz 16n/37e → 28n/52e | ✅ (merge 6c9c8dd) |
| G2 | G | Gene Harris Trio Plus One card exists, linked to both Turrentine and Ray Brown | `album-gene-harris-trio-plus-one.md` body has both wikilinks; reciprocal edges on both person cards | ✅ (merge 6c9c8dd) |
| G3 | G | Sean Jones album card exists with Duquesne note | Note about Duquesne lives on the *person* card per spec; album `album-no-need-for-words.md` is separate. `person-sean-jones.md` contains "Alec studied trumpet with Sean Jones at Duquesne University in Pittsburgh." | ✅ (merge 6c9c8dd) |
| G4 | G | Maureen Budway album card has notes about Alec's accompaniment, recording-before-death, "Hard Times" significance | Notes live on the *person* card (where Alec specified); `person-maureen-budway.md` contains all three elements (accompanied her voice lessons; recorded shortly before her death; "Hard Times Come Again No More" carries weight in that context) | ✅ (merge 6c9c8dd) |
| G5 | G | Sean Jones ↔ Maureen Budway album edge (on "Sweet Lover No More") exists | `album-sweet-candor.md` body has `[[person:sean-jones]]` in the "Sweet Lover No More" sentence; reciprocal edge written on `person-sean-jones.md` | ✅ (merge 6c9c8dd) |
| H1 | H | bowie-covers has ≥5 new cards added via `expand-graph` | 23 new cards (7 cover artists, 7 albums/singles, 6 songs, 2 groups, 1 URL fix) added in merge e1220ee; lint clean | ✅ (merge e1220ee) |
| H2 | H | Nirvana MTV Unplugged Spotify URL resolved OR documented as unresolvable | `album-unplugged-in-new-york.md` now has `spotify_url: https://open.spotify.com/album/1To7kv722A8SpZF789MZy7` (Alec-provided, verified via WebFetch) | ✅ (merge e1220ee) |
| I1 | I | All 3 graph READMEs have non-null `cover_image` with verified URL or local path | All 3 READMEs reference `images/<file>.jpg`; files downloaded from Wikimedia Commons | ✅ (merge b44a25f) |
| I2 | I | Cover images render on home page (no broken-image icons) | `/graph-images/<slug>/<file>` route added in app.py; home page returns 3 `<img class="cover">` tags; HEAD requests return 200 for all three | ✅ (merge b44a25f) |
| Z1 | all | Phase 1 pytest still passes (51 tests, FAIL=0) | 100 passed, 0 failed (suite grew from 51→100 with Phase 2 skill tests) | ✅ (2026-05-17) |
| Z2 | all | `lint_graphs.py` reports 0 errors across all 3 graphs | 0 errors across band-x, bowie-covers, pittsburgh-jazz | ✅ (2026-05-17) |

---

## Manual (Alec signs off)

| # | Check | Status |
|---|---|---|
| M1 | ~~Family-agent end-to-end on local Claude Code~~ | ⛔ DROPPED (Phase 2.5 scope cut — family won't use Claude Code; Google Form intake instead) |
| M2 | ~~Family-agent end-to-end on claude.ai/code (cloud)~~ | ⛔ DROPPED (same reason as M1) |
| M3 | Cover images render correctly on `/` for all 3 graphs (no broken images, sensible crop) | ⬜ |
| M4 | All 3 graph views still load (`/graph/band-x`, `/graph/bowie-covers`, `/graph/pittsburgh-jazz`) with correct node/edge counts | ⬜ |
| M5 | Click a new band-x solo-album card — Spotify embed plays | ⬜ |
| M6 | Click the Gene Harris Trio Plus One card — Spotify embed plays; both Turrentine + Ray Brown wikilinks navigate | ⬜ |
| M7 | Sean Jones card and Maureen Budway album card both surface Alec's personal Duquesne notes | ⬜ |
| M8 | New bowie-covers additions are accurate (no hallucinated covers; each has Wikipedia or Spotify backing) | ⬜ |
| M9 | `expand-graph` skill workflow feels right: candidate list is sensible, approve/reject UX is clear | ⬜ |
| M10 | ~~Setup docs for Clare/Jeremiah~~ | ⛔ DROPPED (Phase 2.5 scope cut — no Claude Code onboarding needed) |

---

## Phase 2.5 — Pre-family-share polish (added 2026-05-17)

See `_phase-2.5-plan.md` for full track briefs.

### Automated (PM signs off)

| # | Track | Check | Status |
|---|---|---|---|
| J1 | J | `triage-suggestion` skill reads one CSV row, presents to Alec, calls `add-node`/`add-edge` on approval | ⬜ |
| J2 | J | `graphs/{slug}/inbox/` exists for all 3 graphs; `.gitkeep` + README explains drop-CSV-here flow | ⬜ |
| K1 | K | Graph view fills viewport (full-bleed `graph-shell`; ~78% canvas, side panel `clamp(280px, 22vw, 380px)`) | ✅ (merge 6fe0ed2) |
| K2 | K | Physics freeze on stabilization; "Frozen" checkbox toggle in `.graph-controls` | ✅ (merge 6fe0ed2) |
| K3 | K | `+` / `−` / `⤢` (fit) buttons in top-right of canvas; scroll-zoom preserved | ✅ (merge 6fe0ed2) |
| L1 | L | `retrieve-wikipedia-category` skill: given a Category URL, returns member pages (title + URL) | ⬜ |
| L2 | L | `expand-graph` reads `seed_sources:` from graph root card and uses Wikipedia categories as candidate source | ⬜ |
| L3 | L | bowie-covers and pittsburgh-jazz root cards updated with `seed_sources:` Wikipedia category URLs | ⬜ |
| Z3 | all | Phase 1+2 pytest still passes after Phase 2.5 merges | ⬜ |
| Z4 | all | `lint_graphs.py` reports 0 errors across all 3 graphs after Phase 2.5 merges | ⬜ |

### Manual (Alec signs off)

| # | Check | Status |
|---|---|---|
| M11 | Google Form created and published; link saved in `docs/family-collaboration.md` | ⬜ |
| M12 | End-to-end: drop a sample CSV in `graphs/bowie-covers/inbox/`, run `triage-suggestion`, see candidate, approve, verify card written | ⬜ |
| M13 | Graph view UX feels good to Alec: large canvas, frozen-by-default, zoom buttons work as expected | ✅ (2026-05-17 — Alec confirmed "really good" after live UI eyeball) |
| M14 | `expand-graph` with Wikipedia seeds surfaces sensible candidates Alec hasn't already added | ⬜ |

---

## Deferred / accepted gaps

- **Nirvana MTV Unplugged in New York Spotify URL.** Pre-sprint retry via MCP again returned no match (consistent with Phase 1 closeout). Track H attempts via `expand-graph` + web search. If still unfindable, card stays `spotify_url: null` with documenting comment — does not block demo (H2).

---

## Demo-ready gate

All automated rows ✅ + all manual rows ✅ (or explicitly deferred with documentation). PM flags **"Demo-ready: NO — N rows outstanding"** until both columns clear.
