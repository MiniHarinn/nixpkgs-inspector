from __future__ import annotations

import argparse

from .engine import run_tracking
from .github import PyGithubReader
from .model import Tracker
from .nixpkgs import CheckoutManager
from .render import render
from .universe import build


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="tracking-automation")
    # Baked by the flake app from the script's attributes (all required):
    p.add_argument("--script", required=True, help="inspector script name")
    p.add_argument("--issue", required=True, type=int, help="tracking issue number")
    p.add_argument("--creation-rev", required=True, help="nixpkgs rev U is frozen at")
    p.add_argument("--script-dir", required=True, help="path to scripts/<name>")
    p.add_argument("--lib-dir", required=True, help="path to lib (provides nilib)")
    p.add_argument("--config-file", required=True, help="path to nixpkgs-default-config.nix")
    p.add_argument("--tooling-nixpkgs", required=True, help="normal nixpkgs for lib/tooling")
    p.add_argument("--post-eval", default=None, help="pure postEval exe (collect JSON argv1 -> offenders JSON)")
    # Runtime additives <3
    p.add_argument("--worktree", required=True, help="nixpkgs clone for attribution")
    p.add_argument("--out", default="out", help="output dir")
    a = p.parse_args(argv)

    tracker = Tracker(id=a.script, issue_number=a.issue, creation_rev=a.creation_rev)
    backend = CheckoutManager(
        a.worktree,
        a.script_dir,
        a.lib_dir,
        a.config_file,
        a.tooling_nixpkgs,
        post_eval=a.post_eval,
        ref_namespace=a.script,
    )
    universe = build(tracker, backend)
    result = run_tracking(
        tracker, universe=universe, backend=backend, reader=PyGithubReader()
    )
    written = render(result, a.out)
    print(
        f"{tracker.id}: {result.done}/{result.total} done "
        f"({result.in_flight} in-flight) -> {written[-1].parent}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
