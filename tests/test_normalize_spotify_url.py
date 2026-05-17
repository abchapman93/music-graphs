"""Tests for the retrieve-spotify-song skill's URL normalizer."""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    REPO_ROOT
    / ".claude"
    / "skills"
    / "retrieve-spotify-song"
    / "scripts"
    / "normalize_url.py"
)

_spec = importlib.util.spec_from_file_location("normalize_url", HELPER_PATH)
_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_mod)
normalize_spotify_url = _mod.normalize_spotify_url

CANONICAL = "https://open.spotify.com/album/2At5ShihdUNDdc33Ztp7RX"
TRACK_CANONICAL = "https://open.spotify.com/track/7qiZfU4dY1lWllzX7mPBI3"


def test_already_canonical():
    assert normalize_spotify_url(CANONICAL) == CANONICAL


def test_strips_query_params():
    url = CANONICAL + "?si=abc123&utm_source=copy-link"
    assert normalize_spotify_url(url) == CANONICAL


def test_strips_fragment():
    url = CANONICAL + "#play"
    assert normalize_spotify_url(url) == CANONICAL


def test_strips_query_and_fragment_together():
    url = CANONICAL + "?si=xyz#play"
    assert normalize_spotify_url(url) == CANONICAL


def test_strips_locale_prefix():
    url = "https://open.spotify.com/intl-fr/album/2At5ShihdUNDdc33Ztp7RX?si=abc"
    assert normalize_spotify_url(url) == CANONICAL


def test_http_upgraded_to_https():
    url = "http://open.spotify.com/track/7qiZfU4dY1lWllzX7mPBI3"
    assert normalize_spotify_url(url) == TRACK_CANONICAL


def test_spotify_uri_form():
    assert (
        normalize_spotify_url("spotify:album:2At5ShihdUNDdc33Ztp7RX") == CANONICAL
    )


def test_non_spotify_url_returns_none():
    assert normalize_spotify_url("https://example.com/album/abc") is None
    assert normalize_spotify_url("https://www.youtube.com/watch?v=abc") is None


def test_invalid_id_returns_none():
    assert normalize_spotify_url("https://open.spotify.com/album/tooshort") is None


def test_invalid_type_returns_none():
    assert (
        normalize_spotify_url(
            "https://open.spotify.com/bogus/2At5ShihdUNDdc33Ztp7RX"
        )
        is None
    )


def test_empty_and_non_string_returns_none():
    assert normalize_spotify_url("") is None
    assert normalize_spotify_url("   ") is None
    assert normalize_spotify_url(None) is None  # type: ignore[arg-type]
