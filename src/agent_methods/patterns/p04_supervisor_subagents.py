r"""
Pattern 04: Supervisor & Subagents (Orchestrator-Workers)
========================================================

Architecture Overview:
----------------------
In the Orchestrator-Workers pattern, a central Supervisor coordinates specialized Subagents.
Crucially, unlike handoffs where control leaves the current agent, in this pattern
subagents are packaged as callable tools using `subagent.as_tool()`.

The Supervisor retains conversational ownership at all times:
  1. Supervisor decomposes a high-level goal into specialized subtasks.
  2. Supervisor invokes Subagents like tools (`subagent.as_tool()`), providing targeted input.
  3. Each Subagent executes in an isolated context window, preventing context pollution.
  4. Subagent returns its distilled conclusion back to the Supervisor.
  5. Supervisor aggregates the subagent findings into an executive synthesis.

Communication Topology:
-----------------------
                       +-----------------------+
                       |   Executive Strategy  |
                       |       Request         |
                       +-----------------------+
                                   |
                                   v
                       +-----------------------+
                       |      Supervisor       |
                       |   (LeadStrategist)    |
                       +-----------------------+
                         /         |         \
         (as_tool)      /          |          \      (as_tool)
                       v           |           v
             +---------------+     |     +---------------+
             | MarketAnalyst |     |     | FinModeler    |
             |   Subagent    |     |     |   Subagent    |
             +---------------+     v     +---------------+
                    |     +---------------+      |
                    |     | TechArchitect |      |
                    |     |   Subagent    |      |
                    |     +---------------+      |
                    \              |             /
                     \---> [Distilled Return] <--/
                                   |
                                   v
                       +-----------------------+
                       | Consolidated Executive|
                       |       Synthesis       |
                       +-----------------------+

Key Difference: Handoff vs. Agent-as-a-Tool:
--------------------------------------------
- Handoff (`handoff`): Target agent TAKES OVER conversation. Receives full conversation history.
- Agent-as-Tool (`as_tool`): Originating agent RETAINS conversation. Target receives only generated
  tool parameters, executes in isolated sub-context, and returns a concise result string.

When to Use:
------------
- Complex projects requiring deep domain specialization (e.g. strategic planning, code generation + review).
- Context hygiene: preventing verbose research outputs from polluting the main conversation history.
- Hierarchical workflows requiring a single coordinator accountable for final output quality.

OpenAI Agents SDK Primitives:
-----------------------------
- `subagent.as_tool(tool_name=..., tool_description=...)`: Converts an `Agent` into a `FunctionTool`.
- `Runner.run(supervisor, input)`: Seamlessly runs the supervisor, which automatically spins up subagent runs!
"""

import asyncio
import json
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
# Subagent Specific Tools
# -------------------------------------------------------------------------

@function_tool
def query_market_trends(industry: str) -> str:
    """Analyze sector market growth, competitor pricing, and CAGR."""
    return json.dumps({
        "industry": industry,
        "market_size_usd": "$24.5 Billion",
        "projected_cagr": "32.4% over 5 years",
        "top_competitor_moves": "Incumbents shifting from per-seat pricing to usage/token-based monetization.",
        "key_risk": "Low barrier to entry for shallow wrapper tools.",
    })


@function_tool
def benchmark_infrastructure(architecture_style: str) -> str:
    """Benchmark latency and monthly cloud compute requirements."""
    return json.dumps({
        "style": architecture_style,
        "p99_latency_ms": 185,
        "estimated_monthly_infra_cost_usd": 4800,
        "bottleneck": "Model provider rate limits and embedding retrieval latency during peak hours.",
        "recommendation": "Use semantic caching and streaming responses to mask latency.",
    })


@function_tool
def model_unit_economics(cac_usd: float, ltv_usd: float, payback_months: int) -> str:
    """Calculate venture metrics (LTV:CAC ratio, payback velocity)."""
    ratio = round(ltv_usd / cac_usd, 2) if cac_usd > 0 else 0.0
    health = "Excellent (>3x)" if ratio >= 3.0 else "Caution (<3x)"
    return json.dumps({
        "cac": cac_usd,
        "ltv": ltv_usd,
        "ltv_to_cac_ratio": ratio,
        "payback_months": payback_months,
        "unit_economics_rating": health,
    })


# -------------------------------------------------------------------------
# Define Specialized Subagents
# -------------------------------------------------------------------------

