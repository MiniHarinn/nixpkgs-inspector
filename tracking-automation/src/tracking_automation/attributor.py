from __future__ import annotations

import sys
from dataclasses import dataclass

from .model import PR_MERGED, PR_OPEN, AttrStatus, PullRequest
from .nixpkgs import Attribution, Evaluator


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
            n = _attribute_one(pr, commit, statuses, backend, scope)
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
    backend: _Backend,
    scope: set[str],
) -> int:
    # Diff the offender set over the whole (frozen) scope across the commit,
    # rather than guessing affected attrs from changed files: this catches fixes
    # that land outside an attr's meta.position (e.g. an adjacent imported file)
    # and keeps the eval boundary closed to attrs we already track. offenders()
    # honours a pure postEval; without one it falls back to the cheap predicate
    # check over just the scope.
    if not scope:
        return 0

    try:
        before = backend.offenders_in_scope(f"{commit}^1", scope)
        after = backend.offenders_in_scope(commit, scope)
    except Exception as exc:  # noqa: BLE001
        _log(f"PR #{pr.number}: eval failed: {exc}")
        return 0

    fixed = before - after
    for attr in fixed:
        statuses[attr].link(pr.number)
    return len(fixed)
