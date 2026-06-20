from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from .model import Tracker


class CollectEvaluator(Protocol):
    def collect(self, rev: str) -> list[dict]: ...


@dataclass(frozen=True)
class Universe:
    attrs: frozenset[str]
    pos: dict[str, frozenset[str]]  # repo-relative file -> attrs defined there

    def candidates(self, changed_files: Iterable[str]) -> set[str]:
        out: set[str] = set()
        for f in changed_files:
            out |= self.pos.get(f, frozenset())
        return out


def normalize_position(position: str) -> str:
    path = position.rsplit(":", 1)[0]
    idx = path.find("/pkgs/")
    if idx >= 0:
        return path[idx + 1 :]
    return path.lstrip("/")


def _invert(entries: list[dict]) -> Universe:
    attrs: set[str] = set()
    pos: dict[str, set[str]] = {}
    for e in entries:
        attrs.add(e["attrpath"])
        position = e.get("position")
        if position:
            pos.setdefault(normalize_position(position), set()).add(e["attrpath"])
    return Universe(
        attrs=frozenset(attrs),
        pos={f: frozenset(v) for f, v in pos.items()},
    )


def build(tracker: Tracker, evaluator: CollectEvaluator) -> Universe:
    return _invert(evaluator.collect(tracker.creation_rev))
