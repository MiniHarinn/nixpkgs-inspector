from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Tracker:
    id: str  # inspector script name; drives collect + restricted check
    issue_number: int
    creation_rev: str  # nixpkgs rev U is frozen at (tracking-automation.creationRev)
    repo: str = "NixOS/nixpkgs"


# PR states we care about. "closed" means closed-without-merge.
PR_OPEN = "open"
PR_MERGED = "merged"
PR_CLOSED = "closed"


@dataclass(frozen=True)
class PullRequest:
    number: int
    state: str  # PR_OPEN | PR_MERGED | PR_CLOSED


@dataclass
class AttrStatus:
    attr: str
    done: bool = False  # True -> [x] (no longer matches), False -> [ ]
    prs: list[int] = field(default_factory=list)  # sorted

    def link(self, number: int) -> None:
        if number not in self.prs:
            self.prs.append(number)


@dataclass
class TrackerResult:
    tracker: Tracker
    current_rev: str  # master commit the checkbox states were evaluated at
    statuses: list[AttrStatus]  # one per universe attr, ASCIIbetically sorted

    @property
    def creation_rev(self) -> str:
        return self.tracker.creation_rev

    @property
    def total(self) -> int:
        return len(self.statuses)

    @property
    def done(self) -> int:
        return sum(1 for s in self.statuses if s.done)

    @property
    def remaining(self) -> int:
        return self.total - self.done

    @property
    def in_flight(self) -> int:
        return sum(1 for s in self.statuses if not s.done and s.prs)
