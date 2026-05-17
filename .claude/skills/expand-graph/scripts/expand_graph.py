"""expand_graph.py — Helper for the `expand-graph` skill.

Orchestrates candidate generation + (optionally) writes via `add-node` /
`add-edge`. The helper itself never writes a card file directly; every node
write goes through ``add-node``'s ``write_card`` helper and every body-edge
through ``add-edge``'s helper. This is a locked architectural rule of the
sprint spec.

Public API
----------

``Candidate`` — dataclass describing one proposed node addition.

``ExpansionResult`` — dataclass returned by ``run_expand_graph``.

``generate_candidates(graph, criterion, *, graphs_root=None, ceiling=5,
                      search_fn=None) -> tuple[list[Candidate], int]``
    Pure-ish candidate-generation pass. Returns ``(candidates, overflow)``
    where ``candidates`` is truncated to the (clamped) ceiling and
    ``overflow`` is how many extra candidates the search produced beyond
    that ceiling. Reads the graph's README + existing card slugs to give
    the search function scope context. ``search_fn`` is injected so tests
    (and real callers) supply their own search; the default raises, since
    web/MCP search is not available inside this helper.

``run_expand_graph(graph, criterion, *, dry_run=False, ...) -> ExpansionResult``
    Full orchestrated pass: candidate generation + optional approval-driven
    writes. In dry-run mode, only candidate generation runs.

Candidate ceiling
-----------------

The ``ceiling`` argument is clamped to ``[1, 10]`` per the sprint spec's
locked rule that ``expand-graph`` never surfaces more than 10 candidates
in one pass. Truncation happens in ``generate_candidates`` so every caller
benefits.
"""
from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Optional, Sequence


# Ceiling rule from project_spec.md section "Resolved (formerly open
# questions)" item 5: 5–10 candidates per run, hard cap 10.
CANDIDATE_CEILING_MIN = 1
CANDIDATE_CEILING_MAX = 10
CANDIDATE_CEILING_DEFAULT = 5


# ---------- data classes ----------


@dataclass
class Candidate:
    """One proposed addition to the graph.

    Attributes:
        name: human-readable name (becomes ``frontmatter.name``).
        type: card type. Defaults to ``"album"`` per spec.
        wikilinks: list of ``"type:slug"`` strings pointing at existing
            cards in the graph. Passed to ``add-node`` so the closing
            "Related: ..." sentence gets generated.
        spotify_url: verified canonical URL, or ``None``.
        spotify_reason: if ``spotify_url`` is ``None``, the documented
            reason (e.g. ``"MCP search exhausted"``). Required when
            ``spotify_url`` is ``None``.
        canonical_link: optional Wikipedia or other canonical URL.
        rationale: one-sentence explanation tying the candidate to the
            graph scope. Used both in the user-facing approval list and
            as the seed for the card body if the orchestrator does not
            override it.
    """

    name: str
    type: str = "album"
    wikilinks: list[str] = field(default_factory=list)
    spotify_url: Optional[str] = None
    spotify_reason: Optional[str] = None
    canonical_link: Optional[str] = None
    rationale: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Candidate.name is empty")
        if self.spotify_url is None and not self.spotify_reason:
            # The spec requires every surfaced candidate either has a
            # verified Spotify URL or a documented reason it lacks one.
            raise ValueError(
                f"Candidate {self.name!r} has no spotify_url and no "
                "spotify_reason; one must be provided."
            )


@dataclass
class ExpansionResult:
    criterion: str
    candidates: list[Candidate]
    overflow: int
    created_paths: list[Path] = field(default_factory=list)
    edge_paths: list[Path] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)  # (name, reason)
    lint_returncode: Optional[int] = None
    dry_run: bool = False


