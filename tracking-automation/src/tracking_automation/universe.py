from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .model import Tracker


class OffenderEvaluator(Protocol):
    def offenders(self, rev: str) -> list[str]: ...


@dataclass(frozen=True)
class Universe:
    attrs: frozenset[str]
    order: tuple[str, ...]  # attrs in offender (post-eval) order, frozen at creation


def _from_attrpaths(attrpaths: list[str]) -> Universe:
    order: list[str] = []
    attrs: set[str] = set()
    for attr in attrpaths:
        if attr not in attrs:
            attrs.add(attr)
            order.append(attr)
    return Universe(attrs=frozenset(attrs), order=tuple(order))


def build(tracker: Tracker, evaluator: OffenderEvaluator) -> Universe:
    return _from_attrpaths(evaluator.offenders(tracker.creation_rev))
