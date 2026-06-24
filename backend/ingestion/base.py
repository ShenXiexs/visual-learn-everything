"""Shared types for the ingestion layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class ExtractedImageFile:
    """An image pulled out of a source document and written to disk."""

    path: Path
    caption: str = ""
    page: Optional[int] = None


@dataclass
class ExtractedDocument:
    """Normalised result of parsing one uploaded file."""

    title: str
    text: str
    source_type: str  # "pdf" | "markdown" | "text"
    images: List[ExtractedImageFile] = field(default_factory=list)
