"""Optional file helpers preserving the source script's local I/O semantics."""

from __future__ import annotations

from pathlib import Path


def read_input_content(
    path: str | Path,
    *,
    max_lines: int | None = None,
    max_chars: int | None = None,
) -> str:
    target = Path(path)
    if not target.exists():
        return ""
    text = target.read_text(encoding="utf-8").strip()
    if not text:
        return ""
    lines = text.splitlines()
    if max_lines and len(lines) > max_lines:
        text = "\n".join(lines[:max_lines])
    if max_chars and len(text) > max_chars:
        text = text[:max_chars]
    return text


def write_output(path: str | Path, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")
