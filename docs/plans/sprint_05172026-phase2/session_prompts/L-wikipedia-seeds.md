# Track L — Wikipedia category as seed source

**Sprint:** sprint_05172026-phase2 (Phase 2.5)
**Worktree:** `/private/tmp/mg-wt-L` on branch `sprint/wikipedia-seeds`
**Acceptance gates:** L1, L2, L3 in `test_registry.md`; M14 manual.

## What to build

1. **`skills/retrieve-wikipedia-category/` skill.** Mirror `skills/retrieve-spotify-song/` structure.
   - **Input:** Wikipedia Category URL (e.g., `https://en.wikipedia.org/wiki/Category:Songs_written_by_David_Bowie`).
   - **Output:** `[{title, url}, ...]` — all member pages, paginated via `continue` parameter if >200.
   - **Implementation:** Wikipedia REST API or `?action=query&list=categorymembers&cmtitle=Category:...&format=json`. Prefer the API over HTML scraping.
   - **Fail-loud** on 404, non-category URL, or empty category.
   - **Tests:** mock the HTTP response; verify pagination and error handling.

2. **`expand-graph` enhancement.**
   - Read `seed_sources:` from the graph root card frontmatter.
   - For each Wikipedia URL in `seed_sources`, call `retrieve-wikipedia-category` and collect member titles.
   - Dedupe against existing graph slugs (compare normalized title → slug).
   - Surface top N (default 10) new candidates **alongside** existing Spotify-MCP candidates — don't replace, augment. Show source ("via Wikipedia: Category:X") so Alec knows which is which.
   - Existing `expand-graph` behavior unchanged when `seed_sources` is absent.

3. **Update graph root cards** with `seed_sources:`:
   - `graphs/bowie-covers/cards/README.md`: add `Category:Songs_written_by_David_Bowie`
   - `graphs/pittsburgh-jazz/cards/README.md`: add `Category:Jazz_musicians_from_Pittsburgh`
   - `graphs/band-x/cards/README.md`: skip unless Alec provides a category URL.

4. **Document the seed-source pattern** in `docs/skills-overview.md` (or wherever the skill catalog is). Add a "Creating a new graph" note that says: start with a Wikipedia category URL in `seed_sources` and let `expand-graph` drive the initial node population.

## Done when

- All L-row checks pass.
- 100+ pytest pass, lint clean.
- Alec runs `expand-graph` on bowie-covers and sees Wikipedia-sourced candidates he hasn't already added.
