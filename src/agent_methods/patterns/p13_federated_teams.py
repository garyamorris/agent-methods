r"""
Pattern 13: Federated Multi-Team Swarm (Hierarchical Swarm of Swarms with Real APIs)
===================================================================================

Architecture Overview:
----------------------
As multi-agent systems expand to dozens of specialized agents, flat peer meshes degrade
into chaotic handoff loops, while flat supervisor hierarchies suffer from severe bottlenecking.
The Federated Multi-Team Swarm organizes agents according to Conway's Law:
  1. Executive Steering Council (CEO Agent): High-level strategic coordinator.
  2. Autonomous Functional Clusters (Teams):
     - Engineering Cluster: Engineering Lead coordinates technical metrics via the GitHub REST API.
     - Growth & Marketing Cluster: Marketing Lead coordinates launch sentiment via the HackerNews Algolia API.
  3. Internal vs External Communication:
     - Inside a cluster, peer agents collaborate closely using specialized domain tools.
     - Across clusters, only Team Leads communicate, presenting distilled department briefings via `as_tool()`.

Real-World Production Scenarios Demonstrated:
---------------------------------------------
- Example 1 (Full-Lifecycle Product Launch Federation):
  Executive CEO coordinates simultaneous launch readiness: Engineering cluster verifies GitHub code
  maturity and releases, while Marketing cluster surveys developer sentiment and viral reach on HackerNews.
- Example 2 (Enterprise Cloud Service Modernization):
  Engineering evaluates architecture and latency budgets; Growth evaluates enterprise TAM and competitor positioning.

Communication Topology:
-----------------------
                       +-----------------------+
                       |   Executive Council   |
                       |      (CEO Agent)      |
                       +-----------------------+
                               /       \
                              /         \
         (as_tool: EngLead)  /           \ (as_tool: MktgLead)
                            v             v
                +---------------+     +---------------+
                |  Engineering  |     |   Marketing   |
                |   Team Lead   |     |   Team Lead   |
                +---------------+     +---------------+
                        |                     |
                        v (Real Tools)        v (Real Tools)
                [GitHub REST API]     [HackerNews Algolia API]
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
    fetch_json,
    console,
    print_header,
    print_agent_step,
    print_tool_call,
    print_result_panel,
    print_explainer,
)

# -------------------------------------------------------------------------
# Real Public API Tools for Clusters
# -------------------------------------------------------------------------

@function_tool
def fetch_github_team_velocity(owner: str, repo: str) -> str:
    """Fetch REAL repository release cadence, stars, and open issues from GitHub REST API.

    Args:
        owner: GitHub organization or username (e.g. 'astral-sh', 'openai').
        repo: Repository name (e.g. 'uv', 'openai-agents-python').
    """
    url = f"https://api.github.com/repos/{owner}/{repo}"
    data = fetch_json(url)

    if "error" in data:
        return json.dumps({"error": data["error"], "target": f"{owner}/{repo}"})

    return json.dumps({
        "repo": f"{owner}/{repo}",
        "source": "GitHub REST API",
        "stargazers": data.get("stargazers_count"),
        "open_issues": data.get("open_issues_count"),
        "forks": data.get("forks_count"),
        "license": (data.get("license") or {}).get("name", "Proprietary"),
        "last_pushed_at": data.get("pushed_at"),
    })


@function_tool
def fetch_hackernews_market_sentiment(product_keyword: str) -> str:
    """Fetch REAL developer sentiment and trending community discussions on HackerNews.

    Args:
        product_keyword: Product name or keyword (e.g. 'uv package manager', 'agent framework').
    """
    url = "https://hn.algolia.com/api/v1/search"
    params = {"query": product_keyword, "tags": "story", "hitsPerPage": 3}
    data = fetch_json(url, params=params)

    hits = data.get("hits", [])
    extracted = [
        {"title": h.get("title"), "points": h.get("points"), "comments": h.get("num_comments")}
        for h in hits
    ]
    return json.dumps({"keyword": product_keyword, "source": "HackerNews Algolia API", "stories": extracted})


# -------------------------------------------------------------------------
# Cluster Leads and Agents
# -------------------------------------------------------------------------

engineering_lead = Agent(
    name="VPofEngineeringLead",
    model=DEFAULT_MODEL,
    instructions=(
        "You are the VP of Engineering. "
        "When evaluating technical readiness, call `fetch_github_team_velocity` to query the REAL codebase metrics on GitHub. "
        "Distill code health, maintenance velocity, and technical architecture into an executive briefing."
    ),
    tools=[fetch_github_team_velocity],
)

marketing_lead = Agent(
    name="ChiefMarketingOfficerLead",
    model=DEFAULT_MODEL,
    instructions=(
        "You are the Chief Marketing Officer (CMO). "
        "When planning a launch campaign, call `fetch_hackernews_market_sentiment` to analyze REAL developer discussions on HackerNews. "
        "Formulate a go-to-market messaging strategy and launch timeline based on developer sentiment."
    ),
    tools=[fetch_hackernews_market_sentiment],
)

executive_ceo = Agent(
    name="ExecutiveChiefExecutiveOfficer",
    model=DEFAULT_MODEL,
    instructions=(
        "You are the Chief Executive Officer (CEO) and Head of the Executive Council. "
        "You oversee two autonomous clusters:\n"
        "1. Engineering Cluster (via `consult_engineering_team`)\n"
        "2. Marketing & Growth Cluster (via `consult_marketing_team`)\n\n"
        "Delegate to both department heads to gather technical status and go-to-market plans. "
        "Synthesize their distilled returns into a Unified Enterprise Launch Dossier."
    ),
    tools=[
        engineering_lead.as_tool(
            tool_name="consult_engineering_team",
            tool_description="Dispatches the Engineering Cluster to audit repository metrics and technical readiness via GitHub API.",
        ),
        marketing_lead.as_tool(
            tool_name="consult_marketing_team",
            tool_description="Dispatches the Marketing Cluster to analyze developer sentiment and plan launch strategy via HackerNews API.",
        ),
    ],
)


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(query: str | None = None, example_id: int = 1) -> str:
    """Execute federated multi-team swarm with cross-cluster tool delegation."""
    ensure_api_key()

    if example_id == 2:
        default_query = (
            "Coordinate our enterprise launch around 'openai/openai-agents-python'. "
            "Engineering must verify the GitHub repository readiness, and Marketing must "
            "survey current agent framework discussions on HackerNews to design our announcement strategy."
        )
        scenario_title = "Example 2: Agents SDK Platform Commercial Launch"
    else:
        default_query = (
            "We are preparing an enterprise commercial launch around 'astral-sh/uv'. "
            "Have Engineering inspect the repository velocity on GitHub, "
            "and have Marketing survey developer reception on HackerNews to formulate our launch strategy."
        )
        scenario_title = "Example 1: Astral uv Product Launch Federation"

    user_prompt = query or default_query

    print_header(
        "Pattern 13: Federated Multi-Team Swarm",
        f"Hierarchical Swarm of Swarms: {scenario_title}",
    )

    print_explainer(
        summary="Executive Council coordinates autonomous Engineering and Marketing clusters. Department leads invoke REAL public APIs (GitHub, HackerNews) and return distilled briefings to the CEO.",
        communication_mechanism="Hierarchical cluster federation where department leads are exposed as tools (`as_tool`) to the executive coordinator.",
        when_to_use=[
            "Enterprise workflows requiring cross-functional collaboration (Eng + Mktg + Ops).",
            "Eliminating flat mesh anarchy as agent headcounts scale.",
            "Keeping specialized technical and commercial vocabulary appropriately partitioned.",
        ],
    )

    console.print(f"[bold cyan]Executive Directive:[/bold cyan] {user_prompt}\n")

    print_agent_step(executive_ceo.name, "CEO delegating tasks across autonomous department clusters...")
    result = await Runner.run(executive_ceo, user_prompt)

    # Trace CEO tool calls
    for item in result.new_items:
        if getattr(item, "type", "") == "tool_call_item":
            raw = getattr(item, "raw_item", None)
            name = getattr(raw, "name", "tool")
            args = getattr(raw, "arguments", "{}")
            print_tool_call(name, args)

    print_result_panel("Unified Enterprise Launch Dossier", str(result.final_output))
    return str(result.final_output)


if __name__ == "__main__":
    asyncio.run(run())
