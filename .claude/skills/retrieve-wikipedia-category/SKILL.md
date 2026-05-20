---
name: retrieve-wikipedia-category
description: Look up the member pages of a Wikipedia Category via the MediaWiki API. Use whenever a skill or user needs a list of candidate titles seeded from a Wikipedia category page — e.g., "list every song in Category:Songs_written_by_David_Bowie", or as a candidate-discovery source for `expand-graph`. Never scrapes HTML and never guesses titles from training data.
triggers:
  - "retrieve wikipedia category [url]"
  - "list members of [category url]"
  - "wikipedia category [url]"
  - "fetch wikipedia category"
  - "get members of [Category:...]"
  - Programmatic: invoked by `expand-graph` when a graph's `resources:` includes a `type: wikipedia-category` entry.
---

# Skill: retrieve-wikipedia-category

Given a Wikipedia Category URL, return the list of pages currently filed under that category. This is the **Wikipedia twin** of `retrieve-spotify-song`: a single-source-of-truth foundation skill for any music-graphs flow that uses Wikipedia categories to seed candidate nodes.

## Input

A canonical Wikipedia Category URL:

```
https://en.wikipedia.org/wiki/Category:Songs_written_by_David_Bowie
https://en.wikipedia.org/wiki/Category:Jazz_musicians_from_Pittsburgh
```

The URL **must** be a `Category:` page on `en.wikipedia.org`. Other-language Wikipedias, non-category pages, and shortened forms (`/wiki/Songs_written_by_David_Bowie`) are rejected.

## Output

A list of dicts, one per category member:

```python
[
    {"title": "Heroes (David Bowie song)",
     "url":   "https://en.wikipedia.org/wiki/Heroes_(David_Bowie_song)",
     "pageid": 12345,
     "ns": 0},
    ...
]
```

- `title` is the page's human-readable title.
- `url` is the canonical `en.wikipedia.org/wiki/<title>` URL with spaces converted to underscores.
- `pageid` is the MediaWiki numeric page ID (useful for dedupe across renames).
- `ns` is the namespace (0 = main article; subcategories come back as ns=14 — callers usually filter these out).

The list is the **full membership** of the category, paginated transparently across multiple API calls using the `continue` parameter.

## Fail-loud contract (LOCKED)

This skill never substitutes its own knowledge for the API response. Same rule as `retrieve-spotify-song`: if the API call fails, errors, or returns an unexpected shape, the skill returns an explicit error string, **not** a fabricated list.

| Failure | Response |
|---|---|
| URL is not on `en.wikipedia.org` | `INVALID_URL: only en.wikipedia.org category pages are supported (got: <url>)` |
| URL is not a `Category:` page | `INVALID_URL: not a Wikipedia category URL (got: <url>)` |
| HTTP error (4xx/5xx, timeout, DNS fail) | `WIKIPEDIA_ERROR: <error message>` |
| API returns `error` field (bad category, etc.) | `WIKIPEDIA_ERROR: <api error code> — <api error info>` |
| Category exists but has zero members | `NOT_FOUND: category <name> has no members` |

If the caller is a programmatic skill (e.g., `expand-graph`), it propagates the error rather than continuing.

## Workflow

### Step 1 — Validate the URL

The URL must match: `https?://en\.wikipedia\.org/wiki/Category:.+`. Strip query parameters and fragments. Reject anything else with `INVALID_URL`.

### Step 2 — Call the MediaWiki API

Endpoint:

```
https://en.wikipedia.org/w/api.php
  ?action=query
  &list=categorymembers
  &cmtitle=Category:<urldecoded title>
  &cmlimit=200
  &format=json
  &cmprop=ids|title|type
```

Paginate via the `continue.cmcontinue` cursor. Stop when `continue` is absent.

### Step 3 — Normalize and return

For each member:
- Build the URL: `https://en.wikipedia.org/wiki/` + `title.replace(" ", "_")` (URL-encode any non-ASCII).
- Keep `pageid` and `ns`.
- Drop nothing — let the caller decide whether to filter subcategories (`ns=14`) or files (`ns=6`).

Return the full list.

## Helper

`scripts/fetch_category.py` exposes:

```python
from scripts.fetch_category import fetch_category_members, validate_category_url

# pure validation, no network
validate_category_url("https://en.wikipedia.org/wiki/Category:Songs_written_by_David_Bowie")
# → "Category:Songs_written_by_David_Bowie"

# full members, paginated; fetch_fn is the network seam (defaults to urllib)
members = fetch_category_members(
    "https://en.wikipedia.org/wiki/Category:Songs_written_by_David_Bowie",
    fetch_fn=None,  # tests inject a closure that returns canned JSON
)
```

`fetch_fn` is the test seam: pass a callable `(url, params) -> dict` that returns the API JSON for each page, so the test suite never touches the network.

## Smoke test

A live lookup for `Category:Songs_written_by_David_Bowie` should return ≥100 members (the category is large) with `"Heroes (David Bowie song)"` among them. If a live call returns fewer than 10 members or omits `"Heroes ..."`, surface the result and stop — something is wrong with the API path.

Tests at `tests/test_retrieve_wikipedia_category.py` cover URL validation, pagination via injected `fetch_fn`, fail-loud on HTTP error, and rejection of empty categories.

## Integration notes for other skills

- **`expand-graph`** calls this skill in Phase 1 (planning) to probe a graph's `resources:` for candidate yield, and in Phase 2 (knowledge retrieval) as a seed list for the research subagent.
- This skill is **read-only**. It does not write cards, frontmatter, or graph state.
- The caller is responsible for dedupe against existing graph slugs — this skill returns full category membership every time.

## Out of scope

- Only `en.wikipedia.org` is supported. Other Wikipedias are out of scope for Phase 2.5.
- No category-tree traversal. Subcategories are returned with `ns=14` but their members are not recursively fetched. If the caller wants subcategory members, it calls this skill again with each subcategory URL.
- No HTML scraping. The API is the only sanctioned data source.
- No write-back to Wikipedia or any other system.
