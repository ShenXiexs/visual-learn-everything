"""Markdown (.md / .markdown) loader.

We keep the raw markdown as the text to analyse (headings and structure help
the model build a better mind map). The first ``# H1`` becomes the title.
"""

from __future__ import annotations

import re
from pathlib import Path

from .base import ExtractedDocument

_H1 = re.compile(r"^\s{0,3}#\s+(.+?)\s*$", re.MULTILINE)


def load(path: Path, media_dir: Path) -> ExtractedDocument:  # noqa: ARG001
    raw = path.read_text(encoding="utf-8", errors="replace")
    m = _H1.search(raw)
    title = (m.group(1).strip() if m else None) or path.stem
    return ExtractedDocument(title=title, text=raw, source_type="markdown", images=[])
