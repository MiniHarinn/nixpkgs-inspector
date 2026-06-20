from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import Protocol

_REF_NS = "refs/nixpkgs-tracker"
_PR_SUBJECT = re.compile(r"\(#(\d+)\)\s*$")
_CHECK_CHUNK = 1000  # `nix eval --expr` arg caps at 128 KiB; chunk attr lists
_EVAL_TIMEOUT = 1800
_COLLECT_TIMEOUT = 3600


class Evaluator(Protocol):
    def collect(self, rev: str) -> list[dict]: ...
    def check_at(self, rev: str, attrs: Iterable[str]) -> set[str]: ...


class Attribution(Protocol):
    def current_rev(self) -> str: ...
    def merge_commit(self, number: int) -> str | None: ...
    def landing_commit(self, number: int) -> str | None: ...
    def first_parent_changed_files(self, commit: str) -> list[str]: ...


def _bundled(name: str) -> Path:
    return Path(__file__).resolve().parent / name


def _attrs_literal(attrs: Iterable[str]) -> str:
    return "[ " + " ".join(f'"{a}"' for a in attrs) + " ]"


class CheckoutManager:
    def __init__(
        self,
        worktree: str | Path,
        script_dir: str | Path,
        lib_dir: str | Path,
        config_file: str | Path,
        tooling_nixpkgs: str | Path,
        *,
        remote: str = "upstream",
        base_branch: str = "master",
        ref_namespace: str | None = None,
    ):
        self.worktree = str(Path(worktree).expanduser().resolve())
        self.script_dir = str(Path(script_dir).expanduser().resolve())
        self.lib_dir = str(Path(lib_dir).expanduser().resolve())
        self.config_file = str(Path(config_file).expanduser().resolve())
        self.tooling_nixpkgs = str(Path(tooling_nixpkgs).expanduser().resolve())
        self.remote = remote
        self.base_branch = base_branch
        self.check_nix = _bundled("check.nix")
        self.collect_nix = _bundled("collect.nix")
        self._landing: dict[int, str] | None = None
        self._base_tip: str | None = None
        # Per-leg namespace: concurrent worktrees share one object store.
        leg = ref_namespace or Path(self.script_dir).name
        self._ref_ns = f"{_REF_NS}/{leg}"

    # ---- git ----------------------------------------------------------------

    def _git(self, *args: str, check: bool = True) -> str:
        proc = subprocess.run(
            ["git", "-C", self.worktree, *args], capture_output=True, text=True
        )
        if check and proc.returncode != 0:
            raise subprocess.CalledProcessError(
                proc.returncode, ("git", *args), proc.stdout, proc.stderr
            )
        return proc.stdout.strip()

    def _checkout(self, rev: str) -> None:
        self._git("checkout", "--quiet", "--detach", rev)

    # ---- attribution --------------------------------------------------------

    def current_rev(self) -> str:
        self._clean_refs()
        tip = self._git("rev-parse", self.base_branch)
        self._checkout(tip)
        self._base_tip = tip
        return tip

    def merge_commit(self, number: int) -> str | None:
        ref = f"{self._ref_ns}/{number}/merge"
        rc = subprocess.run(
            [
                "git", "-C", self.worktree, "fetch", "--quiet", self.remote,
                f"refs/pull/{number}/merge:{ref}",
            ],
            capture_output=True, text=True,
        )
        return ref if rc.returncode == 0 else None

    def prime_landing_map(self, creation_rev: str) -> None:
        out = self._git("log", "--pretty=%H %s", f"{creation_rev}..{self.base_branch}")
        m: dict[int, str] = {}
        for line in out.splitlines():
            sha, _, subject = line.partition(" ")
            hit = _PR_SUBJECT.search(subject)
            if hit:
                m[int(hit.group(1))] = sha
        self._landing = m

    def landing_commit(self, number: int) -> str | None:
        if self._landing is None:
            raise RuntimeError("call prime_landing_map(creation_rev) first")
        return self._landing.get(number)

    def first_parent_changed_files(self, commit: str) -> list[str]:
        out = self._git("diff", "--name-only", f"{commit}^1", commit)
        return [line for line in out.splitlines() if line]

    # ---- eval ---------------------------------------------------------------

    def _harness_args(self) -> str:
        return (
            f"nixpkgs = {self.worktree}; "
            f"scriptDir = {self.script_dir}; "
            f"libDir = {self.lib_dir}; "
            f"configFile = {self.config_file}; "
            f"toolingNixpkgs = {self.tooling_nixpkgs}; "
        )

    def _nix_eval(self, expr: str, *, fmt: str, timeout: int) -> str:
        proc = subprocess.run(
            ["nix", "eval", "--impure", fmt, "--expr", expr],
            cwd=self.worktree, capture_output=True, text=True, timeout=timeout,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"nix eval failed:\n{proc.stderr.strip()[:500]}")
        return proc.stdout

    def collect(self, rev: str) -> list[dict]:
        self._checkout(rev)
        expr = f"import {self.collect_nix} {{ {self._harness_args()}}}"
        return json.loads(self._nix_eval(expr, fmt="--json", timeout=_COLLECT_TIMEOUT))

    def check_at(self, rev: str, attrs: Iterable[str]) -> set[str]:
        attrs = list(attrs)
        if not attrs:
            return set()
        self._checkout(rev)
        result: set[str] = set()
        for i in range(0, len(attrs), _CHECK_CHUNK):
            result |= self._check(attrs[i : i + _CHECK_CHUNK])
        return result

    def _check(self, attrs: list[str]) -> set[str]:
        expr = (
            f"import {self.check_nix} {{ {self._harness_args()}"
            f"attrs = {_attrs_literal(attrs)}; }}"
        )
        out = self._nix_eval(expr, fmt="--raw", timeout=_EVAL_TIMEOUT)
        return {line for line in out.split("\n") if line}

    # ---- cleanup ------------------------------------------------------------

    def restore(self) -> None:
        if self._base_tip:
            self._checkout(self._base_tip)
        self._clean_refs()

    def _clean_refs(self) -> None:
        for line in self._git(
            "for-each-ref", "--format=%(refname)", self._ref_ns
        ).splitlines():
            if line:
                self._git("update-ref", "-d", line, check=False)
