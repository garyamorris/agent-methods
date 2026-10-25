"""Configuration management for the agent-methods testbed powered by DeepSeek."""

import os
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
import agents

# Automatically look for .env in current working directory and parent paths
load_dotenv()

# DeepSeek Configuration (Default Provider)
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEFAULT_MODEL = os.getenv("DEEPSEEK_DEFAULT_MODEL", os.getenv("DEFAULT_MODEL", "deepseek-chat"))


def get_api_key() -> str | None:
    """Return the configured DeepSeek API key (or OpenAI fallback)."""
    return os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")


def is_using_deepseek() -> bool:
    """Check if the active configuration routes through DeepSeek."""
    return bool(os.getenv("DEEPSEEK_API_KEY")) or "deepseek" in DEFAULT_MODEL.lower()


def configure_model_client() -> str:
    """Configure the OpenAI Agents SDK to use DeepSeek or OpenAI client.

    Returns:
        The validated API key.
    """
    api_key = get_api_key()
    if not api_key or not api_key.strip() or api_key.startswith("sk-proj-..."):
        raise RuntimeError(
            "Neither DEEPSEEK_API_KEY nor OPENAI_API_KEY is configured.\n"
            "Please export DEEPSEEK_API_KEY='sk-...' or set it in your .env file."
        )

    # Disable remote OpenAI telemetry tracing when using DeepSeek/custom providers to prevent 401s
    agents.set_tracing_disabled(True)

    if is_using_deepseek():
        # Wire DeepSeek's OpenAI-compatible endpoint into the SDK
        client = AsyncOpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
        agents.set_default_openai_client(client)
        agents.set_default_openai_api("chat_completions")
    else:
        agents.set_default_openai_key(api_key)

    return api_key


def ensure_api_key() -> str:
    """Ensure the model provider is initialized and return the API key."""
    return configure_model_client()


# Auto-configure on initial import if an API key is available
try:
    if get_api_key():
        configure_model_client()
except Exception:
    pass
