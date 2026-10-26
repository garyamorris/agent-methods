"""Rich terminal UI helpers and visual tracers for agent-methods."""

from typing import Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text

console = Console()

def print_header(title: str, subtitle: str = "") -> None:
    """Print an attractive header banner."""
    content = f"[bold cyan]{title}[/bold cyan]"
    if subtitle:
        content += f"\n[dim]{subtitle}[/dim]"
    console.print(Panel(content, border_style="cyan", expand=False))

def print_section(title: str) -> None:
    """Print a section divider."""
    console.print()
    console.rule(f"[bold yellow]{title}[/bold yellow]")
    console.print()

def print_agent_step(agent_name: str, action: str, details: str = "", style: str = "green") -> None:
    """Print a step in the multi-agent communication trace."""
    badge = f"[{style}]● [{agent_name}][/{style}] [bold]{action}[/bold]"
    if details:
        console.print(f"  {badge}: {details}")
    else:
        console.print(f"  {badge}")

def print_tool_call(tool_name: str, args: Any, result: str | None = None) -> None:
    """Format a tool invocation and optional result."""
    if isinstance(args, dict):
        arg_str = ", ".join(f"{k}={v!r}" for k, v in args.items())
    elif isinstance(args, str):
        try:
            import json
            parsed = json.loads(args)
            if isinstance(parsed, dict):
                arg_str = ", ".join(f"{k}={v!r}" for k, v in parsed.items())
            else:
                arg_str = str(args)
        except Exception:
            arg_str = args
    else:
        arg_str = str(args)

    console.print(f"    [magenta]↳ [TOOL CALL][/magenta] [bold]{tool_name}[/bold]({arg_str})")
    if result is not None:
        console.print(f"    [dim green]↳ [TOOL RETURN][/dim green] {result}")

def print_handoff(from_agent: str, to_agent: str, reason: str = "") -> None:
    """Format an agent handoff."""
    msg = f"  [bold yellow]⇄ [HANDOFF][/bold yellow] [bold]{from_agent}[/bold] ➔ [bold]{to_agent}[/bold]"
    if reason:
        msg += f" [dim]({reason})[/dim]"
    console.print(msg)

def print_result_panel(title: str, content: str, style: str = "bold green") -> None:
    """Print a formatted result box."""
    console.print()
    console.print(Panel(content, title=f"[{style}]{title}[/{style}]", border_style="green"))
    console.print()

def print_explainer(summary: str, when_to_use: list[str], communication_mechanism: str) -> None:
    """Print a structured educational explainer table before running."""
    table = Table(title="Architecture Deep-Dive", show_header=True, header_style="bold magenta")
    table.add_column("Concept", style="cyan", width=22)
    table.add_column("Details", style="white")

    table.add_row("Core Pattern", summary)
    table.add_row("Communication", communication_mechanism)
    table.add_row("When To Use", "\n".join(f"• {u}" for u in when_to_use))

    console.print(table)
    console.print()
