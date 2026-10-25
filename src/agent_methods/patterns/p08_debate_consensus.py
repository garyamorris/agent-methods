r"""
Pattern 08: Multi-Agent Debate & Deliberation (Adversarial Roundtable with Real Evidence)
========================================================================================

Architecture Overview:
----------------------
Single-agent reasoning often suffers from confirmation bias, sycophancy, or bland neutrality
on complex architectural dilemmas. The Multi-Agent Debate pattern pits two or more agents
with diametrically opposing perspectives against one another in structured deliberation backed
by REAL empirical evidence:
  1. Opening Statements: Advocate A and Advocate B independently present their strongest cases,
     querying real GitHub metrics and HackerNews engineering discussions for live evidence.
  2. Cross-Examination & Rebuttal: Each advocate is given the opponent's opening transcript to
     critique flaws, operational risks, and unstated assumptions.
  3. Adjudication & Consensus: An impartial Chief Technology Officer / Moderator evaluates both
     sides' rigor, discounts fallacies, and delivers a balanced, nuanced situational verdict.

Real-World Production Scenarios Demonstrated:
---------------------------------------------
- Example 1 (Modular Monolith vs. Microservices):
  AdvocateModularMonolith defends monolithic velocity and transactional integrity;
  AdvocateMicroservices defends decoupled auto-scaling and organizational Conway's Law scaling.
  Both cite real GitHub repo patterns and HackerNews production post-mortems.
- Example 2 (Relational PostgreSQL vs. Distributed DynamoDB / NoSQL):
  AdvocateRelational vs. AdvocateDistributed debate transactional consistency vs. global horizontal scale.

Communication Topology:
-----------------------
                       +-----------------------+
                       |    Dilemma Prompt     |
                       +-----------------------+
                                   |
                                   v
             +---------------------+---------------------+
             | (Round 1: Opening)                        | (Round 1: Opening)
             v                                           v
    +-----------------+                         +-----------------+
    |   Advocate A    |  <-- Live Evidence      |   Advocate B    | <-- Live Evidence
    | (Pro-Monolith)  |      (GitHub/HN APIs)   | (Microservices) |     (GitHub/HN APIs)
    +-----------------+                         +-----------------+
             |                                           |
             |-------- (Round 2: Cross Rebuttal) --------|
             v                                           v
    +-----------------+                         +-----------------+
    |   Advocate A    |                         |   Advocate B    |
    |    (Rebuttal)   |                         |    (Rebuttal)   |
    +-----------------+                         +-----------------+
             \                                           /
              \                                         /
               +-------------------+-------------------+
                                   |
                                   v
                       +-----------------------+
                       |    Impartial Judge    |
                       |      (Moderator)      |
                       +-----------------------+
                                   |
                                   v
                       +-----------------------+
                       |   Consensus Verdict   |
                       +-----------------------+

When to Use:
------------
- High-stakes strategic decisions (Build vs. Buy, Monolith vs. Microservices, SQL vs. NoSQL).
- Mitigating cognitive biases and discovering edge-case failure modes in proposed solutions.
- Executive decision support requiring thorough stress-testing before capital commitment.

OpenAI Agents SDK Primitives:
-----------------------------
- Multiple `Agent` instances parameterized with contrasting personas and strict instructions.
- Controlled conversational turn passing through `Runner.run`.
- Real public API evidence tools (`fetch_json` against GitHub & HackerNews).
- Impartial synthesis agent acting as the jury/moderator.
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
# Real Public API Evidence Tools
# -------------------------------------------------------------------------

@function_tool
def query_github_framework_adoption(owner_repo: str) -> str:
    """Fetch REAL repository adoption stats, stars, and open issues from GitHub REST API.

    Args:
        owner_repo: Repository formatted as 'owner/repo' (e.g. 'rails/rails', 'expressjs/express').
    """
    url = f"https://api.github.com/repos/{owner_repo}"
    data = fetch_json(url)

    if "error" in data:
        return json.dumps({"error": data["error"], "target": owner_repo})

    return json.dumps({
        "repo": owner_repo,
        "source": "GitHub REST API",
        "stars": data.get("stargazers_count"),
        "open_issues": data.get("open_issues_count"),
        "forks": data.get("forks_count"),
        "last_commit": data.get("pushed_at"),
    })


@function_tool
def search_community_engineering_case_studies(search_query: str) -> str:
    """Search REAL production post-mortems and developer feedback on HackerNews.

    Args:
        search_query: Search term (e.g. 'microservices regret', 'monolith scaling', 'dynamodb postgres').
    """
    url = "https://hn.algolia.com/api/v1/search"
    params = {"query": search_query, "tags": "story", "hitsPerPage": 2}
    data = fetch_json(url, params=params)

    hits = data.get("hits", [])
    extracted = [
        {"title": h.get("title"), "points": h.get("points"), "comments": h.get("num_comments")}
        for h in hits
    ]
    return json.dumps({"search": search_query, "source": "HackerNews Algolia API", "discussions": extracted})


# -------------------------------------------------------------------------
# Define Debater and Judge Agents
# -------------------------------------------------------------------------

advocate_monolith = Agent(
    name="AdvocateModularMonolith",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an elite Principal Systems Architect championing Modular Monoliths. "
        "Argue vigorously why modular monoliths maximize developer velocity, reduce operational complexity, "
        "simplify transactional integrity (ACID), and prevent distributed systems overhead for early-to-mid stage companies. "
        "You may call `search_community_engineering_case_studies` or `query_github_framework_adoption` for real evidence. "
        "Be sharp, fact-based, and compelling."
    ),
    tools=[search_community_engineering_case_studies, query_github_framework_adoption],
)

advocate_microservices = Agent(
    name="AdvocateMicroservices",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Cloud-Native Distributed Systems Fellow championing Microservices. "
        "Argue vigorously why decoupled microservices are essential for independent deployability, "
        "fault isolation, granular auto-scaling, polyglot technology stacks, and enterprise organizational scaling (Conway's Law). "
        "You may call `search_community_engineering_case_studies` or `query_github_framework_adoption` for real evidence. "
        "Be sharp, fact-based, and compelling."
    ),
    tools=[search_community_engineering_case_studies, query_github_framework_adoption],
)

judge_moderator = Agent(
    name="JudicialModerator",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a neutral Chief Technology Officer and Supreme Arbiter. "
        "You have observed a rigorous debate between AdvocateModularMonolith and AdvocateMicroservices. "
        "Evaluate the merits and rebuttals of both arguments.\n"
        "1. Identify the strongest points made by each side.\n"
        "2. Identify flaws or unrealistic assumptions in each position.\n"
        "3. Provide a definitive, situational verdict: when to choose Option A vs Option B based on team size, "
        "traffic, latency requirements, and company stage."
    ),
)


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(query: str | None = None, example_id: int = 1) -> str:
    """Execute 2-round adversarial debate followed by judicial consensus."""
    ensure_api_key()

    if example_id == 2:
        default_query = (
            "We are a Series B fintech processing 15,000 transactions/min. "
            "Should we build our new core ledger on an ACID Relational PostgreSQL database or a Distributed NoSQL / DynamoDB?"
        )
        scenario_title = "Example 2: Core Ledger Database Architecture (PostgreSQL vs. DynamoDB)"
    else:
        default_query = (
            "Our company has 25 engineers and is scaling our core B2B SaaS platform. "
            "Should we build as a clean Modular Monolith or decompose immediately into Microservices?"
        )
        scenario_title = "Example 1: Software Architecture Dilemma (Modular Monolith vs. Microservices)"

    dilemma_prompt = query or default_query

    print_header(
        "Pattern 08: Multi-Agent Debate & Deliberation",
        f"Roundtable Arena: {scenario_title}",
    )

    print_explainer(
        summary="Two adversarial advocates debate with real evidence tools (GitHub / HackerNews), critique each other's claims in Round 2, and submit their arguments to a neutral judicial arbiter.",
        communication_mechanism="Turn-based adversarial exchange with evidence-gathering tools and impartial judicial synthesis.",
        when_to_use=[
            "High-stakes architectural or strategic dilemmas.",
            "Mitigating bias and discovering hidden operational failure modes.",
            "Formulating clear situational heuristics (when to use X vs Y).",
        ],
    )

    console.print(f"[bold cyan]Architectural Dilemma:[/bold cyan] {dilemma_prompt}\n")

    # Round 1: Opening Arguments
    console.print("[bold yellow]═══════ Round 1: Opening Arguments ═══════[/bold yellow]")
    print_agent_step(advocate_monolith.name, "Formulating opening case for Modular Monolith...")
    res_m1 = await Runner.run(advocate_monolith, dilemma_prompt)
    opening_monolith = str(res_m1.final_output)

    print_agent_step(advocate_microservices.name, "Formulating opening case for Microservices...")
    res_s1 = await Runner.run(advocate_microservices, dilemma_prompt)
    opening_microservices = str(res_s1.final_output)

    # Round 2: Cross-Rebuttal
    console.print("\n[bold yellow]═══════ Round 2: Cross-Rebuttal ═══════[/bold yellow]")
    print_agent_step(advocate_monolith.name, "Rebutting Microservices claims...")
    reb_m_prompt = (
        f"The user dilemma is: {dilemma_prompt}\n\n"
        f"Your opponent made this case for Microservices:\n{opening_microservices}\n\n"
        f"Deliver a rigorous, surgical rebuttal pointing out distributed systems fallacies and operational overhead."
    )
    res_m2 = await Runner.run(advocate_monolith, reb_m_prompt)
    rebuttal_monolith = str(res_m2.final_output)

    print_agent_step(advocate_microservices.name, "Rebutting Modular Monolith claims...")
    reb_s_prompt = (
        f"The user dilemma is: {dilemma_prompt}\n\n"
        f"Your opponent made this case for Modular Monoliths:\n{opening_monolith}\n\n"
        f"Deliver a rigorous rebuttal pointing out coupling traps, deploy bottlenecks, and Conway's Law scaling limits."
    )
    res_s2 = await Runner.run(advocate_microservices, reb_s_prompt)
    rebuttal_microservices = str(res_s2.final_output)

    # Round 3: Adjudication
    console.print("\n[bold yellow]═══════ Judicial Adjudication ═══════[/bold yellow]")
    print_agent_step(judge_moderator.name, "CTO Judicial Moderator evaluating arguments and formulating verdict...")

    judicial_brief = (
        f"Dilemma: {dilemma_prompt}\n\n"
        f"--- ADVOCATE MODULAR MONOLITH (OPENING) ---\n{opening_monolith}\n\n"
        f"--- ADVOCATE MICROSERVICES (OPENING) ---\n{opening_microservices}\n\n"
        f"--- ADVOCATE MODULAR MONOLITH (REBUTTAL) ---\n{rebuttal_monolith}\n\n"
        f"--- ADVOCATE MICROSERVICES (REBUTTAL) ---\n{rebuttal_microservices}\n"
    )

    verdict_res = await Runner.run(judge_moderator, judicial_brief)
    final_verdict = str(verdict_res.final_output)

    print_result_panel("Chief Technology Officer: Definitive Consensus Verdict", final_verdict)
    return final_verdict


if __name__ == "__main__":
    asyncio.run(run())
