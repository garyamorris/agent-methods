r"""
Pattern 10: Event-Driven Shared Blackboard (Decoupled Shared State)
==================================================================

Architecture Overview:
----------------------
In direct-call architectures (e.g. Supervisor-Subagents or Peer Handoffs), agents must have
explicit dependencies on each other. When system complexity grows, point-to-point connections
balloon into an unmaintainable web of dependencies ($O(N^2)$).

The Blackboard Pattern solves this by decoupling agents completely:
  1. Central Blackboard: A shared, thread-safe memory repository containing the current state,
     verified facts, proposed hypotheses, and open incident tickets.
  2. Autonomous Specialists: Agents do NOT call each other. Instead, each agent monitors the
     blackboard for state changes matching its domain of expertise.
  3. Knowledge Contribution: When an agent solves a sub-problem, it writes new facts back to
     the blackboard, which in turn triggers downstream specialists.
  4. Convergence: The loop continues until a resolution state is reached on the blackboard.

Communication Topology:
-----------------------
                    +------------------------------------+
                    |        Telemetry Anomaly           |
                    +------------------------------------+
                                      |
                                      v
     +------------------------------------------------------------------+
     |                    CENTRAL SHARED BLACKBOARD                     |
     |  - State: INVESTIGATING -> MITIGATING -> RESOLVED                |
     |  - Telemetry: {latency_p99: 4200ms, db_pool: 98% saturation}     |
     |  - Hypotheses: ["Distributed Slowloris attack from ASN 4921"]    |
     |  - Verified Facts: ["Identified 840 compromised worker IPs"]     |
     |  - Mitigation Actions: ["Applied WAF Rate Limit rule #902"]      |
     +------------------------------------------------------------------+
             ^                     ^                     ^
             | (reads/writes)      | (reads/writes)      | (reads/writes)
             v                     v                     v
    +-----------------+   +-----------------+   +-----------------+
    | TelemetryAgent  |   |  ThreatHunter   |   | RemediationEng  |
    | (Anomaly Det.)  |   | (Root Cause)    |   | (WAF & Recovery)|
    +-----------------+   +-----------------+   +-----------------+

When to Use:
------------
- Incident response, autonomous cyber-defense, fraud investigation, multi-sensor intelligence.
- Loosely coupled multi-agent systems where agents shouldn't need hardcoded knowledge of peers.
- Complex, evolving problems where the sequence of steps cannot be predetermined upfront.

OpenAI Agents SDK Primitives:
-----------------------------
- Dedicated `Agent` instances acting as knowledge sources.
- Shared Pydantic / dataclass state models manipulated across agent cycles.
- Reactive coordination loop executing agents based on blackboard triggers.
"""

import asyncio
import json
from datetime import datetime
from pydantic import BaseModel, Field
from agents import Agent, Runner, function_tool
from agent_methods.common import (
    DEFAULT_MODEL,
    ensure_api_key,
    console,
    print_header,
    print_agent_step,
    print_tool_call,
    print_result_panel,
    print_explainer,
)

# -------------------------------------------------------------------------
# Shared Blackboard State Model
# -------------------------------------------------------------------------

class Blackboard(BaseModel):
    incident_id: str
    status: str = "INVESTIGATING"  # INVESTIGATING, MITIGATING, RESOLVED
    timeline: list[str] = Field(default_factory=list)
    telemetry_findings: list[str] = Field(default_factory=list)
    threat_hypotheses: list[str] = Field(default_factory=list)
    verified_facts: list[str] = Field(default_factory=list)
    applied_mitigations: list[str] = Field(default_factory=list)

    def log_event(self, source: str, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] [{source}] {message}"
        self.timeline.append(entry)


# -------------------------------------------------------------------------
# Specialist Domain Tools
# -------------------------------------------------------------------------

@function_tool
def query_traffic_logs(ip_subnet: str) -> str:
    """Analyze ingress traffic patterns, TLS handshakes, and query frequency."""
    return json.dumps({
        "subnet": ip_subnet,
        "sample_size_packets": 240000,
        "signature": "Slowloris incomplete HTTP header attack",
        "origin_asns": ["ASN-4192", "ASN-8821"],
        "compromised_nodes_count": 680,
    })


@function_tool
def apply_waf_firewall_rule(rule_name: str, target_asn: str, action: str) -> str:
    """Deploy emergency edge filter rule to Cloudflare/AWS WAF."""
    return json.dumps({
        "status": "APPLIED",
        "rule_id": "waf_rule_emer_9921",
        "name": rule_name,
        "target": target_asn,
        "action": action,
        "propagation_seconds": 1.2,
    })


# -------------------------------------------------------------------------
# Define Blackboard Specialist Agents
# -------------------------------------------------------------------------

telemetry_analyst = Agent(
    name="TelemetryAnalyst",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an SRE Telemetry Analyst. "
        "Review the initial incident alert and telemetry. "
        "Summarize the exact anomaly metrics (latency, saturation, error spikes) and write your findings."
    ),
)

