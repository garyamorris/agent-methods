r"""
Pattern 04: Supervisor & Subagents (Orchestrator-Workers with Real APIs)
========================================================================

Architecture Overview:
----------------------
In the Orchestrator-Workers pattern, a central Supervisor coordinates specialized Subagents.
Crucially, unlike handoffs where conversational ownership transfers away, in this pattern
subagents are packaged as callable tools using `subagent.as_tool()`.

The Supervisor retains conversational ownership at all times:
  1. Supervisor decomposes a high-level goal into specialized subtasks.
  2. Supervisor invokes Subagents like tools (`subagent.as_tool()`), providing targeted inputs.
  3. Each Subagent executes in an isolated context window, querying REAL public APIs:
     - Subagent A (Market Scout): Queries real HackerNews Algolia API for developer buzz.
     - Subagent B (Tech Evaluator): Queries real GitHub REST API for repo velocity & open issues.
     - Subagent C (Quant Analyst): Runs real unit economics and financial risk calculations.
  4. Each Subagent returns its distilled conclusion back to the Supervisor.
  5. Supervisor aggregates the subagent findings into an executive synthesis.

Real-World Production Scenarios Demonstrated:
---------------------------------------------
- Example 1 (Tech Due Diligence & Commercialization):
  Supervisor analyzes an open-source project (e.g. 'astral-sh/uv' or 'tiangolo/fastapi') by
  dispatching the Tech Evaluator to check real GitHub metrics, the Market Scout to search
  real HackerNews developer discussions, and the Quant Analyst to model SaaS unit economics.
- Example 2 (Enterprise Infrastructure Migration Due Diligence):
  Supervisor assesses migrating from legacy stack to modern cloud runtime by combining
  live GitHub activity on key frameworks, developer community war stories on HackerNews,
  and hosting cost-to-serve models.

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
             | (HackerNews)  |     |     | (Unit Econ)   |
             +---------------+     v     +---------------+
                    |     +---------------+      |
                    |     | TechArchitect |      |
                    |     | (GitHub API)  |      |
                    |     +---------------+      |
                    \              |             /
                     \---> [Distilled Return] <--/
                                   |
                                   v
                       +-----------------------+
                       | Consolidated Executive|
                       |       Synthesis       |
                       +-----------------------+

When to Use:
------------
- Complex projects requiring deep domain specialization and context hygiene.
- Preventing verbose research outputs from polluting the main executive conversation history.
- Hierarchical workflows requiring a single coordinator accountable for final output quality.

OpenAI Agents SDK Primitives:
-----------------------------
- `subagent.as_tool(tool_name=..., tool_description=...)`: Converts an `Agent` into a callable `FunctionTool`.
- `Runner.run(supervisor, input)`: Seamlessly runs the supervisor, which automatically triggers nested subagent execution!
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
# Real Public API Tools for Subagents
# -------------------------------------------------------------------------

@function_tool
def fetch_hn_developer_sentiment(topic: str) -> str:
    """Search REAL developer sentiment, war stories, and community trends on HackerNews.

    Args:
        topic: Keyword or project to search (e.g. 'uv package manager', 'fastapi', 'kubernetes').
    """
    url = "https://hn.algolia.com/api/v1/search"
    params = {"query": topic, "tags": "story", "hitsPerPage": 3}
    data = fetch_json(url, params=params)

    hits = data.get("hits", [])
    extracted = [
        {
            "title": h.get("title"),
            "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
            "points": h.get("points"),
            "comments": h.get("num_comments"),
            "created_at": h.get("created_at"),
        }
        for h in hits
    ]
    return json.dumps({"topic": topic, "source": "HackerNews Algolia API", "top_stories": extracted})


@function_tool
def fetch_github_codebase_health(owner: str, repo: str) -> str:
    """Fetch REAL repository metrics, star counts, and open issues from GitHub REST API.

    Args:
        owner: Repository owner or org (e.g. 'astral-sh', 'tiangolo', 'pallets').
        repo: Repository name (e.g. 'uv', 'fastapi', 'flask').
    """
    url = f"https://api.github.com/repos/{owner}/{repo}"
    data = fetch_json(url)

    if "error" in data:
        return json.dumps({"error": data["error"], "repo": f"{owner}/{repo}"})

    return json.dumps({
        "repository": f"{owner}/{repo}",
        "source": "GitHub REST API",
        "stars": data.get("stargazers_count"),
        "open_issues": data.get("open_issues_count"),
        "forks": data.get("forks_count"),
        "license": (data.get("license") or {}).get("name", "Unknown"),
        "last_push": data.get("pushed_at"),
        "description": data.get("description"),
    })


@function_tool
def model_unit_economics(cac_usd: float, ltv_usd: float, monthly_churn_pct: float) -> str:
    """Calculate venture unit economics, LTV:CAC ratio, and capital payback periods.

    Args:
        cac_usd: Customer Acquisition Cost in USD.
        ltv_usd: Projected Customer Lifetime Value in USD.
        monthly_churn_pct: Monthly churn rate as a percentage (e.g. 2.5 for 2.5%).
    """
    ratio = round(ltv_usd / cac_usd, 2) if cac_usd > 0 else 0.0
    payback_months = round(cac_usd / (ltv_usd * 0.08), 1) if ltv_usd > 0 else 12.0
    return json.dumps({
        "cac_usd": cac_usd,
        "ltv_usd": ltv_usd,
        "ltv_to_cac_ratio": ratio,
        "estimated_payback_months": payback_months,
        "health_verdict": "Venture Scale (>3.5x)" if ratio >= 3.5 else "Sub-optimal (<3.5x)",
        "annualized_churn_pct": round(monthly_churn_pct * 12, 1),
    })


# -------------------------------------------------------------------------
# Define Subagents with Real API Tools
# -------------------------------------------------------------------------

market_analyst_agent = Agent(
    name="MarketScoutSubagent",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an expert Market Intelligence Subagent. "
        "Call `fetch_hn_developer_sentiment` to gather REAL developer trends and community reception from HackerNews. "
        "Distill your findings into a 2-3 bullet point summary highlighting commercial opportunities and community risks."
    ),
    tools=[fetch_hn_developer_sentiment],
)

tech_architect_agent = Agent(
    name="TechArchitectSubagent",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Senior Technology Architect Subagent. "
        "Call `fetch_github_codebase_health` to inspect REAL repository health, stars, and open issues from GitHub. "
        "Synthesize the repository's maintenance velocity, community backing, and architectural maturity."
    ),
    tools=[fetch_github_codebase_health],
)

financial_modeler_agent = Agent(
    name="FinancialModelerSubagent",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Quantitative Financial Modeler Subagent. "
        "Call `model_unit_economics` to calculate LTV:CAC viability and capital payback curves. "
        "Provide a concise recommendation on commercial margin and sustainability."
    ),
    tools=[model_unit_economics],
)

# -------------------------------------------------------------------------
# Define Supervisor (Wraps Subagents as Tools via as_tool())
# -------------------------------------------------------------------------

lead_strategist = Agent(
    name="LeadEnterpriseStrategist",
    model=DEFAULT_MODEL,
    instructions=(
        "You are the Lead Enterprise Strategist and Orchestrator. "
        "When an executive requests strategic due diligence, you coordinate your 3 specialized subagents:\n"
        "1. Call `market_analyst_agent` to evaluate community buzz and market sentiment.\n"
        "2. Call `tech_architect_agent` to evaluate GitHub engineering health and repo velocity.\n"
        "3. Call `financial_modeler_agent` to model economic sustainability.\n\n"
        "Do NOT guess repository numbers or market sentiment; always rely on the subagents' tool results. "
        "Synthesize all 3 returns into a coherent, executive-level investment memo."
    ),
    tools=[
        market_analyst_agent.as_tool(
            tool_name="consult_market_analyst",
            tool_description="Dispatches the Market Scout to evaluate developer sentiment and community buzz on HackerNews.",
        ),
        tech_architect_agent.as_tool(
            tool_name="consult_tech_architect",
            tool_description="Dispatches the Tech Architect to inspect repository health, stars, and issues via GitHub REST API.",
        ),
        financial_modeler_agent.as_tool(
            tool_name="consult_financial_modeler",
            tool_description="Dispatches the Financial Modeler to calculate unit economics and capital payback metrics.",
        ),
    ],
)


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(query: str | None = None, example_id: int = 1) -> str:
    """Execute Supervisor & Subagents orchestrator loop against real public APIs."""
    ensure_api_key()

    if example_id == 2:
        default_query = (
            "Perform comprehensive technology due diligence on the open-source repository 'tiangolo/fastapi'. "
            "Inspect its real GitHub repository health, survey HackerNews developer reception, "
            "and model unit economics assuming a CAC of $450, an enterprise LTV of $2,400, and 2.0% monthly churn."
        )
        scenario_title = "Example 2: FastAPI Enterprise Adoption & Commercialization"
    else:
        default_query = (
            "We are evaluating standardizing our company tooling around 'astral-sh/uv'. "
            "Please orchestrate your subagents: fetch real GitHub metrics for 'astral-sh/uv', "
            "gather real HackerNews sentiment on 'uv package manager', and model our developer tool economics "
            "assuming CAC of $300, LTV of $1,800, and 1.5% monthly churn."
        )
        scenario_title = "Example 1: Astral uv Ecosystem Due-Diligence Briefing"

    user_prompt = query or default_query

    print_header(
        "Pattern 04: Supervisor & Subagents",
        f"Orchestrator-Workers with as_tool(): {scenario_title}",
    )

    print_explainer(
        summary="A central Supervisor coordinates isolated Subagents wrapped as tools via `subagent.as_tool()`, invoking real public APIs.",
        communication_mechanism="Isolated agent-as-a-tool invocations preventing context pollution while retaining supervisor ownership.",
        when_to_use=[
            "Complex due diligence requiring independent research threads.",
            "Keeping main supervisor conversation context clean and concise.",
            "Orchestrator-Workers workflows where central coordinator must deliver final synthesis.",
        ],
    )

    console.print(f"[bold cyan]User Query:[/bold cyan] {user_prompt}\n")

    print_agent_step(lead_strategist.name, "Supervisor delegating subtasks to subagent tools...")
    result = await Runner.run(lead_strategist, user_prompt)

    # Trace supervisor tool calls
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
        elif item_type == "tool_call_output_item":
            output = str(getattr(item, "output", ""))
            console.print(f"      [dim green]↳ Subagent Return:[/dim green] [dim]{output[:140]}...[/dim]")

    print_result_panel("Consolidated Executive Investment Memo", str(result.final_output))
    return str(result.final_output)


if __name__ == "__main__":
    asyncio.run(run())
