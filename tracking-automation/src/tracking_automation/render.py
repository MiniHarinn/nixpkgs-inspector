from __future__ import annotations

import datetime as _dt
from pathlib import Path

from .model import AttrStatus, TrackerResult

DEFAULT_CHUNK_BYTES = 60000


def _attr_line(s: AttrStatus) -> str:
    box = "x" if s.done else " "
    refs = (" " + ", ".join(f"#{n}" for n in s.prs)) if s.prs else ""
    return f"- [{box}] {s.attr}{refs}"


def _chunk_lines(lines: list[str], limit: int) -> list[list[str]]:
    chunks: list[list[str]] = []
    cur: list[str] = []
    size = 0
    for line in lines:
        ln = len(line.encode("utf-8")) + 1
        if cur and size + ln > limit:
            chunks.append(cur)
            cur, size = [], 0
        cur.append(line)
        size += ln
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

    lines = [_attr_line(s) for s in result.statuses]
    chunks = _chunk_lines(lines, chunk_bytes)
    total = len(chunks)

    for i, chunk in enumerate(chunks, start=1):
        anchor = f"<!-- tracker:{result.tracker.id} chunk:{i:02d}/{total:02d} -->"
        body = "\n".join([anchor, "", *chunk, ""])
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
        f"Universe pinned at: `{result.creation_rev}`",
        f"Evaluated at master: `{result.current_rev}`",
        f"Generated: {now}",
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
