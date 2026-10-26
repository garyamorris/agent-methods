r"""
Pattern 02: Router / Triage Dispatcher (Star Topology with Real APIs)
=====================================================================

Architecture Overview:
----------------------
The Router (or Triage) pattern decouples frontline classification from specialized execution.
A lightweight front-door classifier analyzes incoming inquiries and executes an immediate
SDK handoff (`handoff(target)`) to a targeted domain specialist equipped with real-world APIs:
  1. GitHub Repository Health Specialist: Queries the live GitHub REST API for real open issues,
     stargazer velocity, fork counts, and activity dates.
  2. HackerNews Tech Trends Specialist: Queries the live HackerNews search API for real community
     discussions, developer sentiment, and breaking alerts.
  3. Network Infrastructure Specialist: Executes real HTTP latency probes measuring round-trip
     connectivity times to major cloud API endpoints.

Communication Topology:
-----------------------
                           +-------------------+
                           |    User Query     |
                           +-------------------+
                                     |
                                     v
                           +-------------------+
                           |   Triage Router   |
                           +-------------------+
                                     |
                +--------------------+--------------------+
                | (handoff)          | (handoff)          | (handoff)
                v                    v                    v
      +-------------------+ +-------------------+ +-------------------+
      | GitHub Specialist | | HackerNews Scout  | | Network SRE       |
      +-------------------+ +-------------------+ +-------------------+
                |                    |                    |
                v (Real HTTP)        v (Real HTTP)        v (Real HTTP)
        [api.github.com]     [hn.algolia.com]     [Live Ping / Probe]
                |                    |                    |
                +--------------------+--------------------+
                                     |
                                     v
                           +-------------------+
                           |  Final Specialist |
                           |     Response      |
                           +-------------------+

When to Use:
------------
- Multi-domain operations platforms (DevOps, Customer Support, IT helpdesks).
- Eliminating tool overload and hallucination by keeping specialist prompt instructions isolated.
- Dispatching user requests to specialized tools without keeping the dispatcher in the loop.
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
    print_handoff,
    print_result_panel,
    print_explainer,
    CommsTracer,
)

# -------------------------------------------------------------------------
# Real Public API Specialist Tools
# -------------------------------------------------------------------------

@function_tool
def check_github_repo_health(owner: str, repo: str) -> str:
    """Fetch REAL real-time repository health, open issues, and stars from the GitHub REST API.

    Args:
        owner: GitHub organization or username (e.g. 'openai', 'pallets', 'astral-sh').
        repo: Repository name (e.g. 'openai-agents-python', 'flask', 'uv').
    """
    url = f"https://api.github.com/repos/{owner}/{repo}"
    data = fetch_json(url)

    if "error" in data:
        return json.dumps({"error": data["error"], "repo": f"{owner}/{repo}"})

    return json.dumps({
        "repository": f"{owner}/{repo}",
        "source": "GitHub Public REST API",
        "stars": data.get("stargazers_count"),
        "open_issues_count": data.get("open_issues_count"),
        "forks": data.get("forks_count"),
        "default_branch": data.get("default_branch"),
        "license": (data.get("license") or {}).get("name", "None"),
        "last_pushed_at": data.get("pushed_at"),
        "description": data.get("description"),
    })


@function_tool
def fetch_hackernews_discussions(search_term: str) -> str:
    """Search REAL trending technology discussions and community sentiment on HackerNews.

    Args:
        search_term: Keyword or technology to search (e.g. 'deepseek', 'redis', 'postgres').
    """
    url = "https://hn.algolia.com/api/v1/search"
    params = {"query": search_term, "tags": "story", "hitsPerPage": 3}
    data = fetch_json(url, params=params)

    hits = data.get("hits", [])
    extracted = [
        {
            "title": h.get("title"),
            "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
            "points": h.get("points"),
            "num_comments": h.get("num_comments"),
            "created_at": h.get("created_at"),
        }
        for h in hits
    ]
    return json.dumps({"query": search_term, "source": "HackerNews Algolia API", "top_stories": extracted})


@function_tool
def probe_endpoint_latency(endpoint_url: str) -> str:
    """Perform a REAL live HTTP network latency probe to measure round-trip response time.

    Args:
        endpoint_url: Target URL to measure (e.g. 'https://api.github.com' or 'https://api.deepseek.com').
    """
    import httpx

    url = endpoint_url if endpoint_url.startswith("http") else f"https://{endpoint_url}"
    start = time.perf_counter()
    try:
        with httpx.Client(timeout=6.0, follow_redirects=True) as client:
            resp = client.get(url)
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            return json.dumps({
                "target_url": url,
                "status_code": resp.status_code,
                "latency_ms": elapsed_ms,
                "http_protocol": resp.http_version,
                "connectivity": "HEALTHY" if resp.status_code < 400 else "DEGRADED",
            })
    except Exception as e:
        return json.dumps({
            "target_url": url,
            "error": str(e),
            "connectivity": "UNREACHABLE",
        })


# -------------------------------------------------------------------------
# Define Specialists and Triage Router
# -------------------------------------------------------------------------

github_agent = Agent(
    name="GitHubHealthSpecialist",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an Open-Source Health & Codebase Specialist. "
        "Use `check_github_repo_health` to inspect real open issues, star counts, and activity dates on GitHub. "
        "Synthesize a clear maintenance assessment."
    ),
    tools=[check_github_repo_health],
)

hn_trends_agent = Agent(
    name="HackerNewsCommunitySpecialist",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Tech Trends & Community Sentiment Specialist. "
        "Use `fetch_hackernews_discussions` to search real live HackerNews threads. "
        "Summarize community developer discourse with titles, scores, and links."
    ),
    tools=[fetch_hackernews_discussions],
)

network_agent = Agent(
    name="NetworkLatencySpecialist",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Cloud Infrastructure & Network SRE. "
        "Use `probe_endpoint_latency` to measure real round-trip connectivity to live endpoints. "
        "Evaluate latency benchmarks and service connectivity."
    ),
    tools=[probe_endpoint_latency],
)

triage_agent = Agent(
    name="TriageRouter",
    model=DEFAULT_MODEL,
    instructions=(
        "You are the frontline triage dispatcher. Analyze user queries and immediately hand off:\n"
        "- GitHub repositories, open-source codebases, stars, issues -> hand off to GitHubHealthSpecialist.\n"
        "- HackerNews discussions, community sentiment, tech news -> hand off to HackerNewsCommunitySpecialist.\n"
        "- Network connectivity, latency probes, API responsiveness -> hand off to NetworkLatencySpecialist.\n"
        "Never attempt to solve these domain problems yourself; always hand off promptly."
    ),
    handoffs=[github_agent, hn_trends_agent, network_agent],
)


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(query: str | None = None, example_id: int = 1, tracer: CommsTracer | None = None) -> str:
    """Execute triage routing with real public API handoff execution."""
    ensure_api_key()

    if example_id == 2:
        default_query = "What is the developer community discussing about DeepSeek right now on HackerNews?"
    elif example_id == 3:
        default_query = "Probe the real network latency to https://api.github.com and let me know if it's healthy."
    else:
        default_query = "Check the live repository health and open issue count for owner 'astral-sh' repo 'uv'."

    user_prompt = query or default_query

    print_header(
        "Pattern 02: Router / Triage Dispatcher",
        "Frontline intent classifier delegating to specialists with REAL APIs",
    )

    print_explainer(
        summary="A dispatcher router classifies queries and hands off conversation control to specialized domain agents backed by real HTTP endpoints.",
        communication_mechanism="Zero-shot intent classification followed by native SDK handoff to live-API specialist.",
        when_to_use=[
            "Multi-domain developer platforms routing between codebases, news sentiment, and infrastructure probes.",
            "Eliminating prompt bloat and tool conflicts across unrelated functional areas.",
            "Specialist agents requiring dedicated personas and distinct API clients.",
        ],
    )

    console.print(f"[bold cyan]User Query:[/bold cyan] {user_prompt}\n")

    if tracer is None:
        tracer = CommsTracer(scenario_title="Pattern 02: Router / Triage")
    tracer.record_user_query(user_prompt, triage_agent.name)

    print_agent_step("TriageRouter", "Analyzing user intent and routing to live specialist...")
    result = await Runner.run(triage_agent, user_prompt, hooks=tracer)

    # Render complete inter-agent comms ledger and sequence diagram
    tracer.render_summary_ledger()
    tracer.render_sequence_diagram()

    print_agent_step("System", f"Final responding agent: [bold cyan]{result.last_agent.name}[/bold cyan]")
    print_result_panel(f"Response from {result.last_agent.name}", str(result.final_output))
    return str(result.final_output)


if __name__ == "__main__":
    asyncio.run(run())
