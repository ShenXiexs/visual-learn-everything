"""Provider interface.

A provider takes a system prompt, a user prompt, and a JSON schema, and returns
a Python ``dict`` that conforms to that schema.
"""

from __future__ import annotations

import abc
from typing import Any, Dict, Optional


class LLMProvider(abc.ABC):
    name: str = "base"
    model: Optional[str] = None

    @abc.abstractmethod
    def generate_json(
        self, system: str, user: str, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Return a dict matching ``schema``."""
        raise NotImplementedError
