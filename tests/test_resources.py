"""Tests for `lib/resources.py`.

Covers:
    - parse_resources returns [] when README has no `resources:` field
    - parse_resources returns Resource entries with type/url/label
    - unknown `type:` value raises UnknownResourceTypeError
    - missing `url` or `type` raises ValueError
    - non-list `resources:` raises ValueError
    - RESOLVERS maps known types correctly
    - Resource.resolver returns the right skill name
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from lib.resources import (  # noqa: E402
    RESOLVERS,
    Resource,
    UnknownResourceTypeError,
    parse_resources,
)


def _write_readme(tmp_path: Path, frontmatter_yaml: str) -> Path:
    readme = tmp_path / "README.md"
    readme.write_text(f"---\n{frontmatter_yaml}\n---\n\nbody\n", encoding="utf-8")
    return readme


def test_parse_resources_empty_when_field_absent(tmp_path):
    readme = _write_readme(tmp_path, 'name: "Foo"\ndescription: "bar"')
    assert parse_resources(readme) == []


def test_parse_resources_returns_typed_entries(tmp_path):
    yaml = """name: "Bowie Covers"
resources:
  - type: wikipedia-category
    url: https://en.wikipedia.org/wiki/Category:Songs_written_by_David_Bowie
    label: "Bowie songs"
  - type: website
    url: https://example.com/bowie-covers
"""
    readme = _write_readme(tmp_path, yaml.strip())
    out = parse_resources(readme)
    assert len(out) == 2
    assert out[0] == Resource(
        type="wikipedia-category",
        url="https://en.wikipedia.org/wiki/Category:Songs_written_by_David_Bowie",
        label="Bowie songs",
    )
    assert out[1].label is None
    assert out[1].type == "website"


def test_parse_resources_resolver_dispatch():
    r = Resource(type="wikipedia-category", url="https://x")
    assert r.resolver == "retrieve-wikipedia-category"
    assert Resource(type="website", url="https://x").resolver is None


def test_parse_resources_unknown_type_fails(tmp_path):
    yaml = """name: "Foo"
resources:
  - type: not-a-real-type
    url: https://example.com
"""
    readme = _write_readme(tmp_path, yaml.strip())
    with pytest.raises(UnknownResourceTypeError):
        parse_resources(readme)


def test_parse_resources_missing_url_fails(tmp_path):
    yaml = """name: "Foo"
resources:
  - type: wikipedia-category
"""
    readme = _write_readme(tmp_path, yaml.strip())
    with pytest.raises(ValueError, match="missing `url`"):
        parse_resources(readme)


def test_parse_resources_missing_type_fails(tmp_path):
    yaml = """name: "Foo"
resources:
  - url: https://example.com
"""
    readme = _write_readme(tmp_path, yaml.strip())
    with pytest.raises(ValueError, match="missing `type`"):
        parse_resources(readme)


def test_parse_resources_non_list_fails(tmp_path):
    yaml = """name: "Foo"
resources: "https://example.com"
"""
    readme = _write_readme(tmp_path, yaml.strip())
    with pytest.raises(ValueError, match="must be a list"):
        parse_resources(readme)


def test_parse_resources_missing_readme_fails(tmp_path):
    with pytest.raises(FileNotFoundError):
        parse_resources(tmp_path / "no-such.md")


def test_known_resolver_types():
    # Surface this map in a test so changes here become an explicit signal.
    assert "wikipedia-category" in RESOLVERS
    assert RESOLVERS["wikipedia-category"] == "retrieve-wikipedia-category"
    assert "website" in RESOLVERS
    assert RESOLVERS["website"] is None
