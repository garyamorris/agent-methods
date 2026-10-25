"""Performance and communication topology benchmarking harness."""

import asyncio
import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from agent_methods.patterns import PATTERNS
from agent_methods.common import ensure_api_key, DEFAULT_MODEL, is_using_deepseek

console = Console()

async def benchmark_pattern(pattern_id: str, prompt: str | None = None) -> dict:
    """Benchmark an individual agent pattern, capturing latency, turns, and status."""
    p_info = PATTERNS[pattern_id]
    mod = p_info["module"]

    start = time.perf_counter()
    try:
        if prompt:
            output = await mod.run(prompt)
        else:
            output = await mod.run()
        elapsed = time.perf_counter() - start
        return {
            "id": pattern_id,
            "name": p_info["name"],
            "topology": p_info["topology"],
            "latency": elapsed,
            "status": "PASS",
            "output_chars": len(str(output)),
            "error": None,
        }
    except Exception as e:
        elapsed = time.perf_counter() - start
        return {
            "id": pattern_id,
            "name": p_info["name"],
            "topology": p_info["topology"],
            "latency": elapsed,
            "status": "FAIL",
            "output_chars": 0,
            "error": str(e),
        }


async def run_benchmark_suite(pattern_ids: list[str] | None = None) -> None:
    """Run comparative benchmark across agent topologies and output performance matrix."""
    ensure_api_key()

    provider = "DeepSeek (deepseek-chat)" if is_using_deepseek() else "OpenAI"
    console.print()
    console.print(Panel(
        f"[bold cyan]Agent Communication Topology Benchmark Suite[/bold cyan]\n"
        f"[dim]Provider: {provider} | Measuring Wall-Clock Latency & Execution Stability[/dim]",
        border_style="cyan",
    ))

    # Benchmark a core representative subset if none specified (to manage API rate limits & runtime)
    targets = pattern_ids or ["1", "2", "4", "6", "10", "14"]

    results = []
    for pid in targets:
        p_name = PATTERNS[pid]["name"]
        console.print(f"  ● Benchmarking Pattern {pid}: [bold]{p_name}[/bold]...")
        res = await benchmark_pattern(pid)
        results.append(res)
        status_color = "green" if res["status"] == "PASS" else "red"
        console.print(f"    ↳ Finished in [bold cyan]{res['latency']:.2f}s[/bold cyan] [{status_color}]{res['status']}[/{status_color}]")

    # Render results table
    table = Table(
        title=f"Topology Performance Benchmark Matrix [{provider}]",
        show_header=True,
        header_style="bold magenta",
        expand=True,
    )
    table.add_column("#", style="cyan", width=4, justify="center")
    table.add_column("Architecture Pattern", style="bold white", width=28)
    table.add_column("Topology Style", style="yellow", width=24)
    table.add_column("Wall Latency", style="bold cyan", justify="right", width=14)
    table.add_column("Output Size", style="dim", justify="right", width=14)
    table.add_column("Status", justify="center", width=10)

    for r in results:
        status_badge = f"[bold green]PASS[/bold green]" if r["status"] == "PASS" else f"[bold red]FAIL[/bold red]"
        table.add_row(
            r["id"],
            r["name"],
            r["topology"],
            f"{r['latency']:.2f}s",
            f"{r['output_chars']} chars",
            status_badge,
        )

    console.print()
    console.print(table)
    console.print()


if __name__ == "__main__":
    asyncio.run(run_benchmark_suite())
