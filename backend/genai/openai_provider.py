"""OpenAI provider (optional alternative backend).

Uses the Chat Completions API with JSON Schema response formatting. Reads
OPENAI_API_KEY from the environment.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from .. import config
from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        import openai  # imported lazily so the package is optional

        self._client = (
            openai.OpenAI(api_key=api_key) if api_key else openai.OpenAI()
        )
        self.model = model or config.DEFAULT_OPENAI_MODEL

    def generate_json(
        self, system: str, user: str, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "learning_package",
                    "strict": True,
                    "schema": schema,
                },
            },
        )
        text = response.choices[0].message.content or ""
        if not text:
            raise RuntimeError("Model returned no content.")
        return json.loads(text)
