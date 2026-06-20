from __future__ import annotations

import sys

from .attributor import attribute
from .github import GitHubReader
from .model import AttrStatus, Tracker, TrackerResult
from .nixpkgs import CheckoutManager
from .universe import Universe


def _log(msg: str) -> None:
    print(f"[tracking] {msg}", file=sys.stderr)


def run_tracking(
    tracker: Tracker,
    *,
    universe: Universe,
    backend: CheckoutManager,
    reader: GitHubReader,
) -> TrackerResult:
    try:
        current = backend.current_rev()
        _log(f"{tracker.id}: current master {current[:12]}, |U|={len(universe.attrs)}")

        b_now = {e["attrpath"] for e in backend.collect(current)}
        remaining = universe.attrs & b_now
        done = universe.attrs - remaining
        _log(f"{tracker.id}: done={len(done)} remaining={len(remaining)}")

        statuses: dict[str, AttrStatus] = {
            a: AttrStatus(attr=a, done=(a in done)) for a in universe.attrs
        }

        prs = reader.referencing_prs(tracker.repo, tracker.issue_number)
        _log(f"{tracker.id}: {len(prs)} referencing PR(s)")

        backend.prime_landing_map(tracker.creation_rev)
        stats = attribute(
            statuses, universe, prs, backend, remaining=remaining, done=done
        )
        _log(
            f"{tracker.id}: attribution open {stats.open_linked}/{stats.open_total} "
            f"merged {stats.merged_linked}/{stats.merged_total} "
            f"({stats.attr_links} attr-links)"
        )

        statuses_list = [statuses[a] for a in sorted(universe.attrs)]
        for s in statuses_list:
            s.prs.sort()
        return TrackerResult(
            tracker=tracker, current_rev=current, statuses=statuses_list
        )
    finally:
        backend.restore()  # restore worktree + drop this leg's refs, even on failure
