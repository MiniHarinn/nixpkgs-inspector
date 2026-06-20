from __future__ import annotations

import sys
from dataclasses import dataclass

from .model import PR_MERGED, PR_OPEN, AttrStatus, PullRequest
from .nixpkgs import Attribution, Evaluator
from .universe import Universe


@dataclass
class AttributionStats:
    open_total: int = 0
    open_linked: int = 0
    merged_total: int = 0
    merged_linked: int = 0
    attr_links: int = 0


class _Backend(Attribution, Evaluator):  # CheckoutManager satisfies both
    pass


def _log(msg: str) -> None:
    print(f"[tracking] {msg}", file=sys.stderr)


def attribute(
    statuses: dict[str, AttrStatus],
    universe: Universe,
    prs: list[PullRequest],
    backend: _Backend,
    *,
    remaining: set[str],
    done: set[str],
) -> AttributionStats:
    def run(state: str, commit_of, scope: set[str]) -> tuple[int, int, int]:
        total = linked = links = 0
        for pr in (p for p in prs if p.state == state):
            total += 1
            commit = commit_of(pr.number)
            if commit is None:
                continue
            n = _attribute_one(pr, commit, statuses, universe, backend, scope)
            if n:
                linked += 1
                links += n
        return total, linked, links

    ot, ol, oa = run(PR_OPEN, backend.merge_commit, remaining)
    mt, ml, ma = run(PR_MERGED, backend.landing_commit, done)
    return AttributionStats(ot, ol, mt, ml, oa + ma)


def _attribute_one(
    pr: PullRequest,
    commit: str,
    statuses: dict[str, AttrStatus],
    universe: Universe,
    backend: _Backend,
    scope: set[str],
) -> int:
    try:
        changed = backend.first_parent_changed_files(commit)
    except Exception as exc:  # noqa: BLE001
        _log(f"PR #{pr.number}: changed-files failed: {exc}")
        return 0

    candidates = universe.candidates(changed) & scope
    if not candidates:
        return 0

    try:
        before = backend.check_at(f"{commit}^1", candidates)
        after = backend.check_at(commit, candidates)
    except Exception as exc:  # noqa: BLE001
        _log(f"PR #{pr.number}: eval failed: {exc}")
        return 0

    fixed = before - after
    for attr in fixed:
        statuses[attr].link(pr.number)
    return len(fixed)
