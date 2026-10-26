"""Common utilities for agent-methods."""
from .config import (
    DEFAULT_MODEL,
    DEEPSEEK_BASE_URL,
    get_api_key,
    ensure_api_key,
    is_using_deepseek,
    configure_model_client,
)
from .http import fetch_json
from .ui import (
    console,
    print_header,
    print_section,
    print_agent_step,
    print_tool_call,
    print_handoff,
    print_result_panel,
    print_explainer,
)
from .tracer import CommsTracer, CommsPacket

__all__ = [
    "DEFAULT_MODEL",
    "DEEPSEEK_BASE_URL",
    "get_api_key",
    "ensure_api_key",
    "is_using_deepseek",
    "configure_model_client",
    "fetch_json",
    "console",
    "print_header",
    "print_section",
    "print_agent_step",
    "print_tool_call",
    "print_handoff",
    "print_result_panel",
    "print_explainer",
    "CommsTracer",
    "CommsPacket",
]