threat_hunter = Agent(
    name="ThreatHunter",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Cybersecurity Threat Hunter. "
        "Inspect the telemetry findings on the blackboard. Use `query_traffic_logs` to analyze "
        "traffic patterns, determine the attack vector and attacker ASN, and post verified facts."
    ),
    tools=[query_traffic_logs],
)

remediation_engineer = Agent(
    name="RemediationEngineer",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an Edge Infrastructure Remediation Engineer. "
        "Read the verified attack facts on the blackboard. "
        "Use `apply_waf_firewall_rule` to neutralize the attack vector, restore service health, "
        "and conclude with an incident resolution report."
    ),
    tools=[apply_waf_firewall_rule],
)


# -------------------------------------------------------------------------
# Runner: Blackboard Reactive Coordination Loop
# -------------------------------------------------------------------------

async def run(incident_alert: str | None = None) -> str:
    """Execute decoupled event-driven blackboard coordination loop."""
    ensure_api_key()

    default_alert = (
        "CRITICAL ALERT: API Gateway p99 latency spiked from 45ms to 4,800ms. "
        "PostgreSQL connection pool reached 99.4% capacity with thousands of half-open socket connections."
    )
    alert = incident_alert or default_alert

    board = Blackboard(incident_id="INC-2026-8812")
    board.log_event("Monitoring", f"Triggered: {alert}")

    print_header(
        "Pattern 10: Event-Driven Shared Blackboard",
        "Decoupled multi-agent coordination via central shared state repository",
    )

    print_explainer(
        summary="Agents do not call each other; they read and update a shared Blackboard state that coordinates workflow stages.",
        communication_mechanism="Shared memory blackboard pub-sub pattern: agents subscribe to state transitions and post verified facts.",
        when_to_use=[
            "Complex incident response, security operations centers (SOC), fraud detection.",
            "Decoupling large teams of specialized agents from tight peer-to-peer coupling.",
            "Dynamic problems where the next appropriate action depends on opportunistic discovery of facts.",
        ],
    )

    console.print(f"[bold cyan]Incident Trigger:[/bold cyan] {alert}\n")

    # Cycle 1: Telemetry Analyst inspects alert & updates blackboard
    print_agent_step("Blackboard", "State = INVESTIGATING. Activating TelemetryAnalyst...")
    res_telem = await Runner.run(telemetry_analyst, f"ALERT:\n{alert}")
    board.telemetry_findings.append(str(res_telem.final_output))
    board.log_event("TelemetryAnalyst", "Analyzed metrics and posted telemetry findings to blackboard.")

    # Cycle 2: Threat Hunter reacts to telemetry findings
    print_agent_step("Blackboard", "New telemetry posted. Activating ThreatHunter...")
    threat_prompt = (
        f"INCIDENT: {board.incident_id}\n\n"
        f"TELEMETRY FINDINGS ON BLACKBOARD:\n"
        f"{board.telemetry_findings[-1]}\n\n"
        f"Investigate root cause using query_traffic_logs on subnet '198.51.100.0/24'."
    )
    res_threat = await Runner.run(threat_hunter, threat_prompt)
    board.verified_facts.append(str(res_threat.final_output))
    board.status = "MITIGATING"
    board.log_event("ThreatHunter", "Identified attack vector and origin ASN; updated blackboard status to MITIGATING.")

    # Cycle 3: Remediation Engineer reacts to verified threat
    print_agent_step("Blackboard", "State = MITIGATING. Activating RemediationEngineer...")
    remedy_prompt = (
        f"INCIDENT: {board.incident_id}\n\n"
        f"VERIFIED FACTS ON BLACKBOARD:\n"
        f"{board.verified_facts[-1]}\n\n"
        f"Deploy WAF mitigation rule to drop traffic from hostile origin ASNs."
    )
    res_remedy = await Runner.run(remediation_engineer, remedy_prompt)
    board.applied_mitigations.append(str(res_remedy.final_output))
    board.status = "RESOLVED"
    board.log_event("RemediationEngineer", "Applied WAF rules and confirmed recovery; status set to RESOLVED.")

    # Format Incident Dossier
    dossier = (
        f"### Incident Post-Mortem Report: {board.incident_id}\n"
        f"- **Final Blackboard Status:** [bold green]{board.status}[/bold green]\n"
        f"- **Total Lifecycle Steps:** {len(board.timeline)}\n\n"
        f"#### Blackboard Event Timeline:\n"
        + "\n".join(f"- `{event}`" for event in board.timeline)
        + f"\n\n#### Remediation Summary:\n{board.applied_mitigations[-1]}"
    )

    print_result_panel("Shared Blackboard Incident Dossier", dossier)
    return dossier


if __name__ == "__main__":
    asyncio.run(run())
