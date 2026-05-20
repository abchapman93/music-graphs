"""resources.py — Parse graph-level ``resources:`` declarations.

A graph's root README may declare external resources used by the
``expand-graph`` skill for candidate discovery, e.g.:

```yaml
---
name: "Bowie Covers"
resources:
  - type: wikipedia-category
    url: https://en.wikipedia.org/wiki/Category:Songs_written_by_David_Bowie
    label: "Bowie songs"
---
```

Each entry maps to a resolver (skill) via ``RESOLVERS``. Unknown types
fail loud so typos surface immediately instead of silently dropping a
resource.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import frontmatter


# Type -> resolver skill name. ``None`` means the type is recognized but
# has no automated resolver yet (e.g. ``website`` is a free-text seed
# the planning phase surfaces to the model directly).
RESOLVERS: dict[str, Optional[str]] = {
    "wikipedia-category": "retrieve-wikipedia-category",
    "spotify-playlist": "retrieve-spotify-playlist",  # resolver deferred
    "website": None,
}


@dataclass
class Resource:
    type: str
    url: str
    label: Optional[str] = None

    @property
    def resolver(self) -> Optional[str]:
        return RESOLVERS.get(self.type)


class UnknownResourceTypeError(ValueError):
    """Raised when a resource entry uses a ``type:`` not in RESOLVERS."""


def parse_resources(readme_path: Path | str) -> list[Resource]:
    """Read a graph root README and return its declared resources.

    Returns an empty list if the README has no ``resources:`` field.
    Raises ``FileNotFoundError`` if the README is missing,
    ``UnknownResourceTypeError`` if a ``type:`` is not in ``RESOLVERS``,
    and ``ValueError`` for malformed entries (missing url, non-list, etc.).
    """
    path = Path(readme_path)
    if not path.exists():
        raise FileNotFoundError(f"README not found: {path}")

    post = frontmatter.load(str(path))
    raw = post.metadata.get("resources")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(
            f"{path}: `resources` must be a list, got {type(raw).__name__}"
        )

    out: list[Resource] = []
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise ValueError(
                f"{path}: resources[{i}] must be a mapping, got "
                f"{type(entry).__name__}"
            )
        rtype = entry.get("type")
        url = entry.get("url")
        label = entry.get("label")
        if not rtype:
            raise ValueError(f"{path}: resources[{i}] missing `type`")
        if not url:
            raise ValueError(f"{path}: resources[{i}] missing `url`")
        if rtype not in RESOLVERS:
            raise UnknownResourceTypeError(
                f"{path}: resources[{i}] unknown type {rtype!r}. "
                f"Known types: {sorted(RESOLVERS)}"
            )
        out.append(Resource(type=rtype, url=url, label=label))
    return out
