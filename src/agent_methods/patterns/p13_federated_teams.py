r"""
Pattern 13: Federated Multi-Team Swarm (Hierarchical Swarm of Swarms)
=====================================================================

Architecture Overview:
----------------------
As multi-agent systems expand to dozens of specialized agents, flat peer meshes degrade
into chaotic handoff loops, while flat supervisor hierarchies suffer from bottlenecking.
The Federated Multi-Team Swarm organizes agents according to Conway's Law:
  1. Executive Steering Council: High-level strategic coordinator.
  2. Autonomous Functional Clusters (Teams):
     - Engineering Cluster: Lead Architect + Backend Specialist + Cloud SRE.
     - Growth & Marketing Cluster: CMO + Growth Analyst + Content Strategist.
  3. Internal vs External Communication:
     - Inside a cluster, peer agents collaborate closely using specialized tools.
     - Across clusters, only Team Leads communicate, presenting distilled department briefings.

Communication Topology:
-----------------------
                       +-----------------------+
                       |   Executive Council   |
                       |      (CEO Agent)      |
                       +-----------------------+
                               /       \
                              /         \
         (delegates project) /           \ (delegates campaign)
                            v             v
                +---------------+     +---------------+
                |  Engineering  |     |   Marketing   |
                |   Team Lead   |     |   Team Lead   |
                +---------------+     +---------------+
                    |       |             |       |
           (peers)  |       |    (peers)  |       |
                    v       v             v       v
               +---------+ +---------+  +---------+ +---------+
               | Backend | | CloudSRE|  | Growth  | | Content |
               | Engineer| | Special |  | Analyst | | Writer  |
               +---------+ +---------+  +---------+ +---------+
                    \       /             \       /
                     v     v               v     v
                [Eng Deliverable]     [Marketing Deliverable]
                       \                     /
                        +--------->v<-------+
                                   |
                       +-----------------------+
                       |  Unified Enterprise   |
                       |     Launch Dossier    |
                       +-----------------------+

When to Use:
------------
- Enterprise-scale autonomous organizations (e.g. launching end-to-end software + marketing).
- Containing communication complexity inside modular department boundaries.
- Preventing specialized technical jargon from confusing commercial/marketing agents.

OpenAI Agents SDK Primitives:
-----------------------------
- Nested `Agent` instances grouped into functional teams.
- Department leads exposed as tools (`lead.as_tool(...)`) to the Executive Steering Council.
- Cluster-internal collaboration via specialized domain tool execution.
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
# Cluster 1: Engineering Tools & Agents
# -------------------------------------------------------------------------

@function_tool
def design_api_contracts(service_name: str) -> str:
    """Draft OpenAPI 3.1 specification and gRPC proto interfaces."""
    return json.dumps({
        "service": service_name,
        "endpoints": ["POST /v1/checkout", "GET /v1/status", "POST /v1/webhooks"],
        "auth": "OAuth 2.0 Mutual TLS (mTLS)",
        "p99_budget_ms": 120,
    })


@function_tool
def plan_cloud_topology(region: str) -> str:
    """Define multi-region Kubernetes cluster and egress NAT gateways."""
    return json.dumps({
        "primary_region": region,
        "nodes": "EKS Auto-scaling Group (m6i.xlarge)",
        "database": "Aurora PostgreSQL Serverless v2 Multi-AZ",
        "estimated_monthly_usd": 3200,
    })


engineering_lead = Agent(
    name="EngineeringLead",
    model=DEFAULT_MODEL,
    instructions=(
        "You are the VP of Engineering leading the technical organization. "
        "When given a product initiative:\n"
        "1. Use `design_api_contracts` to specify architecture protocols.\n"
        "2. Use `plan_cloud_topology` to design resilient infrastructure.\n"
        "3. Deliver a consolidated Engineering Briefing covering API contracts, infrastructure cost, and rollout phases."
    ),
    tools=[design_api_contracts, plan_cloud_topology],
)


# -------------------------------------------------------------------------
# Cluster 2: Marketing & Growth Tools & Agents
# -------------------------------------------------------------------------

@function_tool
def analyze_target_personas(vertical: str) -> str:
    """Analyze buyer personas, pain points, and CAC expectations."""
    return json.dumps({
        "vertical": vertical,
        "ideal_customer": "Staff Software Engineers and Heads of Infrastructure",
        "primary_pain_point": "High latency and fragility in existing multi-agent integrations",
        "recommended_cac_usd": 1800,
    })


@function_tool
def plan_go_to_market_channels(budget_usd: float) -> str:
    """Allocate marketing budget across developer community, conferences, and technical content."""
    return json.dumps({
        "budget": budget_usd,
        "allocations": {
            "developer_advocacy_oss": "45%",
            "technical_podcasts_sponsorship": "30%",
            "hacker_news_launch_pr": "25%",
        },
        "expected_lead_velocity": "450 qualified MQLs / month",
    })


marketing_lead = Agent(
    name="MarketingLead",
    model=DEFAULT_MODEL,
    instructions=(
        "You are the Chief Marketing Officer (CMO). "
        "When given a product initiative:\n"
        "1. Use `analyze_target_personas` to profile the target developer demographic.\n"
        "2. Use `plan_go_to_market_channels` to allocate the launch budget.\n"
        "3. Deliver an integrated Go-To-Market strategy briefing."
    ),
    tools=[analyze_target_personas, plan_go_to_market_channels],
)


# -------------------------------------------------------------------------
# Executive Council (Top-Level Coordinator)
# -------------------------------------------------------------------------

eng_tool = engineering_lead.as_tool(
    tool_name="consult_engineering_team",
    tool_description="Delegates full technical architecture, API design, and cloud topology to the Engineering department.",
)

mktg_tool = marketing_lead.as_tool(
    tool_name="consult_marketing_team",
    tool_description="Delegates go-to-market strategy, persona profiling, and launch budget allocation to the Marketing department.",
)

executive_ceo = Agent(
    name="ExecutiveCEO",
    model=DEFAULT_MODEL,
    instructions=(
        "You are the Chief Executive Officer directing an enterprise product launch. "
        "To execute the initiative:\n"
        "1. Consult your Engineering department via `consult_engineering_team`.\n"
        "2. Consult your Marketing department via `consult_marketing_team`.\n"
        "3. Synthesize both department briefings into an Executive Unified Launch Dossier "
        "aligning engineering delivery milestones with go-to-market campaigns."
    ),
    tools=[eng_tool, mktg_tool],
)


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(initiative: str | None = None) -> str:
    """Execute federated multi-team swarm orchestration."""
    ensure_api_key()

    default_init = (
        "Launch 'AgentMesh': A real-time, low-latency multi-agent networking runtime for enterprise developers. "
        "Total initial launch budget is $40,000, deployment target is AWS us-east-1."
    )
    user_prompt = initiative or default_init

    print_header(
        "Pattern 13: Federated Multi-Team Swarm",
        "Two-level federated cluster topology organizing autonomous departments",
    )

    print_explainer(
        summary="An executive steering agent coordinates semi-autonomous department leads (Engineering & Marketing), who each lead specialized sub-teams.",
        communication_mechanism="Hierarchical federation: cluster-internal tool collaboration rolled up into inter-department team lead tools (`as_tool`).",
        when_to_use=[
            "Large-scale enterprise workflows with distinct functional domains.",
            "Eliminating chaotic cross-talk between developers and marketing specialists.",
            "Structuring agent architectures to mirror organizational Conway's Law.",
        ],
    )

    console.print(f"[bold cyan]Enterprise Initiative:[/bold cyan] {user_prompt}\n")

    print_agent_step("ExecutiveCEO", "Directing department leads across Engineering and Marketing...")
    result = await Runner.run(executive_ceo, user_prompt)

    # Trace tool calls
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

    print_result_panel("Unified Enterprise Launch Dossier", str(result.final_output))
    return str(result.final_output)


if __name__ == "__main__":
    asyncio.run(run())
