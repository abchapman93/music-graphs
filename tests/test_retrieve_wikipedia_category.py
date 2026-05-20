"""Tests for the `retrieve-wikipedia-category` skill helper.

Covers:
    - validate_category_url accepts canonical Category URLs
    - validate_category_url rejects non-Wikipedia URLs, non-Category pages
    - fetch_category_members paginates via `continue` and dedupes pageids
    - fetch_category_members maps title -> canonical URL
    - HTTP error from fetch_fn surfaces as WikipediaError
    - API `error` field surfaces as WikipediaError
    - Empty category surfaces as NOT_FOUND (WikipediaError)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = (
    REPO_ROOT
    / ".claude"
    / "skills"
    / "retrieve-wikipedia-category"
    / "scripts"
)
sys.path.insert(0, str(SCRIPTS))

from fetch_category import (  # noqa: E402
    InvalidCategoryURLError,
    WikipediaError,
    fetch_category_members,
    validate_category_url,
)


# ---------- URL validation ----------


def test_validate_category_url_accepts_canonical():
    title = validate_category_url(
        "https://en.wikipedia.org/wiki/Category:Songs_written_by_David_Bowie"
    )
    assert title == "Category:Songs_written_by_David_Bowie"


def test_validate_category_url_accepts_http_and_trailing_slash():
    assert (
        validate_category_url(
            "http://en.wikipedia.org/wiki/Category:Jazz_musicians_from_Pittsburgh/"
        )
        == "Category:Jazz_musicians_from_Pittsburgh"
    )


def test_validate_category_url_strips_query_and_fragment():
    assert (
        validate_category_url(
            "https://en.wikipedia.org/wiki/Category:Foo?action=edit#section"
        )
        == "Category:Foo"
    )


def test_validate_category_url_rejects_other_wiki():
    with pytest.raises(InvalidCategoryURLError):
        validate_category_url(
            "https://de.wikipedia.org/wiki/Category:Lieder_von_David_Bowie"
        )


def test_validate_category_url_rejects_non_category():
    with pytest.raises(InvalidCategoryURLError):
        validate_category_url(
            "https://en.wikipedia.org/wiki/David_Bowie"
        )


def test_validate_category_url_rejects_garbage():
    with pytest.raises(InvalidCategoryURLError):
        validate_category_url("not a url")


# ---------- pagination ----------


def _make_paginated_fetch(pages):
    """Build a fetch_fn closure that returns canned pages in sequence.

    Each entry of ``pages`` is a dict matching MediaWiki API JSON.
    """
    iterator = iter(pages)

    def fetch_fn(url, params):
        try:
            return next(iterator)
        except StopIteration:
            raise AssertionError("fetch_fn called more times than pages provided")

    return fetch_fn


def test_fetch_paginates_via_continue_and_dedupes():
    pages = [
        {
            "query": {
                "categorymembers": [
                    {"pageid": 1, "ns": 0, "title": "Heroes (David Bowie song)"},
                    {"pageid": 2, "ns": 0, "title": "Life on Mars?"},
                ]
            },
            "continue": {"cmcontinue": "page||3"},
        },
        {
            "query": {
                "categorymembers": [
                    # pageid 2 is a duplicate across pages; must be dropped.
                    {"pageid": 2, "ns": 0, "title": "Life on Mars?"},
                    {"pageid": 3, "ns": 0, "title": "Space Oddity"},
                ]
            },
        },
    ]
    out = fetch_category_members(
        "https://en.wikipedia.org/wiki/Category:Songs_written_by_David_Bowie",
        fetch_fn=_make_paginated_fetch(pages),
    )
    assert [m["title"] for m in out] == [
        "Heroes (David Bowie song)",
        "Life on Mars?",
        "Space Oddity",
    ]
    assert [m["pageid"] for m in out] == [1, 2, 3]


def test_fetch_maps_title_to_canonical_url():
    pages = [
        {
            "query": {
                "categorymembers": [
                    {"pageid": 1, "ns": 0, "title": "Heroes (David Bowie song)"},
                ]
            },
        }
    ]
    out = fetch_category_members(
        "https://en.wikipedia.org/wiki/Category:Songs_written_by_David_Bowie",
        fetch_fn=_make_paginated_fetch(pages),
    )
    assert out[0]["url"] == "https://en.wikipedia.org/wiki/Heroes_(David_Bowie_song)"


# ---------- failure modes ----------


def test_fetch_fail_loud_on_http_error():
    def fetch_fn(url, params):
        raise WikipediaError("WIKIPEDIA_ERROR: HTTP 503")

    with pytest.raises(WikipediaError, match="WIKIPEDIA_ERROR"):
        fetch_category_members(
            "https://en.wikipedia.org/wiki/Category:Foo",
            fetch_fn=fetch_fn,
        )


def test_fetch_fail_loud_on_api_error_field():
    pages = [
        {
            "error": {
                "code": "invalidcategory",
                "info": "The category title is invalid.",
            }
        }
    ]
    with pytest.raises(WikipediaError, match="invalidcategory"):
        fetch_category_members(
            "https://en.wikipedia.org/wiki/Category:Foo",
            fetch_fn=_make_paginated_fetch(pages),
        )


def test_fetch_fail_loud_on_empty_category():
    pages = [{"query": {"categorymembers": []}}]
    with pytest.raises(WikipediaError, match="NOT_FOUND"):
        fetch_category_members(
            "https://en.wikipedia.org/wiki/Category:Empty",
            fetch_fn=_make_paginated_fetch(pages),
        )


def test_fetch_fail_loud_on_bad_shape():
    def fetch_fn(url, params):
        return "totally not a dict"

    with pytest.raises(WikipediaError, match="unexpected response shape"):
        fetch_category_members(
            "https://en.wikipedia.org/wiki/Category:Foo",
            fetch_fn=fetch_fn,
        )
