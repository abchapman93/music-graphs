"""add_edge.py — Helper for the `add-edge` skill.

Inserts a ``[[type:slug|Display]]`` wikilink into the body of an existing card.
Optionally also writes a reciprocal link to the target card (``symmetric=True``).
Always runs ``tools/lint_graphs.py`` after the write(s); on lint failure the
original card contents are restored from in-memory snapshots and ``LintError``
is raised.

Public API:
    add_edge(graph, src_slug, tgt_slug, *,
             repo_root=None, graphs_root=None,
             relationship=None, symmetric=False,
             on_dangling="abort",
             run_lint=True, lint_cmd=None) -> list[Path]

    DanglingTargetError, DuplicateEdgeError, LintError, CardNotFoundError
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, Sequence

import frontmatter

# Reuse the wikilink regex shape from lib/cards.py so detection is consistent
# (we do not import lib/cards directly to keep this script self-contained when
# invoked with a different sys.path).
_WIKILINK_RE = re.compile(
    r"""
    \[\[\s*
    ([a-zA-Z][a-zA-Z0-9_-]*)
    \s*:\s*
    ([a-zA-Z0-9][a-zA-Z0-9._\-]*)
    \s*
    (?:\|\s*([^\]]*?)\s*)?
    \s*\]\]
    """,
    re.VERBOSE,
)


class LintError(RuntimeError):
    def __init__(self, stdout: str, stderr: str, returncode: int):
        super().__init__(f"lint_graphs.py exited {returncode}")
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


class DanglingTargetError(RuntimeError):
    """Raised when the target card does not exist and the caller asked to abort."""


class DuplicateEdgeError(RuntimeError):
    """Raised when the source card already contains the wikilink."""


class CardNotFoundError(FileNotFoundError):
    """Raised when the source card cannot be located in the graph."""


def _find_card(cards_dir: Path, slug: str) -> Optional[Path]:
    """Locate a card by its slug (filename stem after first hyphen).

    Returns the first match in alphabetical order, or None if not found.
    """
    if not cards_dir.is_dir():
        return None
    for p in sorted(cards_dir.glob("*.md")):
        stem = p.stem
        card_slug = stem.split("-", 1)[1] if "-" in stem else stem
        if card_slug == slug:
            return p
    return None


def _card_type_from_filename(path: Path) -> str:
    stem = path.stem
    return stem.split("-", 1)[0] if "-" in stem else stem


def _has_wikilink(body: str, ttype: str, slug: str) -> bool:
    for m in _WIKILINK_RE.finditer(body or ""):
        if m.group(1) == ttype and m.group(2) == slug:
            return True
    return False


def _default_display(name: str) -> str:
    return name


def _compose_sentence(
    relationship: Optional[str],
    src_name: str,
    tgt_type: str,
    tgt_slug: str,
    tgt_display: str,
) -> str:
    """Construct a natural-sounding sentence containing the wikilink.

    Examples:
        relationship="appears on" → "Dave Alvin appears on [[album:ashgrove|Ashgrove]]."
        relationship=None         → "Related: [[album:ashgrove|Ashgrove]]."
    """
    link = f"[[{tgt_type}:{tgt_slug}|{tgt_display}]]"
    if relationship and relationship.strip():
        return f"{src_name} {relationship.strip()} {link}."
    return f"Related: {link}."


def _append_sentence(body: str, sentence: str) -> str:
    """Append a sentence to the card body as a new paragraph.

    Keeps existing content intact. Ensures a blank-line separator between the
    existing body and the new paragraph.
    """
    body = (body or "").rstrip()
    if not body:
        return sentence + "\n"
    return body + "\n\n" + sentence + "\n"


def _read_card(path: Path) -> tuple[dict, str, str]:
    """Return ``(frontmatter_dict, body, raw_text)``."""
    raw = path.read_text(encoding="utf-8")
    post = frontmatter.loads(raw)
    return dict(post.metadata or {}), post.content or "", raw


def _write_card(path: Path, fm: dict, body: str) -> None:
    post = frontmatter.Post(body, **fm)
    path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")


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


def add_edge(
    graph: str,
    src_slug: str,
    tgt_slug: str,
    *,
    repo_root: Optional[Path] = None,
    graphs_root: Optional[Path] = None,
    relationship: Optional[str] = None,
    symmetric: bool = False,
    on_dangling: str = "abort",  # "abort" | "forward"
    run_lint: bool = True,
    lint_cmd: Optional[Sequence[str]] = None,
) -> list[Path]:
    """Add a ``[[type:slug|Display]]`` wikilink from src to tgt in ``graph``.

    Parameters
    ----------
    graph : str
        Graph slug (e.g. ``"band-x"``).
    src_slug, tgt_slug : str
        Card slugs (filename-stem-after-first-hyphen). Types are inferred from
        the matching filenames in ``graphs/<graph>/cards/``.
    relationship : str, optional
        Phrase that joins src and tgt in the inserted sentence
        (e.g. ``"appears on"``, ``"covers"``). When omitted, a generic
        "Related: ..." sentence is appended.
    symmetric : bool, default False
        If True, also write the reciprocal wikilink (tgt → src) into the
        target card. Uses the same relationship phrase if supplied; the caller
        is responsible for picking a phrase that reads correctly in both
        directions (e.g. omit ``relationship`` for symmetric edges).
    on_dangling : {"abort", "forward"}, default "abort"
        Behavior when the target slug does not exist in the graph:
        - ``"abort"``: raise ``DanglingTargetError`` without writing anything.
        - ``"forward"``: proceed and write a forward-reference wikilink anyway.
          The lint gate may still reject the write.
    run_lint : bool, default True
        If True, run ``tools/lint_graphs.py`` after the write and roll back on
        failure.
    lint_cmd : sequence[str], optional
        Override the lint command (for tests).

    Returns
    -------
    list[Path]
        Absolute paths of card files modified (one if one-way; two if
        symmetric).

    Raises
    ------
    CardNotFoundError
        If the source card slug does not resolve to a file.
    DanglingTargetError
        If ``on_dangling="abort"`` and the target card is missing.
    DuplicateEdgeError
        If the source card body already contains the wikilink.
    LintError
        If ``run_lint=True`` and the post-write lint check fails. All modified
        files are restored to their pre-write contents before the raise.
    """
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[3]
    else:
        repo_root = Path(repo_root)
    if graphs_root is None:
        graphs_root = repo_root / "graphs"
    else:
        graphs_root = Path(graphs_root)

    cards_dir = graphs_root / graph / "cards"
    if not cards_dir.is_dir():
        raise FileNotFoundError(f"cards directory not found: {cards_dir}")

    # --- locate source card ---
    src_path = _find_card(cards_dir, src_slug)
    if src_path is None:
        raise CardNotFoundError(f"source card not found for slug {src_slug!r} in {cards_dir}")

    # --- locate target card (may be missing) ---
    tgt_path = _find_card(cards_dir, tgt_slug)
    if tgt_path is None:
        if on_dangling == "abort":
            raise DanglingTargetError(
                f"target card not found for slug {tgt_slug!r} in {cards_dir}. "
                f"Create it first via add-node, or pass on_dangling='forward' "
                f"to write a forward reference."
            )
        elif on_dangling != "forward":
            raise ValueError(f"unknown on_dangling value: {on_dangling!r}")

    # --- read source ---
    src_fm, src_body, src_raw = _read_card(src_path)
    src_type = _card_type_from_filename(src_path)
    src_name = str(src_fm.get("name") or src_slug)

    # --- determine target type/display ---
    if tgt_path is not None:
        tgt_fm, tgt_body, tgt_raw = _read_card(tgt_path)
        tgt_type = _card_type_from_filename(tgt_path)
        tgt_name = str(tgt_fm.get("name") or tgt_slug)
    else:
        # Forward reference: caller didn't tell us the type. Default to the
        # source type's most-common "other side" — but in practice the safest
        # default is to mirror the source type. The lint gate will catch any
        # genuinely wrong references at the next write.
        tgt_fm = None
        tgt_body = None
        tgt_raw = None
        tgt_type = src_type
        tgt_name = tgt_slug.replace("-", " ").title()

    # --- duplicate detection on source ---
    if _has_wikilink(src_body, tgt_type, tgt_slug):
        raise DuplicateEdgeError(
            f"edge already exists: [[{tgt_type}:{tgt_slug}]] already present in {src_path}"
        )

    # --- compose + write source ---
    sentence = _compose_sentence(
        relationship, src_name, tgt_type, tgt_slug, tgt_display=tgt_name
    )
    new_src_body = _append_sentence(src_body, sentence)

    modified: list[tuple[Path, str]] = [(src_path, src_raw)]
    _write_card(src_path, src_fm, new_src_body)

    # --- symmetric: write target side if requested and target exists ---
    if symmetric and tgt_path is not None:
        if not _has_wikilink(tgt_body, src_type, src_slug):
            sentence2 = _compose_sentence(
                relationship, tgt_name, src_type, src_slug, tgt_display=src_name
            )
            new_tgt_body = _append_sentence(tgt_body, sentence2)
            modified.append((tgt_path, tgt_raw))
            _write_card(tgt_path, tgt_fm, new_tgt_body)
        # If reciprocal link is already there, skip silently — still report
        # the source change as the primary effect.

    # --- lint gate ---
    if run_lint:
        result = _run_lint(graphs_root, repo_root, lint_cmd)
        if result.returncode != 0:
            # rollback all modified files
            for path, original in modified:
                path.write_text(original, encoding="utf-8")
            raise LintError(result.stdout, result.stderr, result.returncode)

    return [p for p, _ in modified]