market_analyst = Agent(
    name="MarketAnalyst",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Market Intelligence Analyst. "
        "Use `query_market_trends` to analyze competitor dynamics, market sizing, and industry growth. "
        "Return a crisp, 2-paragraph executive briefing highlighting market opportunities and risks."
    ),
    tools=[query_market_trends],
)

tech_architect = Agent(
    name="TechArchitect",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Principal Cloud Solutions Architect. "
        "Use `benchmark_infrastructure` to evaluate architecture latency, cloud costs, and bottlenecks. "
        "Return a technical assessment with concrete mitigation recommendations."
    ),
    tools=[benchmark_infrastructure],
)

financial_modeler = Agent(
    name="FinancialModeler",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Venture CFO and financial modeler. "
        "Use `model_unit_economics` to assess commercial viability, CAC payback, and margins. "
        "Return a financial viability verdict."
    ),
    tools=[model_unit_economics],
)

# -------------------------------------------------------------------------
# Convert Subagents to Tools for the Supervisor
# -------------------------------------------------------------------------

market_tool = market_analyst.as_tool(
    tool_name="consult_market_analyst",
    tool_description="Delegates market research, competitor analysis, and industry trends to the Market Analyst subagent.",
)

tech_tool = tech_architect.as_tool(
    tool_name="consult_tech_architect",
    tool_description="Delegates technical feasibility, cloud infrastructure benchmarking, and latency analysis to the Tech Architect subagent.",
)

finance_tool = financial_modeler.as_tool(
    tool_name="consult_financial_modeler",
    tool_description="Delegates LTV:CAC, unit economics, and payback velocity analysis to the Financial Modeler subagent.",
)

# -------------------------------------------------------------------------
# Define Supervisor Agent
# -------------------------------------------------------------------------

lead_strategist = Agent(
    name="LeadStrategist",
    model=DEFAULT_MODEL,
    instructions=(
        "You are the Chief Strategy Officer orchestrating an executive decision team. "
        "When given a strategic initiative:\n"
        "1. Consult your specialist subagent tools: consult_market_analyst, consult_tech_architect, "
        "and consult_financial_modeler.\n"
        "2. Do NOT hallucinate the analysis yourself; gather findings from all three specialists.\n"
        "3. Synthesize their insights into an integrated Executive Strategy Dossier with a definitive "
        "Go/No-Go recommendation."
    ),
    tools=[market_tool, tech_tool, finance_tool],
)


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(query: str | None = None) -> str:
    """Execute supervisor orchestrating subagents via agent.as_tool()."""
    ensure_api_key()

    default_query = (
        "We are evaluating launching an enterprise AI Agent Workflow Orchestrator. "
        "Target CAC is $2,500, expected LTV is $12,000 with a 6-month payback. "
        "Conduct a full review across market trends, technical infrastructure feasibility, "
        "and unit economics, and deliver an Executive Go/No-Go Decision Dossier."
    )
    user_prompt = query or default_query

    print_header(
        "Pattern 04: Supervisor & Sub-Agents",
        "Hierarchical Orchestrator-Workers using `agent.as_tool()` isolation",
    )

    print_explainer(
        summary="A central supervisor coordinates specialized sub-agents converted into tools. The supervisor retains conversational context.",
        communication_mechanism="Call-and-return semantics (`subagent.as_tool()`). Subagents run in isolated sub-turns and return distilled summaries.",
        when_to_use=[
            "Complex multidisciplinary goals requiring coordinated specialist perspectives.",
            "Protecting the main conversation context from verbose sub-agent tool chatter (context hygiene).",
            "Single accountable decision-maker synthesizing inputs from multiple delegates.",
        ],
    )

    console.print(f"[bold cyan]User Query:[/bold cyan] {user_prompt}\n")

    print_agent_step("LeadStrategist", "Decomposing task and invoking specialist subagents...")
    result = await Runner.run(lead_strategist, user_prompt)

    # Trace subagent tool calls
    for item in result.new_items:
        item_type = getattr(item, "type", type(item).__name__)
        if item_type == "tool_call_item":
            raw = getattr(item, "raw_item", None)
            name = getattr(raw, "name", "tool")
            args = getattr(raw, "arguments", "{}")
            try:
                parsed_args = json.loads(args) if isinstance(args, str) else args
            except Exception:
                parsed_args = {"raw": args}
            print_tool_call(name, parsed_args)

    print_result_panel("Executive Strategy Dossier (from LeadStrategist)", str(result.final_output))
    return str(result.final_output)


if __name__ == "__main__":
    asyncio.run(run())