# ---------- scope reading ----------


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _read_scope(graphs_root: Path, graph: str) -> dict:
    """Read the graph's README + existing card slugs, returning a dict
    suitable as scope context for a search function.

    Returns keys:
        graph: slug
        graph_dir: Path
        readme: str (README.md contents or "")
        cards_dir: Path
        existing_cards: list[str] of relative filenames
        existing_slugs: list[str] of ``"type:slug"`` tokens for wikilink
            proposals
        scope_notes: list[str] of contents of ``note-*.md`` cards (these
            are the Phase 1 inline scope statements).
    """
    graph_dir = graphs_root / graph
    if not graph_dir.is_dir():
        raise FileNotFoundError(f"graph directory not found: {graph_dir}")

    readme_path = graph_dir / "README.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

    cards_dir = graph_dir / "cards"
    existing_cards: list[str] = []
    existing_slugs: list[str] = []
    scope_notes: list[str] = []

    if cards_dir.is_dir():
        for card in sorted(cards_dir.glob("*.md")):
            existing_cards.append(card.name)
            # filename pattern: <type>-<slug>.md (slug after first hyphen)
            stem = card.stem
            if "-" in stem:
                card_type, slug = stem.split("-", 1)
                existing_slugs.append(f"{card_type}:{slug}")
            if card.name.startswith("note-"):
                scope_notes.append(card.read_text(encoding="utf-8"))

    return {
        "graph": graph,
        "graph_dir": graph_dir,
        "readme": readme,
        "cards_dir": cards_dir,
        "existing_cards": existing_cards,
        "existing_slugs": existing_slugs,
        "scope_notes": scope_notes,
    }


# ---------- candidate generation ----------


def _clamp_ceiling(ceiling: int) -> int:
    if ceiling < CANDIDATE_CEILING_MIN:
        return CANDIDATE_CEILING_MIN
    if ceiling > CANDIDATE_CEILING_MAX:
        return CANDIDATE_CEILING_MAX
    return ceiling


SearchFn = Callable[[str, str, dict], Iterable[Candidate]]


def _default_search_fn(graph: str, criterion: str, scope: dict) -> list[Candidate]:
    """Default no-op search. Real callers MUST inject a search function
    that wraps WebSearch / Spotify MCP. The helper refuses to invent
    candidates."""
    raise NotImplementedError(
        "expand-graph: no search_fn was provided. The orchestrating "
        "skill must inject a search function that calls WebSearch and "
        "the Spotify MCP. The helper does not perform live searches "
        "itself."
    )


def generate_candidates(
    graph: str,
    criterion: str,
    *,
    graphs_root: Optional[Path] = None,
    ceiling: int = CANDIDATE_CEILING_DEFAULT,
    search_fn: Optional[SearchFn] = None,
) -> tuple[list[Candidate], int]:
    """Generate and return ``(candidates, overflow)``.

    The ``ceiling`` is clamped to ``[1, 10]``. The truncated list never
    exceeds the clamped ceiling. ``overflow`` is ``max(0, total - ceiling)``
    where ``total`` is how many candidates the search function produced.
    """
    if graphs_root is None:
        graphs_root = Path.cwd() / "graphs"
    graphs_root = Path(graphs_root)

    capped = _clamp_ceiling(ceiling)
    scope = _read_scope(graphs_root, graph)

    if search_fn is None:
        search_fn = _default_search_fn

    raw = list(search_fn(graph, criterion, scope))
    overflow = max(0, len(raw) - capped)
    truncated = raw[:capped]
    return truncated, overflow


# ---------- helpers for add-node / add-edge bridging ----------


def _import_write_card(repo_root: Path):
    """Locate the add-node helper. Imported lazily so tests can run even
    if the helper is in an unusual spot."""
    candidate = repo_root / ".claude" / "skills" / "add-node" / "scripts"
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
    from write_card import write_card  # type: ignore  # noqa: WPS433

    return write_card


def _import_add_edge(repo_root: Path):
    """Locate the add-edge helper if present. Returns ``None`` if Track C
    has not yet shipped its helper at the expected path — the orchestrator
    is tolerant of this in dry-run / partial-environment tests."""
    candidate = repo_root / ".claude" / "skills" / "add-edge" / "scripts"
    init = candidate / "add_edge.py"
    if not init.exists():
        return None
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
    try:
        from add_edge import add_edge  # type: ignore  # noqa: WPS433
    except Exception:
        return None
    return add_edge


