"""Anthropic (Claude) provider — the primary GenAI backend.

Uses the Messages API with structured outputs (``output_config.format``) so the
model returns JSON that already conforms to our learning-package schema. The
SDK reads ANTHROPIC_API_KEY (and optionally ANTHROPIC_BASE_URL) from the
environment automatically.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from .. import config
from .base import LLMProvider


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        import anthropic  # imported lazily so the package is optional

        self._client = (
            anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        )
        self.model = model or config.DEFAULT_ANTHROPIC_MODEL

    def generate_json(
        self, system: str, user: str, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=16000,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        # With output_config.format the first text block is guaranteed JSON.
        text = next((b.text for b in response.content if b.type == "text"), "")
        if not text:
            raise RuntimeError("Model returned no text content.")
        return json.loads(text)
