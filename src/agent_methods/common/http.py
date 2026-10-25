"""Resilient HTTP client helper for querying real public APIs."""

import json
from typing import Any
import httpx

# Shared persistent client with standard timeout and user agent
DEFAULT_HEADERS = {
    "User-Agent": "agent-methods-research-testbed/1.0 (https://github.com/garyamorris/agent-methods)",
    "Accept": "application/json",
}

def fetch_json(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 8.0,
) -> dict[str, Any]:
    """Execute a real HTTP GET request returning parsed JSON, with graceful error handling.

    Args:
        url: The API endpoint URL.
        params: Optional query string parameters.
        headers: Optional additional HTTP request headers.
        timeout: Request timeout in seconds.

    Returns:
        Dictionary containing either the live API response payload or an error structure.
    """
    req_headers = dict(DEFAULT_HEADERS)
    if headers:
        req_headers.update(headers)

    try:
        with httpx.Client(timeout=timeout, headers=req_headers, follow_redirects=True) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP {e.response.status_code} from {url}",
            "status_code": e.response.status_code,
            "url": url,
        }
    except Exception as e:
        return {
            "error": f"Failed connecting to {url}: {str(e)}",
            "url": url,
        }
