# Sprint Manager Handoff — 2026-05-19 (end of session, late)

**Written:** 2026-05-19
**Sprint folder:** `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/`
**Main branch HEAD:** `bdb7c95 feat(expand-graph): typed resources schema + 4-phase orchestration + content expansion (L1/L2/L3 + TC2/TC3)`
**Worktrees:** none (mg-wt-resources merged + removed; orphan mg-L-wikipedia-seeds removed)
**Demo target:** 2026-06-07
**Task tracking:** None — `music-graphs` is not registered in task_lib. Sprint tracked via this folder + `test_registry.md`.

---

## Current state

**Track L shipped end-to-end + two major content expansions on main.** This session resumed from the earlier 2026-05-19 PM handoff (Track L implemented but uncommitted), ran the three acceptance test cases live, ff-merged the worktree to main, and used the new 4-phase `expand-graph` orchestrator to expand `pittsburgh-jazz` twice (Wikipedia seed → 10 artists; curated Spotify playlist → 29 artists/groups) while a parallel session expanded `bowie-covers` (TC3). All work landed in a single commit `bdb7c95`.

| Phase / Track | Status | Notes |
|---|---|---|
| Phase 1 | ✅ | tagged v0.1 (prior sprint) |
| Phase 2 automated (Pre, A–I, H) | ✅ | all merged |
| Phase 2.5 Track K — graph view UI | ✅ | merged `6fe0ed2` |
| **Phase 2.5 Track L — Wikipedia seeds + orchestrated expand** | ✅ | merged `bdb7c95`; L1/L2/L3 signed in `test_registry.md`; M14 ready to sign pending app eyeball |
| **Phase 2.5 TC2 (pittsburgh-jazz Wikipedia)** | ✅ | 10 new persons + 10 tracks via 4-phase orchestrator |
| **Phase 2.5 TC2-playlist (pittsburgh-jazz Spotify playlist)** | ✅ | 14 new persons + 3 groups + 28 tracks + 1 note via direct playlist scrape (resolver deferred) |
| **Phase 2.5 TC3 (bowie-covers Wikipedia)** | ✅ | 5 new artists + song/track split for 5 covers (parallel session) |
| Phase 2.5 Track J — suggestion intake | ⬜ | session prompt ready: `J-suggestion-intake.md` |
| Phase 2.5 Track M — closeout | ⏳ | unblocked once Alec confirms M14 sign-off + J merges |

**Graph counts on main as of HEAD:**
- band-x: 18 nodes / 55 edges (unchanged)
- bowie-covers: 49 cards (↑13 from ~36)
- pittsburgh-jazz: 94 cards (↑66 from 28)

---

## What happened this session

1. **Resumed from `_pm-continuation.md` (earlier 2026-05-19).** Read the prior handoff and the worktree state; the Track L code was complete (126 pytest pass, lint clean) but uncommitted.
2. **TC1 — quick parse smoke test.** Ran `parse_resources('graphs/pittsburgh-jazz/README.md')` and `parse_resources('graphs/bowie-covers/README.md')` — both returned the expected typed `Resource` entry. ✅
3. **TC2 — pittsburgh-jazz Wikipedia expansion (4-phase orchestrator end-to-end).**
   - Phase 1 (this session): probed `Category:Jazz_musicians_from_Pittsburgh` → 62 members, ~54 net-new after slug-hint dedupe (existing graph had 8 of the 62 in person cards).
   - Phase 2 (delegated subagent): returned 10 canonical candidates — Ahmad Jamal, Mary Lou Williams, Billy Eckstine, Kenny Clarke, Roy Eldridge, George Benson, Sonny Clark, Dodo Marmarosa, Dakota Staton, Maxine Sullivan.
   - Phase 3 (delegated subagent): all 10 Spotify tracks resolved successfully via `retrieve-spotify-song` (0 NOT_FOUND).
   - Phase 4 (this session): album-first attempt failed — only 3/10 albums resolvable via Spotify MCP (track-search response lacks parent-album metadata; `release_date` never returned). Alec chose tracks instead. Wrote 10 person + 10 track cards via `write_card`. Lint clean. ✅
