"""Maps file extensions to loaders."""

from __future__ import annotations

from pathlib import Path

from .base import ExtractedDocument
from . import markdown_loader, pdf_loader, text_loader

_LOADERS = {
    ".pdf": pdf_loader.load,
    ".md": markdown_loader.load,
    ".markdown": markdown_loader.load,
    ".txt": text_loader.load,
    ".text": text_loader.load,
}

SUPPORTED_EXTENSIONS = sorted(_LOADERS.keys())


def load_document(path: Path, media_dir: Path) -> ExtractedDocument:
    """Parse ``path`` into an :class:`ExtractedDocument`.

    ``media_dir`` is where extracted images are written.
    """
    ext = path.suffix.lower()
    loader = _LOADERS.get(ext)
    if loader is None:
        raise ValueError(
            f"Unsupported file type '{ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    media_dir.mkdir(parents=True, exist_ok=True)
    return loader(path, media_dir)
