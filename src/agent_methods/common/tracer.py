"""Live Inter-Agent Communication Tracer and Wire Protocol Visualizer.

Captures real-time communication events across multi-agent handoffs, tool calls,
observations, and conversational turns using OpenAI Agents SDK RunHooks.
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any, Literal
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from agents import RunHooks

console = Console()

PacketType = Literal["QUERY", "AGENT_START", "HANDOFF", "TOOL_CALL", "TOOL_RESULT", "AGENT_END", "FINAL_OUTPUT"]

@dataclass
class CommsPacket:
    seq: int
    timestamp_offset: float
    source: str
    target: str
    packet_type: PacketType
    summary: str
    payload: Any = None


class CommsTracer(RunHooks):
    """Real-time observability hook capturing inter-agent wire communications."""

    def __init__(self, scenario_title: str = "", display_live: bool = True):
        super().__init__()
        self.scenario_title = scenario_title
        self.display_live = display_live
        self.start_time = time.perf_counter()
        self.packets: list[CommsPacket] = []
        self._seq = 1
        self._active_agent = "User"
        self._pending_tool_calls: dict[str, float] = {}

    def _now(self) -> float:
        return round(time.perf_counter() - self.start_time, 3)

    def record_user_query(self, query: str, target_agent: str) -> None:
        """Record the initial incoming user prompt packet."""
        pkt = CommsPacket(
            seq=self._seq,
            timestamp_offset=self._now(),
            source="User",
            target=target_agent,
            packet_type="QUERY",
            summary="Initial User Query Ingestion",
            payload=query,
        )
        self.packets.append(pkt)
        self._seq += 1
        if self.display_live:
            self._print_packet(pkt)

    async def on_agent_start(self, context, agent) -> None:
        self._active_agent = getattr(agent, "name", str(agent))
        pkt = CommsPacket(
            seq=self._seq,
            timestamp_offset=self._now(),
            source="System / Orchestrator",
            target=self._active_agent,
            packet_type="AGENT_START",
            summary=f"Context Turn Transferred to [{self._active_agent}]",
            payload={"model": getattr(agent, "model", "deepseek-chat"), "tools_count": len(getattr(agent, "tools", []))},
        )
        self.packets.append(pkt)
        self._seq += 1
        if self.display_live:
            self._print_packet(pkt)

    async def on_handoff(self, context, from_agent, to_agent) -> None:
        from_name = getattr(from_agent, "name", str(from_agent))
        to_name = getattr(to_agent, "name", str(to_agent))
        pkt = CommsPacket(
            seq=self._seq,
            timestamp_offset=self._now(),
            source=from_name,
            target=to_name,
            packet_type="HANDOFF",
            summary=f"SDK Handoff: [{from_name}] transfers conversation context to [{to_name}]",
            payload={"from": from_name, "to": to_name, "mechanism": "Native OpenAI Agents SDK handoff()"},
        )
        self.packets.append(pkt)
        self._seq += 1
        if self.display_live:
            self._print_packet(pkt)

    async def on_tool_start(self, context, agent, tool) -> None:
        agent_name = getattr(agent, "name", str(agent))
        tool_name = getattr(tool, "name", str(tool))
        self._pending_tool_calls[tool_name] = time.perf_counter()

        pkt = CommsPacket(
            seq=self._seq,
            timestamp_offset=self._now(),
            source=agent_name,
            target=f"Tool:{tool_name}",
            packet_type="TOOL_CALL",
            summary=f"Agent invokes real API tool [{tool_name}]",
            payload={"tool": tool_name},
        )
        self.packets.append(pkt)
        self._seq += 1
        if self.display_live:
            self._print_packet(pkt)

    async def on_tool_end(self, context, agent, tool, result) -> None:
        agent_name = getattr(agent, "name", str(agent))
        tool_name = getattr(tool, "name", str(tool))
        start_ts = self._pending_tool_calls.pop(tool_name, None)
        duration_ms = round((time.perf_counter() - start_ts) * 1000, 1) if start_ts else None

        result_str = str(result)
        pkt = CommsPacket(
            seq=self._seq,
            timestamp_offset=self._now(),
            source=f"Tool:{tool_name}",
            target=agent_name,
            packet_type="TOOL_RESULT",
            summary=f"Observation returned from [{tool_name}] ({duration_ms}ms)",
            payload={"duration_ms": duration_ms, "result_preview": result_str[:250] + ("..." if len(result_str) > 250 else "")},
        )
        self.packets.append(pkt)
        self._seq += 1
        if self.display_live:
            self._print_packet(pkt)

    async def on_agent_end(self, context, agent, output) -> None:
        agent_name = getattr(agent, "name", str(agent))
        out_str = str(output)
        pkt = CommsPacket(
            seq=self._seq,
            timestamp_offset=self._now(),
            source=agent_name,
            target="Conversation Floor",
            packet_type="AGENT_END",
            summary=f"[{agent_name}] completed turn synthesis",
            payload={"output_preview": out_str[:200] + ("..." if len(out_str) > 200 else "")},
        )
        self.packets.append(pkt)
        self._seq += 1
        if self.display_live:
            self._print_packet(pkt)

    def _print_packet(self, pkt: CommsPacket) -> None:
        """Render a single packet in the live wire feed."""
        styles = {
            "QUERY": ("bold cyan", "blue", "📥 [QUERY INGESTION]"),
            "AGENT_START": ("bold cyan", "cyan", "🟢 [AGENT ACTIVATION]"),
            "HANDOFF": ("bold yellow", "yellow", "⇄ [PEER / ROUTER HANDOFF]"),
            "TOOL_CALL": ("bold magenta", "magenta", "⚡ [REAL API REQUEST]"),
            "TOOL_RESULT": ("bold green", "green", "✓ [REAL API OBSERVATION]"),
            "AGENT_END": ("bold white", "white", "💬 [AGENT SYNTHESIS]"),
            "FINAL_OUTPUT": ("bold green", "green", "🏁 [FINAL DELIVERY]"),
        }
        title_style, border_style, label = styles.get(pkt.packet_type, ("white", "white", pkt.packet_type))

        header = f"[{title_style}]#{pkt.seq:02d} [{pkt.timestamp_offset:05.2f}s][/{title_style}] {label}: [bold white]{pkt.source}[/bold white] ➔ [bold white]{pkt.target}[/bold white]"

        body_lines = [f"[dim]{pkt.summary}[/dim]"]
        if pkt.payload:
            if isinstance(pkt.payload, dict):
                for k, v in pkt.payload.items():
                    body_lines.append(f"  [cyan]{k}:[/cyan] [white]{v}[/white]")
            elif isinstance(pkt.payload, str):
                body_lines.append(f"  [white]{pkt.payload}[/white]")

        console.print(Panel("\n".join(body_lines), title=header, border_style=border_style, padding=(0, 1)))

    def render_summary_ledger(self) -> None:
        """Print a summary table of all communication transactions."""
        table = Table(
            title="📡 Inter-Agent Communication Ledger",
            show_header=True,
            header_style="bold magenta",
            expand=True,
        )
        table.add_column("Seq", style="bold cyan", width=5, justify="center")
        table.add_column("Time", style="dim", width=8, justify="right")
        table.add_column("Source", style="bold yellow", width=22)
        table.add_column("Target", style="bold green", width=22)
        table.add_column("Packet Type", style="bold white", width=16)
        table.add_column("Event Summary", style="dim")

        for p in self.packets:
            table.add_row(
                f"{p.seq:02d}",
                f"+{p.timestamp_offset:.2f}s",
                p.source,
                p.target,
                p.packet_type,
                p.summary,
            )

        console.print()
        console.print(table)
        console.print()

    def render_sequence_diagram(self) -> None:
        """Render an ASCII/Unicode sequence diagram depicting communication hops."""
        # Collect unique participants preserving order
        participants = ["User"]
        for p in self.packets:
            for entity in [p.source, p.target]:
                # clean up Tool: prefix for diagram headers
                name = entity.replace("Tool:", "")
                if name not in participants and name != "System / Orchestrator" and name != "Conversation Floor":
                    participants.append(name)

        if len(participants) < 2:
            return

        console.rule("[bold cyan]Inter-Agent Message Sequence Diagram[/bold cyan]")
        console.print()

        col_width = 18
        # Header row
        header = "  ".join(f"[{p[:col_width-2]:^{col_width-2}}]" for p in participants)
        divider = "  ".join("-" * (col_width-2) for _ in participants)
        console.print(f"[bold magenta]{header}[/bold magenta]")
        console.print(f"[dim]{divider}[/dim]")

        # Draw transactions
        for p in self.packets:
            src = p.source.replace("Tool:", "")
            tgt = p.target.replace("Tool:", "")
            if src not in participants or tgt not in participants or src == tgt:
                continue

            src_idx = participants.index(src)
            tgt_idx = participants.index(tgt)

            # Build line
            line_chars = [" "] * (len(participants) * col_width)
            for i in range(len(participants)):
                line_chars[i * col_width + (col_width // 2) - 1] = "│"

            # Connect arrow
            left_col = min(src_idx, tgt_idx)
            right_col = max(src_idx, tgt_idx)
            start_pos = left_col * col_width + (col_width // 2)
            end_pos = right_col * col_width + (col_width // 2) - 2

            for pos in range(start_pos, end_pos + 1):
                line_chars[pos] = "─"

            if src_idx < tgt_idx:
                line_chars[end_pos] = "▶"
            else:
                line_chars[start_pos] = "◀"

            line_str = "".join(line_chars)
            label = f"({p.seq}) {p.packet_type}"
            console.print(f"{line_str}  [dim cyan]{label}[/dim cyan]")

        console.print(f"[dim]{divider}[/dim]")
        console.print()
