"""Lightweight local web server hosting the interactive Agent Methods Visualizer."""

import http.server
import socketserver
import webbrowser
from pathlib import Path
from rich.console import Console

console = Console()

def serve_visualizer(port: int = 8080, open_browser: bool = True) -> None:
    """Serve the static web visualizer application on an available local port."""
    web_dir = Path(__file__).resolve().parent / "web"
    if not web_dir.exists():
        console.print(f"[bold red]Error:[/bold red] Web directory not found at {web_dir}")
        return

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(web_dir), **kwargs)

        def log_message(self, format, *args):
            pass

    socketserver.TCPServer.allow_reuse_address = True

    candidate_ports = [port, 8080, 8888, 8000, 8081, 3000]
    httpd = None
    actual_port = None

    for p in candidate_ports:
        try:
            httpd = socketserver.TCPServer(("", p), Handler)
            actual_port = p
            break
        except OSError:
            continue

    if not httpd:
        console.print("[bold red]Failed to bind to any candidate port.[/bold red]")
        return

    try:
        with httpd:
            url = f"http://localhost:{actual_port}"
            console.print()
            console.print(f"[bold green]✓ Agent Methods Visualizer running at:[/bold green] [bold cyan]{url}[/bold cyan]")
            console.print("[dim]Press Ctrl+C to stop the visualizer server.[/dim]\n")
            if open_browser:
                try:
                    webbrowser.open(url)
                except Exception:
                    pass
            httpd.serve_forever()
    except KeyboardInterrupt:
        console.print("\n[yellow]Visualizer server stopped.[/yellow]")


if __name__ == "__main__":
    serve_visualizer()
