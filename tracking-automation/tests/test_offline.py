from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # tracking-automation/
sys.path.insert(0, str(ROOT / "src"))

from tracking_automation.engine import run_tracking  # noqa: E402
from tracking_automation.model import (  # noqa: E402
    PR_CLOSED,
    PR_MERGED,
    PR_OPEN,
    PullRequest,
    Tracker,
)
from tracking_automation.render import render  # noqa: E402
from tracking_automation.universe import Universe  # noqa: E402

UNIVERSE = Universe(
    attrs=frozenset({"a", "b", "c", "d", "e"}),
    pos={
        "pkgs/by-name/aa/a/package.nix": frozenset({"a"}),
        "pkgs/by-name/dd/d/package.nix": frozenset({"d"}),
        "pkgs/by-name/ee/e/package.nix": frozenset({"e"}),
    },
)

# Current offenders at master (B_now): a, b, c still match; d, e are done.
B_NOW = [{"attrpath": x} for x in ("a", "b", "c")]

# Per-revision predicate-match for the eval-diff (before = commit^1, after = commit).
MATCHED = {
    "c101^1": {"a", "b", "c", "d"},  # before #101: d broken
    "c101": {"a", "b", "c"},         # after  #101: d fixed
    "c104^1": {"a", "b", "c", "e"},
    "c104": {"a", "b", "c"},
    "m102^1": {"a", "b", "c"},       # before #102 (open): a broken
    "m102": {"b", "c"},              # after  #102: a would be fixed
    "c106^1": {"a", "b", "c"},       # guard: #106 touches d's file but
    "c106": {"a", "b", "c"},         # d already fixed before & after -> no link
}
CHANGED = {
    "m102": ["pkgs/by-name/aa/a/package.nix"],
    "c101": ["pkgs/by-name/dd/d/package.nix"],
    "c104": ["pkgs/by-name/ee/e/package.nix"],
    "c106": ["pkgs/by-name/dd/d/package.nix"],
}
LANDING = {101: "c101", 104: "c104", 106: "c106"}


class FakeBackend:
    def current_rev(self) -> str:
        return "CUR"

    def collect(self, rev: str) -> list:
        return list(B_NOW)

    def check_at(self, rev: str, attrs) -> set:
        return {a for a in attrs if a in MATCHED.get(rev, set())}

    def prime_landing_map(self, creation_rev: str) -> None:
        pass

    def merge_commit(self, number: int):
        return f"m{number}" if number == 102 else None

    def landing_commit(self, number: int):
        return LANDING.get(number)

    def first_parent_changed_files(self, commit: str) -> list:
        return list(CHANGED.get(commit, []))

    def restore(self) -> None:
        pass


class FakeReader:
    def __init__(self, prs):
        self.prs = prs

    def referencing_prs(self, repo: str, issue_number: int):
        return list(self.prs)


def main() -> int:
    tracker = Tracker(
        id="demo",
        issue_number=999999,
        creation_rev="abc123def456",
    )
    prs = [
        PullRequest(101, PR_MERGED),  # fixes d
        PullRequest(102, PR_OPEN),    # would fix a -> [ ] #102
        PullRequest(103, PR_CLOSED),  # ignored
        PullRequest(104, PR_MERGED),  # fixes e
        PullRequest(106, PR_MERGED),  # stale ref on d's file -> no link
    ]

    result = run_tracking(
        tracker, universe=UNIVERSE, backend=FakeBackend(), reader=FakeReader(prs)
    )

    got = {s.attr: (s.done, tuple(s.prs)) for s in result.statuses}
    expected = {
        "a": (False, (102,)),
        "b": (False, ()),
        "c": (False, ()),
        "d": (True, (101,)),
        "e": (True, (104,)),
    }
    assert got == expected, f"attribution mismatch:\n got={got}\n exp={expected}"
    assert result.total == 5 and result.done == 2 and result.in_flight == 1
    assert result.current_rev == "CUR" and result.creation_rev == "abc123def456"

    with tempfile.TemporaryDirectory() as tmp:
        written = render(result, tmp, chunk_bytes=60000)
        index = next(p for p in written if p.name.endswith("-index.md"))
        comment = next(p for p in written if "comment-01" in p.name)
        ctext = comment.read_text()
        assert "- [ ] a #102" in ctext, ctext
        assert "- [x] d #101" in ctext, ctext
        assert "- [x] e #104" in ctext, ctext
        assert "#106" not in ctext, "stale merged ref must not be linked"
        itext = index.read_text()
        assert "Done: **2**" in itext, itext
        assert "abc123def456" in itext and "CUR" in itext, itext
        assert "offender" not in itext.lower(), "no new-offenders section in v2"

        print("OK - frozen-universe attribution + render verified\n")
        print("=== comment-01.md ===")
        print(ctext)
        print("=== index.md ===")
        print(itext)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
