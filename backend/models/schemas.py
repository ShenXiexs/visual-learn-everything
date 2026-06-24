"""Pydantic models for the learning package returned to the frontend.

These mirror ``backend/genai/schema.py`` (the JSON schema handed to the model's
structured-output mode). The schema there is the contract for generation; these
models validate and normalise whatever comes back before it reaches the UI.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class MindmapNode(BaseModel):
    title: str
    children: List["MindmapNode"] = Field(default_factory=list)


MindmapNode.model_rebuild()


class KeyConcept(BaseModel):
    term: str
    definition: str


class Flashcard(BaseModel):
    front: str
    back: str


class QuizItem(BaseModel):
    question: str
    options: List[str]
    answer_index: int
    explanation: str = ""


class ExtractedImage(BaseModel):
    id: str
    url: str
    caption: str = ""
    page: Optional[int] = None


class Meta(BaseModel):
    provider: str
    model: Optional[str] = None
    source_filename: str
    source_type: str
    char_count: int
    truncated: bool = False
    image_count: int = 0


class LearningPackage(BaseModel):
    """The full, interactive learning bundle generated from one document."""

    title: str
    summary: str
    mindmap: MindmapNode
    key_concepts: List[KeyConcept] = Field(default_factory=list)
    flashcards: List[Flashcard] = Field(default_factory=list)
    quiz: List[QuizItem] = Field(default_factory=list)
    images: List[ExtractedImage] = Field(default_factory=list)
    meta: Optional[Meta] = None
