"""Orchestrates: extracted document -> GenAI -> validated learning package."""

from __future__ import annotations

from .. import config
from ..genai import get_provider
from ..genai.prompts import SYSTEM_PROMPT, build_user_prompt
from ..genai.schema import LEARNING_SCHEMA
from ..ingestion.base import ExtractedDocument
from ..models.schemas import (
    ExtractedImage,
    LearningPackage,
    Meta,
)


def build_learning_package(
    doc: ExtractedDocument,
    job_id: str,
    source_filename: str,
) -> LearningPackage:
    """Turn a parsed document into a validated :class:`LearningPackage`."""
    full_len = len(doc.text)
    truncated = full_len > config.MAX_INPUT_CHARS
    text = doc.text[: config.MAX_INPUT_CHARS]

    provider = get_provider()
    user_prompt = build_user_prompt(doc.title, text)

    raw = provider.generate_json(SYSTEM_PROMPT, user_prompt, LEARNING_SCHEMA)

    # Validate / normalise the model output.
    package = LearningPackage.model_validate(raw)

    # Attach images extracted during ingestion (served from /media/<job_id>/).
    package.images = [
        ExtractedImage(
            id=img.path.name,
            url=f"/media/{job_id}/{img.path.name}",
            caption=img.caption,
            page=img.page,
        )
        for img in doc.images
    ]

    package.meta = Meta(
        provider=provider.name,
        model=provider.model,
        source_filename=source_filename,
        source_type=doc.source_type,
        char_count=full_len,
        truncated=truncated,
        image_count=len(package.images),
    )
    return package
