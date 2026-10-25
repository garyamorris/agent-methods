r"""
Pattern 06: Parallel Fan-Out / Fan-In (Scatter-Gather / Map-Reduce)
===================================================================

Architecture Overview:
----------------------
When multiple independent analyses or subtasks must be performed, executing agents
sequentially multiplies latency and slows user response times.
The Parallel Fan-Out / Fan-In pattern achieves maximum concurrency:
  1. Fan-Out (Scatter): The system triggers multiple specialized agents concurrently
     using `asyncio.gather(...)`.
  2. Independent Processing: Each agent evaluates the query against its specific domain
     without blocking or interfering with other agents.
  3. Fan-In (Gather / Reduce): An aggregator agent collects all parallel evaluations
     and synthesizes an integrated decision matrix.

Communication Topology:
-----------------------
                           +-------------------+
                           |    User Request   |
                           +-------------------+
                                     |
              +----------------------+----------------------+
              | (concurrent fan-out) |                      |
              v                      v                      v
     +-----------------+    +-----------------+    +-----------------+
     |  Cybersecurity  |    |   Regulatory    |    |  Financial      |
     |   Risk Agent    |    | Compliance Agent|    |   Risk Agent    |
     +-----------------+    +-----------------+    +-----------------+
              \                      |                      /
               \                     |                     /
                +--------------------+--------------------+
                                     | (fan-in aggregation)
                                     v
                           +-------------------+
                           | Chief Risk Officer|
                           |   (Synthesizer)   |
                           +-------------------+
                                     |
                                     v
                           +-------------------+
                           |  Integrated Risk  |
                           |      Matrix       |
                           +-------------------+

When to Use:
------------
- Multi-perspective evaluations (Risk auditing, code reviews by security + performance + style).
- Map-Reduce workflows processing multiple chunks of documents or datasets.
- Minimizing wall-clock latency for complex queries where subtasks are mutually independent.

OpenAI Agents SDK Primitives:
-----------------------------
- Multiple independent `Agent` instances.
- Asynchronous concurrent dispatch via `asyncio.gather(*[Runner.run(agent, prompt) for agent in agents])`.
- Aggregator `Agent` synthesizing concurrent outputs.
"""

import asyncio
import time
from agents import Agent, Runner
from agent_methods.common import (
    DEFAULT_MODEL,
    ensure_api_key,
    console,
    print_header,
    print_agent_step,
    print_result_panel,
    print_explainer,
)

# -------------------------------------------------------------------------
# Define Specialized Domain Risk Agents
# -------------------------------------------------------------------------

cybersecurity_agent = Agent(
    name="CybersecurityAuditor",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Senior Cybersecurity Auditor. "
        "Analyze the provided initiative for security vulnerabilities, "
        "attack vectors, data privacy risks (PII/PHI), and authentication weaknesses. "
        "Provide 3 bullet points with risk severity ratings (Low/Med/High)."
    ),
)

compliance_agent = Agent(
    name="RegulatoryComplianceAuditor",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Regulatory Compliance Counsel. "
        "Analyze the initiative for compliance with GDPR, HIPAA, AI Act, and consumer protection laws. "
        "Provide 3 bullet points on compliance obligations and legal exposure."
    ),
)

financial_risk_agent = Agent(
    name="FinancialRiskAuditor",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Quantitative Financial Risk Analyst. "
        "Evaluate liquidity risk, default exposure, volatility, and capital reserve requirements. "
        "Provide 3 bullet points on capital safety and loss mitigation."
    ),
)

chief_risk_officer = Agent(
    name="ChiefRiskOfficer",
    model=DEFAULT_MODEL,
    instructions=(
        "You are the Chief Risk Officer. "
        "You receive 3 independent risk reports: Cybersecurity, Regulatory, and Financial. "
        "Synthesize these findings into an Executive Risk Matrix table with overall risk posture, "
        "key vulnerabilities, and mandatory pre-launch mitigation gates."
    ),
)


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(proposal: str | None = None) -> str:
    """Execute parallel fan-out across multiple domain agents, then fan-in aggregation."""
    ensure_api_key()

    default_proposal = (
        "Launching a patient health-fintech mobile app that offers instant, AI-underwritten "
        "micro-loans ($500-$5,000) for elective medical surgeries, connecting directly to "
        "hospital Electronic Health Record (EHR) systems via open APIs."
    )
    user_prompt = proposal or default_proposal

    print_header(
        "Pattern 06: Parallel Fan-Out / Fan-In",
        "High-concurrency scatter-gather pattern minimizing latency across independent agents",
    )

    print_explainer(
        summary="Concurrent execution of multiple specialized agents simultaneously, followed by an aggregator agent combining the results.",
        communication_mechanism="Scatter-Gather via asyncio.gather() followed by synthesis agent consolidation.",
        when_to_use=[
            "Independent sub-analyses (multi-perspective risk audits, parallel search, peer review).",
            "Latency-critical applications where sequential execution would be prohibitively slow.",
            "Map-Reduce architectures processing discrete segments of a problem.",
        ],
    )

    console.print(f"[bold cyan]Proposal to Audit:[/bold cyan] {user_prompt}\n")

    start_time = time.perf_counter()

    # Step 1: Concurrent Fan-Out
    print_agent_step("System", "Fanning out across 3 specialist agents concurrently in parallel...")
    print_agent_step("CybersecurityAuditor", "Auditing attack surface & EHR privacy...", style="cyan")
    print_agent_step("RegulatoryComplianceAuditor", "Auditing HIPAA, GDPR, & Lending laws...", style="cyan")
    print_agent_step("FinancialRiskAuditor", "Auditing default rates & capital adequacy...", style="cyan")

    cyber_future = Runner.run(cybersecurity_agent, user_prompt)
    compliance_future = Runner.run(compliance_agent, user_prompt)
    financial_future = Runner.run(financial_risk_agent, user_prompt)

    # Await all simultaneously
    cyber_res, compliance_res, financial_res = await asyncio.gather(
        cyber_future, compliance_future, financial_future
    )

    elapsed_fanout = time.perf_counter() - start_time
    print_agent_step(
        "System",
        f"All 3 parallel audits completed concurrently in {elapsed_fanout:.2f} seconds!",
        style="bold green",
    )

    # Step 2: Fan-In Aggregation
    print_agent_step("ChiefRiskOfficer", "Fanning in: Synthesizing executive risk matrix...")

    aggregated_brief = (
        f"PROPOSAL:\n{user_prompt}\n\n"
        f"CYBERSECURITY AUDIT:\n{cyber_res.final_output}\n\n"
        f"REGULATORY AUDIT:\n{compliance_res.final_output}\n\n"
        f"FINANCIAL RISK AUDIT:\n{financial_res.final_output}"
    )

    synthesis_res = await Runner.run(chief_risk_officer, aggregated_brief)
    total_elapsed = time.perf_counter() - start_time

    print_agent_step(
        "System",
        f"Full Fan-Out/Fan-In completed in {total_elapsed:.2f}s total wall-clock time.",
        style="bold green",
    )
    print_result_panel("Executive Risk Matrix (from ChiefRiskOfficer)", str(synthesis_res.final_output))
    return str(synthesis_res.final_output)


if __name__ == "__main__":
    asyncio.run(run())
