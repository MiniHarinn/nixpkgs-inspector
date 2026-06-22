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
from tracking_automation.universe import Universe, build  # noqa: E402

UNIVERSE = Universe(
    attrs=frozenset({"a", "b", "c", "d", "e"}),
    order=("a", "b", "c", "d", "e"),
)

# offenders now: a,b,c match; d,e done.
B_NOW = [{"attrpath": x} for x in ("a", "b", "c")]

# predicate-match per rev (before=commit^1, after=commit).
MATCHED = {
    "c101^1": {"a", "b", "c", "d"},
    "c101": {"a", "b", "c"},         # #101 fixed d
    "c104^1": {"a", "b", "c", "e"},
    "c104": {"a", "b", "c"},         # #104 fixed e
    "m102^1": {"a", "b", "c"},
    "m102": {"b", "c"},              # #102 would fix a
    "c106^1": {"a", "b", "c"},
    "c106": {"a", "b", "c"},         # #106 flips nothing -> no link
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

    def offenders(self, rev: str) -> list:
        return [e["attrpath"] for e in self.collect(rev)]

    def offenders_in_scope(self, rev: str, scope: set) -> set:
        return self.check_at(rev, scope)  # no postEval -> predicate is authoritative

    def restore(self) -> None:
        pass


class FakeReader:
    def __init__(self, prs):
        self.prs = prs

    def referencing_prs(self, repo: str, issue_number: int):
        return list(self.prs)


# postEval path: offenders() is authoritative (decoupled from raw predicate).
OFFENDERS = {
    "rev0": ["p", "q", "r"],   # universe at creation
    "CUR2": ["p"],             # now: q, r done
    "l201^1": ["p", "q", "r"],
    "l201": ["p", "r"],        # #201 fixed q
    "g202^1": ["p"],
    "g202": [],                # #202 would fix p
}
LANDING2 = {201: "l201"}


class PostEvalBackend:
    def current_rev(self) -> str:
        return "CUR2"

    def offenders(self, rev: str) -> list:
        return list(OFFENDERS[rev])

    def offenders_in_scope(self, rev: str, scope: set) -> set:
        return set(self.offenders(rev)) & scope

    def prime_landing_map(self, creation_rev: str) -> None:
        pass

    def merge_commit(self, number: int):
        return "g202" if number == 202 else None

    def landing_commit(self, number: int):
        return LANDING2.get(number)

    def restore(self) -> None:
        pass


def _check_posteval() -> None:
    tracker = Tracker(id="pe", issue_number=1, creation_rev="rev0")
    backend = PostEvalBackend()
    universe = build(tracker, backend)
    assert universe.attrs == frozenset({"p", "q", "r"}), universe
    assert universe.order == ("p", "q", "r"), universe.order  # postEval order preserved

    prs = [PullRequest(201, PR_MERGED), PullRequest(202, PR_OPEN)]
    result = run_tracking(
        tracker, universe=universe, backend=backend, reader=FakeReader(prs)
    )
    got = {s.attr: (s.done, tuple(s.prs)) for s in result.statuses}
    expected = {
        "p": (False, (202,)),  # open PR would fix it
        "q": (True, (201,)),   # merged PR fixed it
        "r": (True, ()),       # done, no referencing PR
    }
    assert got == expected, f"postEval attribution mismatch:\n got={got}\n exp={expected}"
    print("OK - postEval offender pipeline verified")


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
        PullRequest(106, PR_MERGED),  # lands but flips nothing in scope -> no link
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

    _check_posteval()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
