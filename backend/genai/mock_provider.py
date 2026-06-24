"""Offline, dependency-free provider.

Lets the whole pipeline run with no API key so the demo works out of the box.
It uses simple heuristics (headings, paragraphs, term frequency) to build a
plausible learning package. The output is intentionally modest — it exists to
prove the flow end-to-end, not to rival a real model.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List

from .base import LLMProvider

_STOPWORDS = set(
    """a an the and or but if then else for to of in on at by with from as is are was
    were be been being this that these those it its it's we you they he she them his her
    their our your my i me will would can could should may might must not no nor so than
    too very just also into over under more most some such only own same other which who
    whom what when where why how all any each few many much both either neither""".split()
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?。！？])\s+")
_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$")
_WORD = re.compile(r"[A-Za-z][A-Za-z\-']{2,}")


class MockProvider(LLMProvider):
    name = "mock"
    model = "heuristic-offline"

    def generate_json(
        self, system: str, user: str, schema: Dict[str, Any]  # noqa: ARG002
    ) -> Dict[str, Any]:
        title, text = _parse_prompt(user)
        sections = _split_sections(text)
        sentences = _sentences(text)

        summary = " ".join(sentences[:4]) if sentences else "No readable content was found."
        keywords = _keywords(text, limit=8)

        key_concepts = _key_concepts(keywords, sentences)
        flashcards = _flashcards(key_concepts, sections)
        quiz = _quiz(keywords, sentences)
        mindmap = _mindmap(title, sections, keywords)

        return {
            "title": title or "Learning Material",
            "summary": summary,
            "mindmap": mindmap,
            "key_concepts": key_concepts,
            "flashcards": flashcards,
            "quiz": quiz,
        }


# --- prompt parsing ------------------------------------------------------
def _parse_prompt(user: str):
    title = ""
    m = re.search(r"Document title:\s*(.+)", user)
    if m:
        title = m.group(1).strip()
    body = user
    inner = re.search(r"<<<DOCUMENT\n(.*)\nDOCUMENT>>>", user, re.DOTALL)
    if inner:
        body = inner.group(1)
    return title, body


# --- text helpers --------------------------------------------------------
def _sentences(text: str) -> List[str]:
    flat = " ".join(line.strip() for line in text.splitlines() if line.strip())
    flat = re.sub(r"#+\s*", "", flat)
    parts = [s.strip() for s in _SENTENCE_SPLIT.split(flat) if len(s.strip()) > 20]
    return parts


def _split_sections(text: str):
    """Group content by markdown headings; fall back to paragraph chunks."""
    sections: List[Dict[str, Any]] = []
    current = {"title": "Overview", "lines": []}
    found_heading = False
    for line in text.splitlines():
        m = _HEADING.match(line)
        if m:
            found_heading = True
            if current["lines"]:
                sections.append(current)
            current = {"title": m.group(2).strip()[:80], "lines": []}
        elif line.strip():
            current["lines"].append(line.strip())
    if current["lines"]:
        sections.append(current)

    if not found_heading:
        # No headings: chunk paragraphs into pseudo-sections.
        paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        sections = []
        for i, para in enumerate(paras[:6]):
            first = _sentences(para)
            head = (first[0] if first else para)[:60]
            sections.append({"title": head, "lines": [para]})
    return sections or [{"title": "Overview", "lines": [text[:400]]}]


def _keywords(text: str, limit: int) -> List[str]:
    words = [w.lower() for w in _WORD.findall(text)]
    counts = Counter(w for w in words if w not in _STOPWORDS)
    return [w for w, _ in counts.most_common(limit)]


# --- learning-package pieces --------------------------------------------
def _key_concepts(keywords, sentences):
    concepts = []
    for kw in keywords[:6]:
        definition = next(
            (s for s in sentences if kw in s.lower()),
            f"A key term that appears frequently in this document.",
        )
        concepts.append({"term": kw.capitalize(), "definition": definition[:240]})
    if not concepts:
        concepts.append(
            {"term": "Overview", "definition": "This document's main subject."}
        )
    return concepts


def _flashcards(key_concepts, sections):
    cards = [
        {"front": f"What is '{c['term']}'?", "back": c["definition"]}
        for c in key_concepts
    ]
    for sec in sections[:4]:
        body = " ".join(sec["lines"])
        first = _sentences(body)
        if first:
            cards.append(
                {"front": f"Summarise: {sec['title']}", "back": first[0][:240]}
            )
    return cards[:12] or [{"front": "What did you learn?", "back": "Review the summary."}]


def _quiz(keywords, sentences):
    quiz = []
    for kw in keywords[:4]:
        context = next((s for s in sentences if kw in s.lower()), "")
        if not context:
            continue
        distractors = [k.capitalize() for k in keywords if k != kw][:3]
        options = [kw.capitalize()] + distractors
        if len(options) < 2:
            options = [kw.capitalize(), "None of the above"]
        quiz.append(
            {
                "question": f"Which term does this describe? \"{context[:140]}\"",
                "options": options,
                "answer_index": 0,
                "explanation": f"The sentence is about '{kw}'.",
            }
        )
    if not quiz:
        quiz.append(
            {
                "question": "Did the document load successfully?",
                "options": ["Yes", "No"],
                "answer_index": 0,
                "explanation": "If you can read the summary, ingestion worked.",
            }
        )
    return quiz


def _mindmap(title, sections, keywords):
    children = []
    for sec in sections[:7]:
        body = " ".join(sec["lines"])
        points = _sentences(body)[:3]
        sub = [{"title": p[:70], "children": []} for p in points]
        children.append({"title": sec["title"][:60], "children": sub})
    if not children:
        children = [{"title": k.capitalize(), "children": []} for k in keywords[:6]]
    return {"title": (title or "Topic")[:60], "children": children}
