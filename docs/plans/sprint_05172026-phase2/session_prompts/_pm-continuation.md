# Sprint Manager Handoff — 2026-05-17 (end of session)

**Written:** 2026-05-17
**Sprint folder:** `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/`
**Main branch HEAD:** `a4da7d1 pm: Track H merged + Z1/Z2 signed; registry updated`
**Demo target:** 2026-06-07
**Task tracking:** None — `music-graphs` is not registered in task_lib. Sprint tracked via this folder + `test_registry.md`.

---

## Current state

**All 9 tracks merged. All automated registry rows ✅.** The sprint is functionally complete on the automated side: 100 pytest pass, lint clean across all 3 graphs, bowie-covers expanded from 3 to 10 cover artists. The only remaining items before sprint closeout are:

1. **Alec's additional feature requests** — Alec said after completing Track H he'd spec new features needed before sharing with family collaborators. He has not described these yet; the next session should collect them first.
2. **Manual M1–M10** — Alec must sign off on the family-agent UX and UI spot-checks.
3. **Sprint closeout** — write `_sprint-closeout.md` following the Phase 1 pattern.

| Track | Status | Merge SHA |
|---|---|---|
| Pre (Tony Gilkyson rename) | ✅ | `6b76576` |
| A `retrieve-spotify-song` | ✅ | `c3cccb1` |
| B `add-node` | ✅ | `6f6195c` |
| C `add-edge` | ✅ | `7999062` |
| D `expand-graph` | ✅ | `11a5d45` |
| E family-agent + setup docs | ✅ | `8a9cfa8` |
| F band-x dogfood (5 albums) | ✅ | `735e88a` |
| G pittsburgh-jazz dogfood (12 albums + notes) | ✅ | `6c9c8dd` |
| I cover images (M12) | ✅ | `b44a25f` |
| H bowie-covers expansion (7 covers + Nirvana URL) | ✅ | `e1220ee` |

Graph counts after Track H:
- band-x: 18n/55e (unchanged from Track F)
- pittsburgh-jazz: 28n/52e (unchanged from Track G)
- bowie-covers: 13 cards → 36 cards (23 new: 10 cover artists, 7 albums/singles, 6 songs; Nirvana URL resolved)

Automated registry: **all rows ✅** (H1, H2, Z1, Z2 signed off this session).
Manual registry: **M1–M10 all ⬜** — none yet attempted.

---

## What happened this session

1. **Resumed sprint manager** from prior `_pm-continuation.md`. Verified worktree `/private/tmp/mg-wt-H` intact on `sprint/bowie-covers-expansion`.
2. **Generated expand-graph candidates** for bowie-covers via Spotify MCP: 5 PM-proposed (Mott the Hoople, Philip Glass, Peter Gabriel, Bauhaus, Cat Power). Alec approved all 5 and added 2 more via Spotify URLs: "Kooks" by Orrin Evans/Rosenwinkel/Eubanks and "Absolute Beginners" by Carla Bruni. Alec also provided the Nirvana MTV Unplugged album URL that had been unresolvable in prior sessions.
3. **Verified all candidates** via Spotify MCP (artist IDs) and WebFetch (track/album identification). Compiled full list of 7 new cover entries with verified Spotify URLs.
4. **Wrote `/tmp/track-h-driver.py`** — one-shot Python driver calling `write_card` (run_lint=False) for all 23 new cards: 6 songs, 2 groups, 7 persons, 7 albums/singles, plus Nirvana frontmatter update.
5. **Ran driver** in the worktree. Lint caught one slug collision (album "All the Young Dudes" disambiguated to `all-the-young-dudes-album` because the song took `all-the-young-dudes`). Fixed two wikilinks via Python inline. Lint clean.
6. **100 pytest pass.** Committed `e1220ee`, rebased onto main, ff-merged, worktree torn down.
7. **Signed off H1, H2, Z1, Z2** in `test_registry.md`. Committed `a4da7d1`.
8. **Did not collect Alec's additional feature requests** — he said he'd give them after Track H was done; session ended before he described them.

---

