"""Configuration management for the agent-methods testbed."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Automatically look for .env in current working directory and parent paths
load_dotenv()

DEFAULT_MODEL = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini")

def get_api_key() -> str | None:
    """Return the configured OpenAI API key or None."""
    return os.getenv("OPENAI_API_KEY")

def ensure_api_key() -> str:
    """Ensure an OpenAI API key is set; raise RuntimeError with helpful instructions if not."""
    key = get_api_key()
    if not key or not key.strip() or key.startswith("sk-proj-..."):
        raise RuntimeError(
            "OPENAI_API_KEY is not set or contains a placeholder.\n"
            "Please export OPENAI_API_KEY='your-key' or set it in a .env file."
        )
    return key
