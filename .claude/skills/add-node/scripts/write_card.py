"""write_card.py — Helper for the `add-node` skill.

Creates a new card file at ``graphs/<graph>/cards/<type>-<slug>.md`` with valid
YAML frontmatter and a markdown body, then runs ``tools/lint_graphs.py`` over
the graphs root. On lint failure the new file is removed and ``LintError`` is
raised so the caller can surface the failure to the user.

Public API:
    write_card(graph, type, name, *,
               repo_root=None,
               graphs_root=None,
               spotify_url=None,
               canonical_link=None,
               body=None,
               wikilinks=None,
               run_lint=True,
               lint_cmd=None) -> Path

    slugify(name) -> str
    derive_filename(card_type, name, existing_slugs) -> tuple[str, str, bool]
"""
from __future__ import annotations

import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Iterable, Optional, Sequence

import frontmatter


class LintError(RuntimeError):
    """Raised when the post-write lint check fails. The new file has already
    been removed before this is raised."""

    def __init__(self, stdout: str, stderr: str, returncode: int):
        super().__init__(f"lint_graphs.py exited {returncode}")
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


_SLUG_PUNCT_RE = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    """Lowercase ASCII slug. Drops accents, collapses runs of non-alphanum to
    single hyphens, strips leading/trailing hyphens. Mirrors the slug style
    used in existing Phase 1 card filenames.
    """
    if not name:
        raise ValueError("name is empty")
    norm = unicodedata.normalize("NFKD", name)
    norm = norm.encode("ascii", "ignore").decode("ascii").lower()
    slug = _SLUG_PUNCT_RE.sub("-", norm).strip("-")
    if not slug:
        raise ValueError(f"name {name!r} produces empty slug")
    return slug


def _existing_slugs(cards_dir: Path) -> set[str]:
    """Set of slugs (filename-after-first-hyphen) already present in cards_dir."""
    out: set[str] = set()
    if not cards_dir.is_dir():
        return out
    for p in cards_dir.glob("*.md"):
        stem = p.stem
        if "-" in stem:
            out.add(stem.split("-", 1)[1])
        else:
            out.add(stem)
    return out


def derive_filename(
    card_type: str,
    name: str,
    existing_slugs: Iterable[str],
) -> tuple[str, str, bool]:
    """Return ``(filename, slug, disambiguated)``.

    Base filename is ``<type>-<slugify(name)>.md``. If that slug already
    exists in ``existing_slugs``, the slug is disambiguated by appending
    ``-<type>`` (e.g., a ``track`` named "Sugar" colliding with another card
    becomes ``track-sugar-track.md``). If *that* still collides, numeric
    suffixes are appended.
    """
    existing = set(existing_slugs)
    base_slug = slugify(name)
    if base_slug not in existing:
        return f"{card_type}-{base_slug}.md", base_slug, False

    candidate = f"{base_slug}-{card_type}"
    if candidate not in existing:
        return f"{card_type}-{candidate}.md", candidate, True

    i = 2
    while f"{candidate}-{i}" in existing:
        i += 1
    candidate = f"{candidate}-{i}"
    return f"{card_type}-{candidate}.md", candidate, True


def _format_frontmatter(fm: dict) -> str:
    """Render frontmatter as YAML in a stable key order matching Phase 1 cards.

    Quotes string values that need it (with embedded colons/leading specials);
    keeps URLs unquoted to match existing card style.
    """
    order = ["type", "name", "canonical_link", "spotify_url"]
    lines = ["---"]
    used = set()
    for key in order:
        if key in fm and fm[key] is not None:
            lines.append(_yaml_line(key, fm[key]))
            used.add(key)
    for key, value in fm.items():
        if key in used or value is None:
            continue
        lines.append(_yaml_line(key, value))
    lines.append("---")
    return "\n".join(lines) + "\n"


def _yaml_line(key: str, value) -> str:
    if isinstance(value, str):
        # Match existing style: quote 'name', leave URLs/identifiers bare.
        if key == "name" or any(ch in value for ch in [":", "#"]):
            escaped = value.replace('"', '\\"')
            return f'{key}: "{escaped}"'
        return f"{key}: {value}"
    return f"{key}: {value}"


def _format_wikilinks_sentence(wikilinks: Sequence) -> str:
    """Turn a list of wikilink targets into a closing sentence.

    Accepts either ``"type:slug"`` strings or ``(type, slug)`` tuples.
    """
    rendered = []
    for w in wikilinks:
        if isinstance(w, tuple):
            t, slug = w
            rendered.append(f"[[{t}:{slug}]]")
        else:
            s = str(w).strip()
            if s.startswith("[[") and s.endswith("]]"):
                rendered.append(s)
            else:
                rendered.append(f"[[{s}]]")
    if not rendered:
        return ""
    if len(rendered) == 1:
        return f"Related: {rendered[0]}."
    return "Related: " + ", ".join(rendered[:-1]) + f", and {rendered[-1]}."


def _infer_repo_root(start: Path) -> Path:
    """Walk up from ``start`` until a directory containing ``tools/lint_graphs.py``
    and ``graphs/`` is found. Worktree-safe: the old ``parents[3]`` heuristic
    pointed at the worktree root, which lacks the ``tools/`` directory in some
    layouts. Searching for the actual landmarks is robust against worktree
    nesting depth.
    """
    for candidate in [start, *start.parents]:
        if (candidate / "tools" / "lint_graphs.py").is_file() and (
            candidate / "graphs"
        ).is_dir():
            return candidate
    # Fall back to the legacy heuristic so callers still get a sensible default.
    return start.resolve().parents[3]