def _run_lint(repo_root: Path) -> int:
    """Run the canonical lint gate over all graphs. Returns the exit
    code. The orchestrator surfaces this; it does not raise."""
    venv_python = repo_root / ".venv" / "bin" / "python"
    python = str(venv_python) if venv_python.exists() else sys.executable
    proc = subprocess.run(
        [python, "tools/lint_graphs.py", "graphs"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    return proc.returncode


# ---------- full orchestrator ----------


def _candidate_body(cand: Candidate) -> str:
    """Build a short body sentence for a candidate so ``add-node`` does
    not fall back to its single-sentence placeholder. Wikilinks are
    appended by ``add-node`` itself when ``wikilinks=`` is set."""
    rationale = cand.rationale.strip() or f"{cand.name} ({cand.type})."
    if not rationale.endswith("."):
        rationale = rationale + "."
    return rationale


def run_expand_graph(
    graph: str,
    criterion: str,
    *,
    repo_root: Optional[Path] = None,
    graphs_root: Optional[Path] = None,
    ceiling: int = CANDIDATE_CEILING_DEFAULT,
    dry_run: bool = False,
    search_fn: Optional[SearchFn] = None,
    approved_indices: Optional[Sequence[int]] = None,
    add_node_fn: Optional[Callable] = None,
    add_edge_fn: Optional[Callable] = None,
    run_lint: bool = True,
) -> ExpansionResult:
    """Generate candidates and (unless ``dry_run``) write the approved
    ones via ``add-node`` / ``add-edge``.

    ``approved_indices`` selects which candidates to write (1-based to
    match the user-facing numbered list). If ``None`` and not dry-run,
    every candidate is treated as approved — the assumption being that
    the orchestrating Claude session has already filtered the list
    according to user response.
    """
    if repo_root is None:
        repo_root = Path.cwd()
    repo_root = Path(repo_root)
    if graphs_root is None:
        graphs_root = repo_root / "graphs"
    graphs_root = Path(graphs_root)

    candidates, overflow = generate_candidates(
        graph,
        criterion,
        graphs_root=graphs_root,
        ceiling=ceiling,
        search_fn=search_fn,
    )

    result = ExpansionResult(
        criterion=criterion,
        candidates=candidates,
        overflow=overflow,
        dry_run=dry_run,
    )

    if dry_run:
        return result

    if approved_indices is None:
        approved = list(range(1, len(candidates) + 1))
    else:
        approved = [i for i in approved_indices if 1 <= i <= len(candidates)]

    write_card = add_node_fn or _import_write_card(repo_root)
    add_edge = add_edge_fn if add_edge_fn is not None else _import_add_edge(repo_root)

    for idx in approved:
        cand = candidates[idx - 1]
        try:
            path = write_card(
                graph=graph,
                type=cand.type,
                name=cand.name,
                repo_root=repo_root,
                graphs_root=graphs_root,
                spotify_url=cand.spotify_url,
                canonical_link=cand.canonical_link,
                body=_candidate_body(cand),
                wikilinks=cand.wikilinks or None,
            )
            result.created_paths.append(Path(path))
        except Exception as exc:  # LintError, ValueError, etc.
            result.skipped.append((cand.name, f"add-node failed: {exc}"))
            continue

        # Reciprocal edges from the existing wikilink targets back to the
        # new card. Only attempted when the add-edge helper is available.
        if add_edge is None or not cand.wikilinks:
            continue
        # Slug for the new card mirrors add-node's derivation: lowercased,
        # accents stripped, non-alphanumeric collapsed to hyphens. We
        # re-derive it from the returned path to stay in lockstep with
        # whatever disambiguation add-node applied.
        new_stem = Path(path).stem
        if "-" in new_stem:
            new_type, new_slug = new_stem.split("-", 1)
        else:
            new_type, new_slug = cand.type, new_stem
        for wl in cand.wikilinks:
            if ":" not in wl:
                continue
            tgt_type, tgt_slug = wl.split(":", 1)
            try:
                changed = add_edge(
                    graph=graph,
                    src_slug=tgt_slug,
                    tgt_slug=new_slug,
                    repo_root=repo_root,
                    graphs_root=graphs_root,
                )
                if isinstance(changed, (list, tuple)):
                    result.edge_paths.extend(Path(p) for p in changed)
                elif changed:
                    result.edge_paths.append(Path(changed))
            except Exception as exc:
                result.skipped.append(
                    (f"{wl} -> {new_type}:{new_slug}", f"add-edge failed: {exc}")
                )

    if run_lint:
        result.lint_returncode = _run_lint(repo_root)

    return result
