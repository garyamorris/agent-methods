"""Asynchronous ASGI Web Server & Live Streaming Comms Backend for Agent Methods.

Provides real-time Server-Sent Events (SSE) streaming inter-agent communication packets,
tool invocations against real public APIs, and multi-agent handoffs directly to the browser.
"""

import asyncio
import json
import socket
import sys
import webbrowser
from pathlib import Path
from typing import Any
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, FileResponse, Response
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from agent_methods.patterns import PATTERNS
from agent_methods.common import console, CommsTracer, CommsPacket

WEB_DIR = Path(__file__).resolve().parent / "web"
INDEX_HTML = WEB_DIR / "index.html"


async def get_index(request: Request) -> Response:
    """Serve the interactive web visualizer frontend."""
    return FileResponse(INDEX_HTML)


async def get_patterns(request: Request) -> JSONResponse:
    """Return JSON metadata for all 15 multi-agent patterns."""
    data = []
    for k, v in PATTERNS.items():
        data.append({
            "key": k,
            "id": v["id"],
            "name": v["name"],
            "description": v["description"],
            "topology": v["topology"],
        })
    return JSONResponse(data)


async def run_scenario_stream(request: Request) -> Response:
    """Execute a pattern against DeepSeek and stream live inter-agent comms packets via SSE."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    pattern_key = str(body.get("pattern_id", "1"))
    example_id = int(body.get("example_id", 1))
    custom_query = body.get("custom_query") or None

    p_info = PATTERNS.get(pattern_key)
    if not p_info:
        for k, v in PATTERNS.items():
            if v["id"] == pattern_key:
                p_info = v
                break

    if not p_info:
        return JSONResponse({"error": f"Unknown pattern '{pattern_key}'"}, status_code=404)

    mod = p_info["module"]
    queue: asyncio.Queue[Any] = asyncio.Queue()

    def packet_listener(pkt: CommsPacket) -> None:
        queue.put_nowait(pkt)

    async def execute_agent_worker() -> None:
        try:
            tracer = CommsTracer(scenario_title=p_info["name"], display_live=False, event_listener=packet_listener)

            # Inspect run() parameters
            import inspect
            sig = inspect.signature(mod.run)
            kwargs: dict[str, Any] = {}
            if custom_query:
                kwargs["query"] = custom_query
            if "example_id" in sig.parameters:
                kwargs["example_id"] = example_id
            if "tracer" in sig.parameters:
                kwargs["tracer"] = tracer

            # Run pattern
            final_output = await mod.run(**kwargs)
            await queue.put({"type": "DONE", "final_output": str(final_output)})
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            await queue.put({"type": "ERROR", "error": str(e), "traceback": tb})

    async def event_generator():
        # Yield initial connected event
        yield {
            "event": "connected",
            "data": json.dumps({"pattern": p_info["name"], "example_id": example_id}),
        }

        # Start agent execution in background task
        worker_task = asyncio.create_task(execute_agent_worker())

        while True:
            try:
                # Wait for next packet with timeout
                item = await asyncio.wait_for(queue.get(), timeout=90.0)
                if isinstance(item, CommsPacket):
                    yield {
                        "event": "packet",
                        "data": json.dumps(item.to_dict()),
                    }
                elif isinstance(item, dict):
                    if item.get("type") == "DONE":
                        yield {
                            "event": "done",
                            "data": json.dumps(item),
                        }
                        break
                    elif item.get("type") == "ERROR":
                        yield {
                            "event": "error",
                            "data": json.dumps(item),
                        }
                        break
                    else:
                        yield {
                            "event": "packet",
                            "data": json.dumps(item),
                        }
            except asyncio.TimeoutError:
                yield {
                    "event": "heartbeat",
                    "data": json.dumps({"status": "running"}),
                }
            except Exception as e:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(e)}),
                }
                break

        if not worker_task.done():
            worker_task.cancel()

    return EventSourceResponse(event_generator())


app = Starlette(
    routes=[
        Route("/", get_index),
        Route("/index.html", get_index),
        Route("/api/patterns", get_patterns),
        Route("/api/run", run_scenario_stream, methods=["POST"]),
    ]
)


def find_free_port(candidates: list[int]) -> int:
    """Find the first bindable TCP port from a list of candidates."""
    for port in candidates:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    return 8080


def serve_visualizer(port: int = 8080, open_browser: bool = True) -> None:
    """Serve the interactive web visualizer application with live SSE streaming."""
    if not WEB_DIR.exists():
        console.print(f"[bold red]Error:[/bold red] Web directory not found at {WEB_DIR}")
        return

    candidate_ports = [port, 8080, 8888, 8000, 8081, 3000]
    actual_port = find_free_port(candidate_ports)
    url = f"http://localhost:{actual_port}"

    console.print()
    console.print(f"[bold green]✓ Agent Methods Live Streaming Visualizer running at:[/bold green] [bold cyan]{url}[/bold cyan]")
    console.print("[dim]Press Ctrl+C to stop the visualizer server.[/dim]\n")

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    uvicorn.run(app, host="127.0.0.1", port=actual_port, log_level="warning")


if __name__ == "__main__":
    serve_visualizer()
