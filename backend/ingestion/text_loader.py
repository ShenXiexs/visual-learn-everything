"""Plain-text (.txt) loader."""

from __future__ import annotations

from pathlib import Path

from .base import ExtractedDocument


def load(path: Path, media_dir: Path) -> ExtractedDocument:  # noqa: ARG001
    raw = path.read_text(encoding="utf-8", errors="replace")
    title = _first_nonempty_line(raw) or path.stem
    return ExtractedDocument(title=title, text=raw, source_type="text", images=[])


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:120]
    return ""
