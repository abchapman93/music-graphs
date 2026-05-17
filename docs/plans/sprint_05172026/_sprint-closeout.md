# Sprint Close-out — sprint_05172026 (music-graphs Phase 1)

**Closed:** 2026-05-17
**Main HEAD at close:** `84f8844`
**Tag:** `v0.1-phase1-demo` (applied on close)

## Final status

- **Automated checks:** 18/18 ✅
- **Manual checks:** 11/12 ✅ — M12 (cover images on home page) deferred to next sprint
- **Tests:** 51 passed, 0 failed
- **Lint:** 0 errors across all 3 graph folders
- **Graphs delivered:** 3 (pittsburgh-jazz 16n/37e, band-x 13n/49e, bowie-covers 13n/28e — 42 cards total)
- **Spotify URLs:** all 27 surviving URLs verified via Spotify MCP (1 removed as unfindable: Nirvana MTV Unplugged in New York)

## Deferred to Phase 2

### Fixups from this sprint
1. **M12 — cover images on home page.** All 3 graph READMEs have `cover_image: null`. Per the spec's image policy, hotlink Wikipedia URLs in frontmatter and download key images to `graphs/<slug>/images/`. Small polish gap.
2. **Troy/Tony Gilkyson naming mismatch in band-x.** `graphs/band-x/cards/person-troy-gilkyson.md` has filename slug "troy-gilkyson" (from plan spec) but `name: "Tony Gilkyson"` (actual X guitarist 1986–1995). Decide: rename file to `person-tony-gilkyson.md` (recommended) OR change `name:` field. The graph's wikilinks will need to follow.
3. **One missing Spotify URL.** `graphs/bowie-covers/cards/album-unplugged-in-new-york.md` has no `spotify_url` line — Nirvana's MTV Unplugged in New York could not be surfaced via the Spotify MCP search. Worth a manual lookup (it does exist on Spotify) or accept the silent-no-embed state.

### New scope requested
4. **Reusable skills.** Build skills for the recurring graph-building tasks: `add-node` (create a card with proper frontmatter from a name+type+graph), `retrieve-spotify-song` (look up + return canonical Spotify URL given an artist/album/track name), and likely an `add-edge`/`add-wikilink` helper. These let Alec (and others) build out graphs without hand-editing YAML.
5. **Specialized Claude agent for non-technical collaborators.** Target audience: Alec's family. They should be able to clone the repo, run Claude Code in it, and converse naturally with a graph-building agent that handles the markdown/frontmatter mechanics, suggests wikilinks to existing nodes, finds Spotify links, etc. Should hide the "you're editing markdown files in `graphs/<slug>/cards/`" mechanics behind conversational UX.
6. **Expand album/song selection.** Alec will provide specific success criteria at sprint kickoff — likely more graphs and/or denser coverage within existing graphs.

## Architecture state for next sprint

- Card schema, module signatures, route shapes all locked in `project_spec.md` and load-bearing — Phase 2 builds on top, not around.
- Card slug derivation gotcha (filename-after-first-hyphen) is the main API quirk callers must respect.
- `parse_card()` returns `card["wikilinks"]` already deduped from frontmatter + body; consumers must not re-extract.
- `app.py` attaches `spotify_embed_url` at request time, keeping `lib/cards.py` free of a `lib/spotify` dependency. Phase 2 should preserve this seam.
- `tools/lint_graphs.py` (Track F deliverable) is the canonical pre-commit check for graph content. Run it before merging any content-only PR.

## What worked

- Pre-creating worktrees with `git worktree add` + telling sub-agents explicit absolute paths + `git -C <path>` was bulletproof after the first attempt failed. Original strategy of "sub-agents call `EnterWorktree`" did not work — they appear to lack the tool and silently fell back to operating in the shared main repo, stepping on each other.
- Dependency-ordered merge (B → A → C, then D, then E, then G + F) avoided rebase conflicts almost entirely. Only F needed a small rebase against G.
- The `_pm-continuation.md` doc from the previous PM session was the highest-fidelity re-entry point. Every Sprint Manager handoff should produce one.

## What to do differently next time

- Sub-agent prompts should explicitly forbid `EnterWorktree` AND give absolute paths up front. Don't trust agents to discover the right worktree on their own.
- For content tasks where the agent will iterate over many files (Track F's 42 cards, the Spotify URL fixup), say explicitly "process EVERY file in the inventory list" — the Spotify fixup agent silently skipped a whole folder on the first pass.
- For any task involving external-data lookup (Spotify URLs, image URLs, citations), require an MCP/web tool. Don't accept training-data guesses.
