from __future__ import annotations

import datetime as _dt
from pathlib import Path

from .model import AttrStatus, TrackerResult

DEFAULT_CHUNK_BYTES = 60000

# Reserved some space for PR attributions to prevent chunk misalignment on comment updates.
RESERVED_PRS = 3
PR_NUM_DIGITS = 7  # nixpkgs PRs are ~500k rn, so 10M is reasonable upper bound no?


def _attr_line(s: AttrStatus) -> str:
    box = "x" if s.done else " "
    refs = (" " + ", ".join(f"#{n}" for n in s.prs)) if s.prs else ""
    return f"- [{box}] {s.attr}{refs}"


def _reserved_ref_bytes(n: int = RESERVED_PRS) -> int:
    if n <= 0:
        return 0
    return 1 + n * (1 + PR_NUM_DIGITS) + (n - 1) * 2


def _budget_bytes(s: AttrStatus) -> int:
    base = f"- [ ] {s.attr}"
    return len(base.encode("utf-8")) + _reserved_ref_bytes() + 1


def _chunk(statuses: list[AttrStatus], limit: int) -> list[list[AttrStatus]]:
    chunks: list[list[AttrStatus]] = []
    cur: list[AttrStatus] = []
    size = 0
    for s in statuses:
        b = _budget_bytes(s)
        if cur and size + b > limit:
            chunks.append(cur)
            cur, size = [], 0
        cur.append(s)
        size += b
    if cur:
        chunks.append(cur)
    return chunks or [[]]


def render(
    result: TrackerResult,
    out_dir: str | Path,
    chunk_bytes: int = DEFAULT_CHUNK_BYTES,
) -> list[Path]:
    out = Path(out_dir) / result.tracker.id
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    chunks = _chunk(result.statuses, chunk_bytes)
    total = len(chunks)

    for i, chunk in enumerate(chunks, start=1):
        anchor = f"<!-- tracker:{result.tracker.id} chunk:{i:02d}/{total:02d} -->"
        lines = [_attr_line(s) for s in chunk]
        body = "\n".join([anchor, "", *lines, ""])
        path = out / f"{result.tracker.id}-comment-{i:02d}.md"
        path.write_text(body, encoding="utf-8")
        written.append(path)

    written.append(_render_index(result, out, total))
    return written


def _render_index(result: TrackerResult, out: Path, n_chunks: int) -> Path:
    t = result.tracker
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pct = (100 * result.done // result.total) if result.total else 0
    lines = [
        f"<!-- tracker:{t.id} index -->",
        f"Tracking: {t.repo}#{t.issue_number}",
        f"Baseline revision: `{result.creation_rev}`",
        f"Last checked against master: `{result.current_rev}`",
        f"Last updated: {now}",
        "",
        f"- Total: **{result.total}**",
        f"- Done: **{result.done}** ({pct}%)",
        f"- Remaining: **{result.remaining}**",
        f"- In-flight (open PR linked): **{result.in_flight}**",
        f"- Comment chunks: **{n_chunks}**",
        "",
    ]
    path = out / f"{t.id}-index.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
