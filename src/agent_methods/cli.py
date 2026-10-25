"""Interactive CLI explorer and runner for multi-agent architectures."""

import asyncio
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from agent_methods.patterns import PATTERNS
from agent_methods.common import console, print_header

def display_patterns_table() -> None:
    """Render a formatted comparison table of all available agent architectures."""
    table = Table(
        title="Multi-Agent Communication Architectures Bed",
        show_header=True,
        header_style="bold magenta",
        expand=True,
    )
    table.add_column("#", style="bold cyan", width=4, justify="center")
    table.add_column("Architecture Pattern", style="bold white", width=30)
    table.add_column("Topology", style="yellow", width=22)
    table.add_column("Communication Style & Purpose", style="dim")

    for key, p in PATTERNS.items():
        table.add_row(key, p["name"], p["topology"], p["description"])

    console.print(table)
    console.print()


async def run_pattern(pattern_key: str, custom_input: str | None = None) -> None:
    """Execute a selected pattern by number or ID."""
    p_info = PATTERNS.get(pattern_key)
    if not p_info:
        # Search by id
        for k, v in PATTERNS.items():
            if v["id"] == pattern_key:
                p_info = v
                break

    if not p_info:
        console.print(f"[bold red]Error:[/bold red] Unknown pattern '{pattern_key}'.")
        console.print("Valid choices are 1 through 10.")
        return

    mod = p_info["module"]
    try:
        if custom_input:
            await mod.run(custom_input)
        else:
            await mod.run()
    except Exception as e:
        console.print(f"\n[bold red]Execution Error in {p_info['name']}:[/bold red] {e}\n")


def print_pattern_explanation(pattern_key: str) -> None:
    """Print the architectural overview docstring of a pattern."""
    p_info = PATTERNS.get(pattern_key)
    if not p_info:
        for k, v in PATTERNS.items():
            if v["id"] == pattern_key:
                p_info = v
                break

    if not p_info:
        console.print(f"[bold red]Error:[/bold red] Unknown pattern '{pattern_key}'.")
        return

    mod = p_info["module"]
    doc = mod.__doc__ or "No documentation provided."
    console.print(Panel(doc.strip(), title=f"[bold cyan]{p_info['name']} Architecture[/bold cyan]", border_style="cyan"))


def main() -> None:
    """CLI entrypoint."""
    args = sys.argv[1:]

    if not args:
        # Interactive mode
        print_header(
            "Agent Methods Lab",
            "Educational testbed of agent architectures & communication topologies (OpenAI Agents SDK)",
        )
        display_patterns_table()

        choice = Prompt.ask(
            "[bold green]Select a pattern to run (1-10), 'e <id>' to explain, or 'q' to quit[/bold green]",
            default="1",
        )

        if choice.lower() in ("q", "quit", "exit"):
            console.print("[dim]Goodbye![/dim]")
            return

        if choice.lower().startswith("e "):
            target_key = choice.split()[1]
            print_pattern_explanation(target_key)
            return

        asyncio.run(run_pattern(choice))
        return

    cmd = args[0].lower()
    if cmd in ("list", "ls"):
        display_patterns_table()
    elif cmd in ("explain", "info") and len(args) > 1:
        print_pattern_explanation(args[1])
    elif cmd in ("run",) and len(args) > 1:
        user_input = " ".join(args[2:]) if len(args) > 2 else None
        asyncio.run(run_pattern(args[1], user_input))
    elif cmd in PATTERNS:
        user_input = " ".join(args[1:]) if len(args) > 1 else None
        asyncio.run(run_pattern(cmd, user_input))
    else:
        console.print("[bold red]Usage:[/bold red]")
        console.print("  python main.py                     (Interactive Menu)")
        console.print("  python main.py list                (List all patterns)")
        console.print("  python main.py run <1-10> [query]  (Run a specific pattern)")
        console.print("  python main.py explain <1-10>      (Read architecture explainer)")


if __name__ == "__main__":
    main()
