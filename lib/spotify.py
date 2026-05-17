"""Spotify URL → embed URL helper. Pure transformation, no network calls."""

from __future__ import annotations

from urllib.parse import urlparse

SPOTIFY_KINDS: frozenset[str] = frozenset(
    {"track", "album", "playlist", "artist", "episode", "show"}
)


def spotify_embed_url(url: str | None) -> str | None:
    """Convert an open.spotify.com resource URL to its embed URL.

    Returns None on any malformed or non-Spotify input. Never raises.
    """
    if not url or not isinstance(url, str):
        return None
    try:
        parsed = urlparse(url)
    except (ValueError, AttributeError):
        return None
    if parsed.scheme not in ("http", "https"):
        return None
    if parsed.netloc != "open.spotify.com":
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) != 2:
        return None
    kind, item_id = parts
    if kind not in SPOTIFY_KINDS or not item_id:
        return None
    return f"https://open.spotify.com/embed/{kind}/{item_id}"
