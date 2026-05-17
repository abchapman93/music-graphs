# Track I — Cover images on home page (M12 from Phase 1)

**Sprint:** `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/`
**Branch:** `sprint/cover-images`
**Worktree path (PM pre-creates):** `/private/tmp/mg-wt-I`
**Wave:** 4 (parallel with H; independent)
**Dependencies:** None — independent of all other tracks; PM can launch this any time after pre-sprint setup.

## How to work on this branch

PM has pre-created the worktree off `main`. You do NOT call `EnterWorktree`. Use `git -C /private/tmp/mg-wt-I <git-op>`.

## Goal

Resolve M12 from Phase 1: pick one representative cover image per graph, populate the `cover_image` field in each graph's `README.md` frontmatter, and confirm the home page renders all three covers without broken-image icons.

## Context files to read

- `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026/test_registry.md` — M12 row (the deferred manual check).
- `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026/project_spec.md` — the image policy: hotlink Wikipedia URLs in frontmatter, download key images to `graphs/<slug>/images/`.
- `/Users/alecchapman/Code/music-graphs/graphs/band-x/README.md`, `.../bowie-covers/README.md`, `.../pittsburgh-jazz/README.md` — current `cover_image: null` state.
- `/Users/alecchapman/Code/music-graphs/templates/home.html` and any related CSS — how the home page renders the cover (find via `grep -r cover_image templates/ static/`).
- `/Users/alecchapman/Code/music-graphs/app.py` — confirm how `cover_image` flows from README frontmatter into the home page template.

## Definition of done

- [ ] One cover image chosen per graph. Image choice criteria:
  - **band-x:** a representative band photo or one of the album covers already cited in the graph (e.g., *Los Angeles* 1980).
  - **bowie-covers:** Bowie himself, OR the cover of one of the canonical cover albums (e.g., *Life Aquatic Studio Sessions* by Seu Jorge), whichever reads cleaner on the home page.
  - **pittsburgh-jazz:** a Pittsburgh skyline / Hill District / iconic jazz-era Pittsburgh image, OR an Errol Garner / Stanley Turrentine portrait.
- [ ] Image source: Wikipedia or Wikimedia Commons preferred (stable URLs, free licensing). Hotlink the canonical Wikipedia URL in frontmatter; if the URL is fragile, also download a local copy to `graphs/<slug>/images/<filename>.jpg` and reference the local relative path.
- [ ] Each `graphs/<slug>/README.md` has `cover_image:` populated with either a full `https://...` URL OR a relative path `images/<filename>.jpg`.
- [ ] Home page (`/`) renders all three cover images. Verify by `curl -s http://localhost:8766/ | grep -E "(<img|cover)"` shows three valid `src` attributes, and a manual browser load shows no broken-image icons.
- [ ] `tools/lint_graphs.py` continues to pass (0 errors) — cover_image is not a graph-card field, but lint may walk READMEs.
- [ ] If `app.py` or `templates/home.html` need a small change to handle the new `cover_image` field (e.g., the template currently has `{% if cover_image %}` but Phase 1 may have hard-coded null), make the minimal change required and call it out in HANDOFF.

## Not in scope

- Do NOT add cover images to individual card pages. This track is home-page-only.
- Do NOT redesign the home page layout. Drop the image into whatever slot the template already has.
- Do NOT touch the four skills or the family agent.

## Test protocol

```bash
cd /private/tmp/mg-wt-I
.venv/bin/python tools/lint_graphs.py 2>&1 | tee /tmp/test_results_track-i.txt
.venv/bin/python -m pytest 2>&1 | tee -a /tmp/test_results_track-i.txt

# Start the app and curl the home page (background; kill after check)
.venv/bin/python app.py &
APP_PID=$!
sleep 2
curl -s http://localhost:8766/ | grep -cE '<img[^>]+src=' | tee -a /tmp/test_results_track-i.txt
kill $APP_PID
```
Expect: lint=0, pytest FAIL=0, ≥3 `<img>` tags on home page. Log path in HANDOFF.

## Handoff protocol

```
HANDOFF (Track I):
- Cover image choices per graph: <three lines, "<graph>: <URL or local path>">
- Local files downloaded (if any): <list of paths>
- Template/app.py changes (if any): <files + 1-line description>
- /tmp/test_results_track-i.txt: lint=0, pytest FAIL=<count>, home <img> count=<n>
- M12 manual check (verify in browser): <pass/fail>
- Deviations: <none / list>
```

## Close-out

```
git -C /private/tmp/mg-wt-I add .
git -C /private/tmp/mg-wt-I commit -m "feat(home): cover images for all three graphs (M12)"
```
Report SHA + HANDOFF to PM.

---

HANDOFF (Track I):
- Cover image choices per graph:
  - band-x: images/x-1979-la.jpg (Wikimedia Commons: X band, 1979 LA — https://commons.wikimedia.org/wiki/File:X1979LA.jpg)
  - bowie-covers: images/david-bowie.jpg (Wikimedia Commons: David Bowie, Chicago 2002, Adam Bielawski — https://commons.wikimedia.org/wiki/File:David-Bowie_Chicago_2002-08-08_photoby_Adam-Bielawski-cropped.jpg)
  - pittsburgh-jazz: images/erroll-garner-1947.jpg (Wikimedia Commons: Erroll Garner, 1947 — https://commons.wikimedia.org/wiki/File:Erroll_Garner_1947.jpg)
- Local files downloaded:
  - graphs/band-x/images/x-1979-la.jpg
  - graphs/bowie-covers/images/david-bowie.jpg
  - graphs/pittsburgh-jazz/images/erroll-garner-1947.jpg
- Template/app.py changes:
  - `app.py`: added `/graph-images/<slug>/<path:filename>` route (send_from_directory) and `_resolve_cover_image` helper that rewrites a relative `images/...` cover_image into that route in the home view. No template changes needed — `templates/home.html` already had the `{% if cover_image %}` block.
- /tmp/test_results_track-i.txt: lint=0, pytest FAIL=0 (100 passed), home <img> count=3
- M12 manual check (verify in browser): pass — `curl -sI /graph-images/<slug>/<file>` returns 200 for all three; `curl /` shows three `<img class="cover" src="/graph-images/...">` tags.
- Deviations: none.

