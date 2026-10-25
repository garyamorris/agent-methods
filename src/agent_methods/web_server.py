"""Lightweight local web server hosting the interactive Agent Methods Visualizer."""

import http.server
import socketserver
import webbrowser
from pathlib import Path
from rich.console import Console

console = Console()

def serve_visualizer(port: int = 8000, open_browser: bool = True) -> None:
    """Serve the static web visualizer application on the specified local port."""
    web_dir = Path(__file__).resolve().parent / "web"
    if not web_dir.exists():
        console.print(f"[bold red]Error:[/bold red] Web directory not found at {web_dir}")
        return

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(web_dir), **kwargs)

        def log_message(self, format, *args):
            # Suppress noisy HTTP request logging in terminal
            pass

    # Allow port reuse
    socketserver.TCPServer.allow_reuse_address = True

    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            url = f"http://localhost:{port}"
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
    except Exception as e:
        console.print(f"[bold red]Failed to start server on port {port}:[/bold red] {e}")


if __name__ == "__main__":
    serve_visualizer()
