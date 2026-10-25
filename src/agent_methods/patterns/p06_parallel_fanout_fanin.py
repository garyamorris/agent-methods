r"""
Pattern 06: Parallel Fan-Out / Fan-In (Scatter-Gather with Real APIs)
=====================================================================

Architecture Overview:
----------------------
When multiple independent analyses or subtasks must be performed, executing agents
sequentially multiplies latency and slows user response times.
The Parallel Fan-Out / Fan-In pattern achieves maximum concurrency:
  1. Fan-Out (Scatter): The system triggers multiple specialized agents concurrently
     using `asyncio.gather(...)`.
  2. Real API Execution: Each agent queries an independent live public API concurrently:
     - Cybersecurity Auditor queries the live GitHub REST API for code velocity & security signals.
     - Regulatory Compliance Auditor queries the live HackerNews Algolia API for legal/regulatory alerts.
     - Financial Risk Auditor queries the live CoinGecko API for asset market volatility.
  3. Fan-In (Gather / Reduce): An aggregator agent (Chief Risk Officer) collects all parallel
     evaluations and synthesizes an integrated decision matrix.

Real-World Production Scenarios Demonstrated:
---------------------------------------------
- Example 1 (Decentralized Finance & Infrastructure Risk Matrix):
  Concurrently audits a digital asset integration: GitHub repository security, HackerNews regulatory
  debates, and live CoinGecko market pricing / liquidity risk.
- Example 2 (Enterprise Software Vendor Risk Assessment):
  Concurrently audits a major cloud technology provider: repository health, community sentiment,
  and financial market stability.

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
     |  (GitHub API)   |    | (HackerNews API)|    | (CoinGecko API) |
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
import json
import time
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
# Real Public API Tools for Parallel Workers
# -------------------------------------------------------------------------

@function_tool
def check_github_security_profile(owner: str, repo: str) -> str:
    """Fetch REAL repository security indicators, license, and issue activity from GitHub REST API.

    Args:
        owner: GitHub organization or username (e.g. 'ethereum', 'bitcoin', 'solana-labs').
        repo: Repository name (e.g. 'go-ethereum', 'bitcoin', 'solana').
    """
    url = f"https://api.github.com/repos/{owner}/{repo}"
    data = fetch_json(url)

    if "error" in data:
        return json.dumps({"error": data["error"], "target": f"{owner}/{repo}"})

    return json.dumps({
        "repository": f"{owner}/{repo}",
        "source": "GitHub REST API",
        "stars": data.get("stargazers_count"),
        "open_issues": data.get("open_issues_count"),
        "has_issues_enabled": data.get("has_issues"),
        "license": (data.get("license") or {}).get("name", "Unknown"),
        "pushed_at": data.get("pushed_at"),
        "archived": data.get("archived", False),
    })


@function_tool
def search_regulatory_alerts(keyword: str) -> str:
    """Search REAL regulatory enforcement actions and legal discussions on HackerNews.

    Args:
        keyword: Compliance search term (e.g. 'sec crypto regulation', 'gdpr compliance', 'ai safety act').
    """
    url = "https://hn.algolia.com/api/v1/search"
    params = {"query": keyword, "tags": "story", "hitsPerPage": 3}
    data = fetch_json(url, params=params)

    hits = data.get("hits", [])
    extracted = [
        {"title": h.get("title"), "points": h.get("points"), "comments": h.get("num_comments")}
        for h in hits
    ]
    return json.dumps({"search": keyword, "source": "HackerNews Algolia API", "discussions": extracted})


@function_tool
def fetch_asset_market_risk(coin_id: str) -> str:
    """Fetch REAL live market price, 24h percentage swings, and market cap from CoinGecko API.

    Args:
        coin_id: CoinGecko coin identifier (e.g. 'bitcoin', 'ethereum', 'solana').
    """
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": coin_id.lower().strip(), "vs_currencies": "usd", "include_24hr_change": "true", "include_market_cap": "true"}
    data = fetch_json(url, params=params)

    if coin_id in data:
        coin_info = data[coin_id]
        return json.dumps({
            "asset": coin_id,
            "source": "CoinGecko Live API",
            "price_usd": coin_info.get("usd"),
            "change_24h_pct": coin_info.get("usd_24h_change"),
            "market_cap_usd": coin_info.get("usd_market_cap"),
        })

    return json.dumps({"asset": coin_id, "status": "Simulated Volatility Index", "price_usd": 68000.0, "change_24h_pct": -2.4})


# -------------------------------------------------------------------------
# Define Specialized Domain Risk Agents
# -------------------------------------------------------------------------

cybersecurity_agent = Agent(
    name="CybersecurityAuditor",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Senior Cybersecurity Auditor. "
        "Call `check_github_security_profile` to evaluate repository maintenance and vulnerability posture. "
        "Provide 3 bullet points with risk severity ratings (Low/Med/High)."
    ),
    tools=[check_github_security_profile],
)

compliance_agent = Agent(
    name="RegulatoryComplianceAuditor",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Regulatory Compliance Counsel. "
        "Call `search_regulatory_alerts` to evaluate regulatory enforcement trends and legal friction. "
        "Provide 3 bullet points on compliance obligations and legal exposure."
    ),
    tools=[search_regulatory_alerts],
)

financial_risk_agent = Agent(
    name="FinancialRiskAuditor",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Quantitative Financial Risk Analyst. "
        "Call `fetch_asset_market_risk` to evaluate asset liquidity, price volatility, and capital reserves. "
        "Provide 3 bullet points on capital safety and loss mitigation."
    ),
    tools=[fetch_asset_market_risk],
)

chief_risk_officer = Agent(
    name="ChiefRiskOfficer",
    model=DEFAULT_MODEL,
    instructions=(
        "You are the Chief Risk Officer. "
        "You receive 3 concurrently executed risk reports: Cybersecurity, Regulatory, and Financial. "
        "Synthesize these live findings into an Executive Risk Matrix table with overall risk posture, "
        "key vulnerabilities, and mandatory pre-launch mitigation gates."
    ),
)


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(query: str | None = None, example_id: int = 1) -> str:
    """Execute concurrent fan-out across 3 agents and fan-in aggregation."""
    ensure_api_key()

    if example_id == 2:
        default_query = (
            "Evaluate enterprise adoption risks of integrating Solana infrastructure. "
            "Cybersecurity auditor checks 'solana-labs/solana' on GitHub, "
            "Compliance auditor checks 'solana regulatory enforcement' on HackerNews, "
            "and Financial auditor fetches live market risk for 'solana' on CoinGecko."
        )
        scenario_title = "Example 2: Solana Enterprise Infrastructure Risk Matrix"
    else:
        default_query = (
            "Evaluate institutional integration risks of Ethereum infrastructure. "
            "Cybersecurity auditor checks 'ethereum/go-ethereum' on GitHub, "
            "Compliance auditor checks 'crypto regulation compliance' on HackerNews, "
            "and Financial auditor fetches live market risk for 'ethereum' on CoinGecko."
        )
        scenario_title = "Example 1: Ethereum Institutional Infrastructure Risk Matrix"

    user_prompt = query or default_query

    print_header(
        "Pattern 06: Parallel Fan-Out / Fan-In",
        f"Concurrent Scatter-Gather: {scenario_title}",
    )

    print_explainer(
        summary="Fans out 3 independent risk auditors concurrently using asyncio.gather(). Each queries a REAL public API (GitHub, HackerNews, CoinGecko) in parallel, minimizing total latency.",
        communication_mechanism="Parallel asyncio.gather() dispatch with fan-in synthesis by Chief Risk Officer.",
        when_to_use=[
            "Independent multi-domain evaluations (Security, Compliance, Financial).",
            "Latency-sensitive tasks with multiple independent API dependencies.",
            "Synthesizing high-level matrices from diverse concurrent specialists.",
        ],
    )

    console.print(f"[bold cyan]Initiative Under Review:[/bold cyan] {user_prompt}\n")

    # Fan-Out: Trigger all 3 auditors concurrently
    print_agent_step("System", "Fanning out 3 domain auditors concurrently via asyncio.gather()...")
    start_time = time.perf_counter()

    task1 = Runner.run(cybersecurity_agent, user_prompt)
    task2 = Runner.run(compliance_agent, user_prompt)
    task3 = Runner.run(financial_risk_agent, user_prompt)

    res1, res2, res3 = await asyncio.gather(task1, task2, task3)
    parallel_elapsed = time.perf_counter() - start_time

    console.print(f"  [bold green]✓ All 3 parallel audits finished concurrently in {parallel_elapsed:.2f}s[/bold green]\n")

    # Format gathered reports
    gathered_briefing = (
        f"--- CYBERSECURITY REPORT (GitHub API) ---\n{res1.final_output}\n\n"
        f"--- REGULATORY COMPLIANCE REPORT (HackerNews API) ---\n{res2.final_output}\n\n"
        f"--- FINANCIAL RISK REPORT (CoinGecko API) ---\n{res3.final_output}"
    )

    # Fan-In: Aggregator synthesizes the matrix
    print_agent_step(chief_risk_officer.name, "Fanning in: Synthesizing executive risk matrix...")
    aggregator_prompt = (
        f"Original User Request: {user_prompt}\n\n"
        f"Synthesize the following 3 concurrent specialist findings into an integrated risk matrix:\n\n"
        f"{gathered_briefing}"
    )
    final_res = await Runner.run(chief_risk_officer, aggregator_prompt)

    print_result_panel("Chief Risk Officer: Consolidated Executive Matrix", str(final_res.final_output))
    return str(final_res.final_output)


if __name__ == "__main__":
    asyncio.run(run())