4. **TC2-playlist — pittsburgh-jazz Spotify playlist expansion (ad-hoc).** Alec passed a 275-track curated playlist (`7cY0P6FRWDh29dGxERjTOx`) with stopping rule "≥1 song or album per unique artist, each new artist has a knowledge card."
   - Spotify MCP doesn't accept playlist URIs (this is the deferred `spotify-playlist` resolver). Workaround: scraped `https://open.spotify.com/embed/track/<id>` `__NEXT_DATA__` JSON for each track. 12 parallel workers hit rate limits (85/275 errors); serial retry with delay cleared all errors.
   - 31 unique primary artists (29 effective after collapsing "Ahmad Jamal Trio" → person:ahmad-jamal, "Art Blakey & The Jazz Messengers" → person:art-blakey, "Paul Chambers Quintet" → person:paul-chambers, "Ray Brown Trio" → person:ray-brown). Skipped Lee Morgan's only playlist track (studio chatter, not a song).
   - **Renamed `person-errol-garner.md` → `person-erroll-garner.md`** + updated backlinks across 6 cards (billy-strayhorn, earl-hines, album-concert-by-the-sea, location-pittsburgh, note-hill-district, track-misty).
   - Wrote 14 new person + 3 new group cards + 28 new track cards + 1 note card (`note-liberty-avenue` documenting Sean Jones / Mack Avenue SuperBand / Liberty Avenue vs Wylie Avenue / Hill District distinction). Bios woven with cross-references: *Weather Bird* ↔ Earl Hines, *Blood Count* ↔ Billy Strayhorn, *Wylie Avenue Days* ↔ note:hill-district, *Pittsburgh Brethren* ↔ Blakey/Ray Brown apprenticeship, Joe Negri ↔ Johnny Costa via Mister Rogers.
5. **TC3 — bowie-covers expansion (parallel session).** A separate `/resume`-spawned session ran the orchestrator on `Category:Songs_written_by_David_Bowie`; added 5 new artists (Culture Club, Lulu, M Ward, Tina Turner, Tori Amos) + introduced a song/track card split pattern (`song-1984.md` = composition, `track-1984-track.md` = specific recording) for 5 covers.
6. **Single commit + ff-merge.** Both sessions worked in the shared `mg-wt-resources` worktree. After Alec confirmed both expansions and noticed the app couldn't see the new cards (running from main repo), did one combined commit `bdb7c95` (100 files, +1793 lines), ff-merged into main, removed worktree, deleted `worktree-mg-wt-resources` branch, and also removed the stale orphan `mg-L-wikipedia-seeds` worktree + branch.

---

## Immediate next steps

### Step 1 — Confirm M14 sign-off in `test_registry.md`

Manual end-to-end runs of the 4-phase orchestrator are now done on both `pittsburgh-jazz` (Wikipedia path) and `bowie-covers` (Wikipedia path). Once Alec reloads the app and confirms the new graphs render correctly, sign **M14** in the registry. L1/L2/L3 already signed pre-commit; no changes needed there.

### Step 2 — Launch Track J (suggestion intake) in a fresh worktree

Session prompt ready: `docs/plans/sprint_05172026-phase2/session_prompts/J-suggestion-intake.md`. Worktree slug: `mg-J-suggestion-intake`. The `write_card.py` `repo_root` bug is already fixed on main; Track J can rely on the worktree-safe inference.

### Step 3 — Track M (sprint closeout)

