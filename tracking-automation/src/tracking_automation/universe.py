from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .model import Tracker


class CollectEvaluator(Protocol):
    def collect(self, rev: str) -> list[dict]: ...


@dataclass(frozen=True)
class Universe:
    attrs: frozenset[str]
    order: tuple[str, ...]  # attrs in collect (script) order


def _from_entries(entries: list[dict]) -> Universe:
    order: list[str] = []
    attrs: set[str] = set()
    for e in entries:
        attr = e["attrpath"]
        if attr not in attrs:
            attrs.add(attr)
            order.append(attr)
    return Universe(attrs=frozenset(attrs), order=tuple(order))


def build(tracker: Tracker, evaluator: CollectEvaluator) -> Universe:
    return _from_entries(evaluator.collect(tracker.creation_rev))
