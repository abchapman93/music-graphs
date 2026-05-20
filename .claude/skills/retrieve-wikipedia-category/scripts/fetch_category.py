"""fetch_category.py — Helper for the ``retrieve-wikipedia-category`` skill.

Fetches the full membership of an English Wikipedia category via the
MediaWiki API (``action=query&list=categorymembers``). Paginates via the
``continue`` cursor.

The ``fetch_fn`` parameter is the network seam: callers (tests) can
inject a callable ``(url, params) -> dict`` that returns canned API
JSON, so the test suite never touches the network. The default uses
``urllib.request``.

Failures raise ``WikipediaError`` with a tagged message matching the
fail-loud contract in ``SKILL.md``.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from typing import Callable, Optional


API_ENDPOINT = "https://en.wikipedia.org/w/api.php"


# Accept http or https, optional trailing slash, ignore query/fragment.
_CATEGORY_URL_RE = re.compile(
    r"^https?://en\.wikipedia\.org/wiki/(Category:[^?#]+?)/?(?:[?#].*)?$"
)


class WikipediaError(RuntimeError):
    """Wikipedia API or transport-level failure."""


class InvalidCategoryURLError(ValueError):
    """The provided URL is not an en.wikipedia.org Category page."""


FetchFn = Callable[[str, dict], dict]


def validate_category_url(url: str) -> str:
    """Validate ``url`` and return the bare ``Category:Title`` string.

    Strips trailing slash, query, and fragment. Raises
    ``InvalidCategoryURLError`` on any non-en-Wikipedia-Category URL.
    """
    if not isinstance(url, str) or not url.strip():
        raise InvalidCategoryURLError(
            f"INVALID_URL: url must be a non-empty string (got: {url!r})"
        )
    m = _CATEGORY_URL_RE.match(url.strip())
    if not m:
        # Distinguish the two common failure modes for a clearer message.
        if "en.wikipedia.org" not in url:
            raise InvalidCategoryURLError(
                f"INVALID_URL: only en.wikipedia.org category pages are "
                f"supported (got: {url})"
            )
        raise InvalidCategoryURLError(
            f"INVALID_URL: not a Wikipedia category URL (got: {url})"
        )
    title_part = m.group(1)
    # Decode percent-escapes so callers get a human-readable title.
    return urllib.parse.unquote(title_part)


def _default_fetch_fn(url: str, params: dict) -> dict:
    """Default HTTP fetcher using urllib. Returns parsed JSON."""
    qs = urllib.parse.urlencode(params)
    full_url = f"{url}?{qs}"
    req = urllib.request.Request(
        full_url,
        headers={
            # Wikipedia requires a descriptive User-Agent on API calls.
            "User-Agent": "music-graphs/0.2 (https://github.com/; expand-graph skill)"
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read()
    except Exception as exc:
        raise WikipediaError(f"WIKIPEDIA_ERROR: {exc}") from exc
    try:
        return json.loads(body)
    except ValueError as exc:
        raise WikipediaError(f"WIKIPEDIA_ERROR: invalid JSON response: {exc}") from exc


def _title_to_url(title: str) -> str:
    # MediaWiki canonical URLs use underscores for spaces and percent-encode
    # other special characters.
    quoted = urllib.parse.quote(title.replace(" ", "_"), safe=":/_(),.'")
    return f"https://en.wikipedia.org/wiki/{quoted}"


def fetch_category_members(
    url: str,
    *,
    fetch_fn: Optional[FetchFn] = None,
    cmlimit: int = 200,
    max_pages: int = 20,
) -> list[dict]:
    """Fetch all members of a Wikipedia category.

    Returns a list of ``{"title", "url", "pageid", "ns"}`` dicts.
    Paginates via ``continue.cmcontinue`` until exhausted or
    ``max_pages`` is reached (a safety stop; 20 pages * 200 per page =
    4,000 members).

    Raises:
        InvalidCategoryURLError: URL is not a valid en-wiki Category page.
        WikipediaError: HTTP or API failure; or empty category (the
            ``NOT_FOUND`` tag is used in the message).
    """
    title = validate_category_url(url)
    fetch = fetch_fn or _default_fetch_fn

    members: list[dict] = []
    cont: dict = {}
    seen_pageids: set[int] = set()

    for _ in range(max_pages):
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": title,
            "cmlimit": cmlimit,
            "cmprop": "ids|title|type",
            "format": "json",
            "formatversion": "2",
        }
        params.update(cont)
        data = fetch(API_ENDPOINT, params)

        if not isinstance(data, dict):
            raise WikipediaError(
                f"WIKIPEDIA_ERROR: unexpected response shape ({type(data).__name__})"
            )
        if "error" in data:
            err = data["error"]
            code = err.get("code", "unknown")
            info = err.get("info", "no info")
            raise WikipediaError(f"WIKIPEDIA_ERROR: {code} — {info}")

        page = (data.get("query") or {}).get("categorymembers") or []
        for m in page:
            pid = m.get("pageid")
            if pid in seen_pageids:
                continue
            seen_pageids.add(pid)
            members.append(
                {
                    "title": m.get("title"),
                    "url": _title_to_url(m.get("title", "")),
                    "pageid": pid,
                    "ns": m.get("ns", 0),
                }
            )

        cont = data.get("continue") or {}
        if not cont:
            break

    if not members:
        raise WikipediaError(
            f"NOT_FOUND: category {title} has no members"
        )
    return members