## Immediate next steps (in order)

### Step 1 — Collect Alec's additional feature requests

Alec said at the start of this session: *"Let's finish the Bowie extract and then add a few additional features to the MVP that is needed before sharing with family collaborators. I'll give more details about the new requests after completing the bowie extract."*

Track H is now complete. Ask Alec: **"What are the additional features you want before sharing with Clare and Jeremiah?"** Then plan them as new tracks or inline changes depending on scope.

### Step 2 — Manual M1–M10 verification (Alec)

After any additional features are implemented, surface the manual checklist to Alec and ask when he wants to run through it. The M-rows are in `docs/plans/sprint_05172026-phase2/test_registry.md` lines 40–52. Key ones:

- **M1** — Local Claude Code: family agent adds one node + one edge without seeing YAML
- **M2** — claude.ai/code: same on cloud surface
- **M3** — Cover images render on `/` for all 3 graphs (no broken images)
- **M4** — All 3 graph views load with correct node/edge counts
- **M8** — bowie-covers additions are accurate (no hallucinated covers)
- **M9** — `expand-graph` workflow feels right to Alec
- **M10** — Setup docs (Clare/Jeremiah) make sense to a non-technical reader

### Step 3 — Sprint closeout

Once all M-rows are signed, write `docs/plans/sprint_05172026-phase2/_sprint-closeout.md` following the Phase 1 template at `docs/plans/sprint_05172026/_sprint-closeout.md`. Capture:
- Phase 2 delivered scope
- Skill-friction notes from F, G, H HANDOFFs (esp. `write_card.py` `repo_root` bug, missing free-text-body-addendum, Spotify licensor errors)
- Phase 3 wishlist (cloud hosting? new graphs? `add-note` skill?)

Then tag: `git tag v0.2-phase2-demo`.

---

## Key decisions (do not re-litigate)

- **All 7 cover entries are approved.** Alec confirmed all 5 PM-proposed candidates and added 2 of his own. No further approval needed for bowie-covers content.
- **Bauhaus exception:** "Ziggy Stardust" is a single with no album home. Using track URL as `spotify_url` is the accepted workaround (same as Carla Bruni "Absolute Beginners" and the Orrin Evans `#knowingishalfthebattle` album which is MCP-restricted). The single is represented as `type: album` with the track URL.
- **`all-the-young-dudes-album` slug**: The Mott the Hoople album was disambiguated because the song card `song-all-the-young-dudes` claimed the slug first. All internal wikilinks use `[[album:all-the-young-dudes-album]]`. This is final — don't rename.
- **Alec's new feature requests are unknown** — don't guess or pre-implement anything. Collect them in the next session first.

---

## Blocking questions

- **What additional features does Alec want before family sharing?** (Step 1 above — must ask before doing anything else)

---

## Skill-bug backlog (unchanged from prior session)

These are real bugs surfaced during dogfood. None block the current sprint. Fix before Phase 3 or before non-Alec users run the family agent:

1. **`write_card.py` `repo_root` inference wrong** — `parents[3]` resolves to `.claude/` in a worktree. Workaround: always pass `repo_root=` explicitly.
2. **No "add free-text body addendum" operation** — personal notes on person cards required direct Edit tool calls.
3. **Spotify `ALL_CONTENT_LICENSOR_RESTRICTED` errors** — family agent should explain in plain English.
4. **`add-edge` relationship verb** — caller must choose "recorded" vs "appears on" etc. per-call. A small taxonomy would help the family agent.

---

## Key files

| File | Role |
|---|---|
| `docs/plans/sprint_05172026-phase2/test_registry.md` | Pass/fail gate — all automated rows ✅, M1–M10 outstanding |
| `docs/plans/sprint_05172026-phase2/session_prompts/_pm-continuation.md` | This file — re-entry point for next PM session |
| `docs/plans/sprint_05172026/_sprint-closeout.md` | Phase 1 closeout — template for Phase 2 closeout |
| `graphs/bowie-covers/cards/` | 36 cards total after Track H |
| `tools/lint_graphs.py` | Always green — run before any commit |
