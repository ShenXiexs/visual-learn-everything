"""PDF loader: extracts text and embedded images via PyMuPDF (fitz)."""

from __future__ import annotations

from pathlib import Path
from typing import List

from .. import config
from .base import ExtractedDocument, ExtractedImageFile


def load(path: Path, media_dir: Path) -> ExtractedDocument:
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "PDF support requires PyMuPDF. Install it with: pip install pymupdf"
        ) from exc

    doc = fitz.open(path)
    try:
        text_parts: List[str] = []
        images: List[ExtractedImageFile] = []
        seen_xrefs: set[int] = set()

        # Prefer embedded metadata; fall back to the first line of text below
        # (path.stem is a temp name like "source", so it's the last resort).
        title = (doc.metadata or {}).get("title") or ""

        for page_index in range(doc.page_count):
            page = doc.load_page(page_index)
            page_text = page.get_text("text").strip()
            if page_text:
                text_parts.append(page_text)

            if len(images) >= config.MAX_IMAGES:
                continue

            for img in page.get_images(full=True):
                if len(images) >= config.MAX_IMAGES:
                    break
                xref = img[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                saved = _save_image(fitz, doc, xref, media_dir, len(images), page_index + 1)
                if saved is not None:
                    images.append(saved)

        text = "\n\n".join(text_parts)
        if not str(title).strip():
            title = _first_nonempty_line(text) or path.stem
        return ExtractedDocument(
            title=str(title)[:200], text=text, source_type="pdf", images=images
        )
    finally:
        doc.close()


def _save_image(fitz, doc, xref, media_dir, index, page_number):
    """Extract one image by xref, normalising odd colourspaces to PNG."""
    try:
        pix = fitz.Pixmap(doc, xref)
        # Skip tiny images (icons, bullets, separators).
        if pix.width < 48 or pix.height < 48:
            pix = None
            return None
        if pix.n >= 5:  # CMYK or with alpha that fitz can't write directly
            pix = fitz.Pixmap(fitz.csRGB, pix)
        filename = f"img_{index:03d}.png"
        out_path = media_dir / filename
        pix.save(out_path)
        pix = None
        return ExtractedImageFile(
            path=out_path,
            caption=f"Figure {index + 1} (page {page_number})",
            page=page_number,
        )
    except Exception:
        return None


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:120]
    return ""