Blocked on Track J merged + manual signs (M3/M4/M5/M6/M7/M8/M9/M11/M12/**M14**). When all green, sign Z3/Z4 final; write `_sprint-closeout.md`; `git tag v0.2-phase2-demo`.

---

## Key decisions (do not re-litigate)

- **Album-first expansion is officially blocked on `retrieve-spotify-album`.** TC2 attempted album cards first; the Spotify MCP track-search response does not include parent-album metadata, and `release_date` is never surfaced. Workaround for the live test cases was track cards. The orchestrator's "album-only default" rule in `expand-graph/SKILL.md` is still correct; the gap is at the foundation-skill layer.
- **`spotify-playlist` resolver is now a concrete need, not a theoretical reservation.** Today's TC2-playlist round had to scrape `embed/track/<id>` `__NEXT_DATA__` JSON across 275 tracks with rate-limit retries. A real `retrieve-spotify-playlist` foundation skill is the right fix — it should accept either a playlist URL or a list of track URLs and return resolved (title, artists, album_uri, track_uri) tuples.
- **Erroll Garner slug typo fixed.** The pre-existing `person-errol-garner.md` (one 'l') was renamed to `person-erroll-garner.md` (canonical spelling). Six backlinks updated. Future Erroll references should use the corrected slug.
- **Variant artist credits map to the leader's person card.** Tracks credited to "Ahmad Jamal Trio" / "Art Blakey & The Jazz Messengers" / "Paul Chambers Quintet" / "Ray Brown Trio" were attached to the leader's existing person card, not given new `group:` cards. New `group:` cards (Elevations, Poogie Bell Band, Mack Avenue SuperBand) were created only when the band identity is the primary recording entity.
- **Non-Pittsburgh artists are allowed in `pittsburgh-jazz`** when the playlist curator explicitly includes them and bios make the connection clear (Duke Ellington ↔ Strayhorn, Louis Armstrong ↔ Earl Hines duet, Dr. Lonnie Smith ↔ George Benson apprenticeship, etc.).
- **Lee Morgan dropped.** Only playlist appearance was the studio-chatter track "Warm-Up / Dialogue Between Lee Morgan And Rudy Van Gelder" — not a song. Skipped per stopping-rule interpretation (one song *and/or* album per unique artist; studio chatter doesn't qualify).
- **One-batch approval for the playlist round.** SKILL says 5–10 per batch; the playlist round wrote 46 cards in one batch because Alec had already approved the scope and the per-artist mapping was straightforward. Worth a small SKILL note: "batch ceiling can be relaxed when the candidate→card mapping is mechanical, not discretionary."

---

## Skill-bug backlog (carry-forward) — UPDATED

1. ~~`write_card.py` `repo_root` inference wrong in worktrees~~ — fixed in `bdb7c95`.
2. **No "add free-text body addendum" op** — still queued. Consider during Track J.
3. **Spotify `ALL_CONTENT_LICENSOR_RESTRICTED` user-facing message** — minor copy fix, still queued.
4. **`add-edge` relationship verb taxonomy** — defer to Phase 3.
5. **`retrieve-spotify-album` foundation skill** — **NEW, concrete blocker for album-first.** Spotify MCP `search type:track` doesn't return parent-album metadata. Needs a dedicated skill that uses `search type:album` directly, with `release_date` and tracklist included in the response shape. Until this lands, the orchestrator's "album-only default" can't be honored without manual album-URL provision.
6. **`retrieve-spotify-playlist` foundation skill** — **NEW.** Spotify MCP `search` doesn't accept playlist URIs. The workaround used today (scrape `embed/track/<id>` `__NEXT_DATA__`) requires rate-limit retries and 12 parallel workers. A proper skill should accept a playlist URL and either use the Spotify Web API (with bearer token) or robustly handle the embed-page scrape with backoff built in.
7. **`add-node` slug-collision disambiguator produces ugly slugs** (e.g. `liberty-avenue-stroll-note` when a track and a note share the human-readable name). Suggest a smarter fallback: ask for an alternative human name, or strip a trailing common-noun token before appending `-<type>`. Today's workaround was manual rename + body fix.
8. **Lint validates link integrity but not slug spelling.** The pre-existing `errol-garner` typo lived for sessions without detection. Worth a stretch goal: a slug-spell-check lint pass against Wikipedia titles or a project-level slug allowlist.

---

## Files written this session (top-level)

| File | Action |
|---|---|
| `graphs/pittsburgh-jazz/cards/person-*.md` ×24 | created (10 from Wikipedia round, 14 from playlist round) |
| `graphs/pittsburgh-jazz/cards/group-*.md` ×3 | created (Elevations, Poogie Bell Band, Mack Avenue SuperBand) |
| `graphs/pittsburgh-jazz/cards/track-*.md` ×38 | created (10 from Wikipedia round, 28 from playlist round) |
| `graphs/pittsburgh-jazz/cards/note-liberty-avenue.md` | created |
| `graphs/pittsburgh-jazz/cards/person-erroll-garner.md` | renamed from `person-errol-garner.md` + 6 backlink updates |
| `graphs/bowie-covers/cards/*` ×10 | created (parallel session — 5 persons/group + 5 song/track pairs) |
| `docs/plans/sprint_05172026-phase2/session_prompts/_pm-continuation.md` | **this file — overwritten** |

All cards lint-clean. 126 pytest pass.

---

## Key files for next session

| File | Role |
|---|---|
| `docs/plans/sprint_05172026-phase2/test_registry.md` | Pass/fail gate — sign M14 next; J/M still outstanding |
| `docs/plans/sprint_05172026-phase2/session_prompts/J-suggestion-intake.md` | Ready-to-run starter for Track J |
| `lib/resources.py` + `.claude/skills/retrieve-wikipedia-category/` + `.claude/skills/expand-graph/SKILL.md` | Track L deliverables on main; reference for the next two foundation skills (album + playlist) |
| `app.py` | Running from main repo; reads `graphs/` per-request — no restart needed after `bdb7c95` |
| `tools/lint_graphs.py` | Always green — run before any commit |
