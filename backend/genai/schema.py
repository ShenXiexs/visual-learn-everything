"""JSON schema handed to the model's structured-output mode.

This is the generation contract. It deliberately uses a *fixed-depth* mind map
instead of a recursive ``$ref`` because the Anthropic structured-outputs subset
does not support recursive schemas. Four levels of nesting is plenty for a
readable mind map.

Constraints honoured for the strict subset:
  * every object sets ``additionalProperties: false``
  * every declared property is listed in ``required``
  * no string-length / numeric range constraints
"""

from __future__ import annotations


def _node(child_schema):
    """A mind-map node with the given (already-built) child node schema."""
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "title": {"type": "string", "description": "Short label for this node."},
            "children": {"type": "array", "items": child_schema},
        },
        "required": ["title", "children"],
    }


# Leaf level: a terminal node with no children. This breaks the chain without
# needing a recursive ``$ref`` (which structured outputs disallow).
_leaf = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "title": {"type": "string"},
    },
    "required": ["title"],
}

_level3 = _node(_leaf)
_level2 = _node(_level3)
_level1 = _node(_level2)

MINDMAP_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "title": {"type": "string", "description": "Central topic of the mind map."},
        "children": {"type": "array", "items": _level1},
    },
    "required": ["title", "children"],
}


LEARNING_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "title": {"type": "string", "description": "Concise title for the material."},
        "summary": {
            "type": "string",
            "description": "A clear 3-6 sentence overview a learner can read first.",
        },
        "mindmap": MINDMAP_SCHEMA,
        "key_concepts": {
            "type": "array",
            "description": "The most important terms/ideas with plain-language definitions.",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "term": {"type": "string"},
                    "definition": {"type": "string"},
                },
                "required": ["term", "definition"],
            },
        },
        "flashcards": {
            "type": "array",
            "description": "Question/answer pairs for active recall.",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "front": {"type": "string", "description": "Prompt side."},
                    "back": {"type": "string", "description": "Answer side."},
                },
                "required": ["front", "back"],
            },
        },
        "quiz": {
            "type": "array",
            "description": "Multiple-choice questions to test understanding.",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "question": {"type": "string"},
                    "options": {"type": "array", "items": {"type": "string"}},
                    "answer_index": {
                        "type": "integer",
                        "description": "0-based index of the correct option.",
                    },
                    "explanation": {"type": "string"},
                },
                "required": ["question", "options", "answer_index", "explanation"],
            },
        },
    },
    "required": ["title", "summary", "mindmap", "key_concepts", "flashcards", "quiz"],
}
