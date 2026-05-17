"""Normalize a Spotify URL to its canonical bare form.

Canonical form: ``https://open.spotify.com/<type>/<id>``

- Strips query strings (e.g., ``?utm_source=copy-link``, ``?si=...``).
- Strips URL fragments (``#...``).
- Accepts ``http://`` and rewrites to ``https://``.
- Accepts the ``spotify:<type>:<id>`` URI form and rewrites to the open.spotify.com URL.
- Returns ``None`` for any URL that is not a recognizable Spotify resource URL.

Recognized resource types: track, album, artist, playlist, episode, show.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

_VALID_TYPES = {"track", "album", "artist", "playlist", "episode", "show"}
_ID_RE = re.compile(r"^[A-Za-z0-9]{22}$")
_URI_RE = re.compile(r"^spotify:(track|album|artist|playlist|episode|show):([A-Za-z0-9]{22})$")


def normalize_spotify_url(url: str) -> str | None:
    """Return the canonical ``https://open.spotify.com/<type>/<id>`` URL, or None.

    Returns None if the input is not a Spotify URL or cannot be parsed.
    """
    if not isinstance(url, str):
        return None
    url = url.strip()
    if not url:
        return None

    # Handle spotify: URI form.
    m = _URI_RE.match(url)
    if m:
        return f"https://open.spotify.com/{m.group(1)}/{m.group(2)}"

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return None
    if parsed.netloc.lower() not in ("open.spotify.com", "play.spotify.com"):
        return None

    # Path like /track/<id> or /intl-xx/track/<id>
    parts = [p for p in parsed.path.split("/") if p]
    # Drop locale prefix like "intl-fr"
    if parts and parts[0].startswith("intl-"):
        parts = parts[1:]
    if len(parts) < 2:
        return None
    rtype, rid = parts[0], parts[1]
    if rtype not in _VALID_TYPES:
        return None
    if not _ID_RE.match(rid):
        return None
    return f"https://open.spotify.com/{rtype}/{rid}"
