"""Interactive CLI explorer and runner for multi-agent architectures."""

import asyncio
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from agent_methods.patterns import PATTERNS
from agent_methods.common import console, print_header, DEFAULT_MODEL, is_using_deepseek

def display_patterns_table() -> None:
    """Render a formatted comparison table of all available agent architectures."""
    provider_label = "DeepSeek" if is_using_deepseek() else "OpenAI"
    table = Table(
        title=f"Multi-Agent Communication Architectures Bed [{provider_label}: {DEFAULT_MODEL}]",
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


async def run_pattern(pattern_key: str, custom_input: str | None = None, example_id: int = 1) -> None:
    """Execute a selected pattern by number or ID, choosing a real-world scenario."""
    p_info = PATTERNS.get(pattern_key)
    if not p_info:
        # Search by id
        for k, v in PATTERNS.items():
            if v["id"] == pattern_key:
                p_info = v
                break

    if not p_info:
        console.print(f"[bold red]Error:[/bold red] Unknown pattern '{pattern_key}'.")
        console.print("Valid choices are 1 through 15.")
        return

    mod = p_info["module"]
    try:
        # Pass example_id if the module run() accepts it
        import inspect
        sig = inspect.signature(mod.run)
        kwargs = {}
        if custom_input:
            kwargs["query"] = custom_input
        if "example_id" in sig.parameters:
            kwargs["example_id"] = example_id
        await mod.run(**kwargs)
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
        provider_name = "DeepSeek (deepseek-chat)" if is_using_deepseek() else "OpenAI"
        print_header(
            "Agent Methods Lab",
            f"Educational testbed of agent architectures & communication topologies\nPowered by {provider_name} via OpenAI Agents SDK",
        )
        display_patterns_table()

        choice = Prompt.ask(
            "[bold green]Select pattern (1-15), 't <id>' to trace comms, 'e <id>' to explain, 'v' for visualizer, or 'q' to quit[/bold green]",
            default="2",
        )

        if choice.lower() in ("q", "quit", "exit"):
            console.print("[dim]Goodbye![/dim]")
            return

        if choice.lower() in ("v", "visualizer", "web"):
            from agent_methods.web_server import serve_visualizer
            serve_visualizer()
            return

        if choice.lower().startswith("e "):
            target_key = choice.split()[1]
            print_pattern_explanation(target_key)
            return

        if choice.lower().startswith("t "):
            target_key = choice.split()[1]
            ex_choice = Prompt.ask(
                "[bold yellow]Select real-world scenario to trace[/bold yellow] (1=Primary production case, 2=Secondary case)",
                choices=["1", "2"],
                default="1",
            )
            console.print("\n[bold yellow]📡 Initiating Real-Time Inter-Agent Wire Communication Trace...[/bold yellow]\n")
            asyncio.run(run_pattern(target_key, example_id=int(ex_choice)))
            return

        ex_choice = Prompt.ask(
            "[bold yellow]Select real-world scenario[/bold yellow] (1=Primary production case, 2=Secondary case)",
            choices=["1", "2"],
            default="1",
        )

        asyncio.run(run_pattern(choice, example_id=int(ex_choice)))
        return

    cmd = args[0].lower()
    if cmd in ("list", "ls"):
        display_patterns_table()
    elif cmd in ("benchmark", "bench"):
        from agent_methods.benchmark import run_benchmark_suite
        targets = args[1:] if len(args) > 1 else None
        asyncio.run(run_benchmark_suite(targets))
    elif cmd in ("visualizer", "web", "ui"):
        from agent_methods.web_server import serve_visualizer
        port = int(args[1]) if len(args) > 1 and args[1].isdigit() else 8000
        serve_visualizer(port=port)
    elif cmd in ("explain", "info") and len(args) > 1:
        print_pattern_explanation(args[1])
    elif cmd in ("trace", "comms") and len(args) > 1:
        pattern_arg = args[1]
        example_id = 1
        query_parts = []
        skip_next = False
        for i, a in enumerate(args[2:]):
            if skip_next:
                skip_next = False
                continue
            if a in ("--example", "-e") and i + 1 < len(args[2:]):
                example_id = int(args[2:][i + 1])
                skip_next = True
            else:
                query_parts.append(a)
        user_input = " ".join(query_parts) if query_parts else None
        console.print("\n[bold yellow]📡 Initiating Real-Time Inter-Agent Wire Communication Trace...[/bold yellow]\n")
        asyncio.run(run_pattern(pattern_arg, user_input, example_id=example_id))
    elif cmd in ("run",) and len(args) > 1:
        pattern_arg = args[1]
        example_id = 1
        query_parts = []
        skip_next = False
        for i, a in enumerate(args[2:]):
            if skip_next:
                skip_next = False
                continue
            if a in ("--example", "-e") and i + 1 < len(args[2:]):
                example_id = int(args[2:][i + 1])
                skip_next = True
            else:
                query_parts.append(a)
        user_input = " ".join(query_parts) if query_parts else None
        asyncio.run(run_pattern(pattern_arg, user_input, example_id=example_id))
    elif cmd in PATTERNS:
        example_id = 1
        query_parts = []
        skip_next = False
        for i, a in enumerate(args[1:]):
            if skip_next:
                skip_next = False
                continue
            if a in ("--example", "-e") and i + 1 < len(args[1:]):
                example_id = int(args[1:][i + 1])
                skip_next = True
            else:
                query_parts.append(a)
        user_input = " ".join(query_parts) if query_parts else None
        asyncio.run(run_pattern(cmd, user_input, example_id=example_id))
    else:
        console.print("[bold red]Usage:[/bold red]")
        console.print("  python main.py                              (Interactive Menu with Scenario Selection)")
        console.print("  python main.py list                         (List all 15 patterns)")
        console.print("  python main.py trace <1-15> [--example 1|2] (Trace real-time inter-agent wire comms & sequence)")
        console.print("  python main.py run <1-15> [--example 1|2]   (Run a specific pattern & real-world example)")
        console.print("  python main.py explain <1-15>               (Read architecture & real API docstring)")
        console.print("  python main.py visualizer                   (Launch interactive browser visualizer)")
        console.print("  python main.py benchmark                    (Run comparative latency & stability benchmark)")


if __name__ == "__main__":
    main()
