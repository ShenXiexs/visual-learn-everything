"""Central configuration, resolved from environment variables.

Nothing here is required to run the demo: with no API keys set, the app falls
back to the offline ``mock`` provider so it works out of the box.
"""

from __future__ import annotations

import os
from pathlib import Path

try:  # Optional convenience: load a local .env if python-dotenv is installed.
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional
    pass


# --- Paths ---------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = Path(os.getenv("VLE_DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)


# --- Ingestion limits ----------------------------------------------------
# Upper bound on characters sent to the model. The full document is never
# silently dropped: when we exceed this, we flag ``truncated`` in the response
# so the UI can tell the user only part of the document was analysed.
MAX_INPUT_CHARS = int(os.getenv("VLE_MAX_INPUT_CHARS", "120000"))

# Max upload size (bytes). Default 25 MB.
MAX_UPLOAD_BYTES = int(os.getenv("VLE_MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))

# Cap on images extracted per document (keeps the gallery and disk sane).
MAX_IMAGES = int(os.getenv("VLE_MAX_IMAGES", "40"))


# --- GenAI provider ------------------------------------------------------
def resolve_provider() -> str:
    """Pick the GenAI provider.

    Explicit ``LLM_PROVIDER`` wins; otherwise auto-detect from available keys,
    falling back to the offline ``mock`` provider.
    """
    explicit = os.getenv("LLM_PROVIDER")
    if explicit:
        return explicit.strip().lower()
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return "mock"


# Default model is the most capable Claude model. Override with LLM_MODEL.
DEFAULT_ANTHROPIC_MODEL = os.getenv("LLM_MODEL", "claude-opus-4-8")
DEFAULT_OPENAI_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