def _run_lint(
    graphs_root: Path,
    repo_root: Path,
    lint_cmd: Optional[Sequence[str]],
) -> subprocess.CompletedProcess:
    if lint_cmd is not None:
        cmd = list(lint_cmd)
    else:
        venv_py = repo_root / ".venv" / "bin" / "python"
        python = str(venv_py) if venv_py.exists() else sys.executable
        cmd = [python, str(repo_root / "tools" / "lint_graphs.py"), str(graphs_root)]
    return subprocess.run(cmd, capture_output=True, text=True)


def write_card(
    graph: str,
    type: str,
    name: str,
    *,
    repo_root: Optional[Path] = None,
    graphs_root: Optional[Path] = None,
    spotify_url: Optional[str] = None,
    canonical_link: Optional[str] = None,
    body: Optional[str] = None,
    wikilinks: Optional[Sequence] = None,
    run_lint: bool = True,
    lint_cmd: Optional[Sequence[str]] = None,
) -> Path:
    """Write a new card and lint.

    Parameters
    ----------
    graph : str
        Graph slug, e.g. ``"band-x"``. Resolved against ``graphs_root``.
    type : str
        Card type (``person``, ``group``, ``album``, ``track``, ``location``,
        ``note``, ``memory``, …). Phase 1's loose type set — not pinned here.
    name : str
        Human-readable name; goes in ``frontmatter["name"]`` and slugifies into
        the filename.
    repo_root : Path, optional
        Repo root (where ``tools/lint_graphs.py`` lives). Defaults to the
        repo root inferred from this file's location.
    graphs_root : Path, optional
        Directory containing the per-graph folders. Defaults to
        ``<repo_root>/graphs``.
    spotify_url : str, optional
        Already-validated Spotify URL. This helper does NOT call the Spotify
        MCP; callers obtain URLs via the ``retrieve-spotify-song`` skill.
    canonical_link : str, optional
        Wikipedia URL or similar canonical link.
    body : str, optional
        Markdown body paragraph(s). May contain wikilinks.
    wikilinks : sequence, optional
        Extra wikilink targets to append as a closing sentence. Either
        ``"type:slug"`` strings or ``(type, slug)`` tuples.
    run_lint : bool, default True
        If True, run ``tools/lint_graphs.py`` after the write and roll back on
        failure. Tests pass False (or supply ``lint_cmd``) to inject mocks.
    lint_cmd : sequence[str], optional
        Override the lint command (for tests).

    Returns
    -------
    Path
        Absolute path to the newly written card file.

    Raises
    ------
    FileExistsError
        If the derived filename is occupied even after disambiguation collapse.
    LintError
        If ``run_lint`` is True and the lint check fails; the new file has been
        removed before this is raised.
    """
    if repo_root is None:
        repo_root = _infer_repo_root(Path(__file__).resolve())
    else:
        repo_root = Path(repo_root)
    if graphs_root is None:
        graphs_root = repo_root / "graphs"
    else:
        graphs_root = Path(graphs_root)

    graph_dir = graphs_root / graph
    cards_dir = graph_dir / "cards"
    if not cards_dir.is_dir():
        raise FileNotFoundError(f"cards directory not found: {cards_dir}")

    filename, _slug, _disambig = derive_filename(type, name, _existing_slugs(cards_dir))
    target = cards_dir / filename
    if target.exists():
        # Shouldn't happen — _existing_slugs covered it — but be defensive.
        raise FileExistsError(f"card already exists: {target}")

    fm: dict = {"type": type, "name": name}
    if canonical_link:
        fm["canonical_link"] = canonical_link
    if spotify_url:
        fm["spotify_url"] = spotify_url

    body_parts: list[str] = []
    if body and body.strip():
        body_parts.append(body.strip())
    if wikilinks:
        sentence = _format_wikilinks_sentence(wikilinks)
        if sentence:
            body_parts.append(sentence)
    body_text = "\n\n".join(body_parts) if body_parts else f"{name}."

    content = _format_frontmatter(fm) + "\n" + body_text + "\n"
    target.write_text(content, encoding="utf-8")

    # Sanity: confirm parse_card accepts it.
    try:
        frontmatter.load(str(target))
    except Exception:
        target.unlink(missing_ok=True)
        raise

    if run_lint:
        result = _run_lint(graphs_root, repo_root, lint_cmd)
        if result.returncode != 0:
            target.unlink(missing_ok=True)
            raise LintError(result.stdout, result.stderr, result.returncode)

    return target


def check_collision(graph_dir: Path, card_type: str, name: str) -> Optional[str]:
    """Return the disambiguated slug if a collision would occur, else None.

    Pure inspection — does not write anything. Useful for the SKILL.md flow's
    "should I disambiguate?" check before calling write_card.
    """
    cards_dir = graph_dir / "cards"
    existing = _existing_slugs(cards_dir)
    base_slug = slugify(name)
    if base_slug not in existing:
        return None
    _, new_slug, _ = derive_filename(card_type, name, existing)
    return new_slug
