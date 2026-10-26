r"""
Pattern 05: Sequential Pipeline (Assembly Line / Chained Agents with Real APIs)
==============================================================================

Architecture Overview:
----------------------
In a Sequential Pipeline (Assembly Line), work flows deterministically through a series
of specialized agents arranged in a linear sequence ($A \to B \to C \to D$).
Each agent acts as a specialized station on an automated conveyor belt:
  1. Stage 1 (SpecExtractor): Queries the live GitHub REST API for real repository releases or issues.
  2. Stage 2 (CurriculumArchitect / Categorizer): Groups raw changes into SemVer tiers (Major, Minor, Patch).
  3. Stage 3 (TutorialWriter / Drafter): Writes actionable, customer-facing release notes with code snippets.
  4. Stage 4 (EditorialReviewer): Performs rigorous Markdown syntax validation and quality audit.

Real-World Production Scenarios Demonstrated:
---------------------------------------------
- Example 1 (Automated GitHub Changelog & Release Notes):
  Ingests REAL live releases from 'pallets/flask' or 'openai/openai-agents-python' via GitHub REST API,
  categorizes commits/tags, drafts migration notes, and formats publication-ready docs.
- Example 2 (Live Open-Source Issue Triage & Advisory Pipeline):
  Ingests REAL open issues from 'astral-sh/uv', clusters high-priority bug reports,
  and drafts an engineering triage advisory.

Communication Topology:
-----------------------
    +-------------------------------------------------------+
    |                      Raw User Request                 |
    +-------------------------------------------------------+
                               |
                               v
                     +--------------------+
                     |  Stage 1: Extractor|  <-- Live GitHub REST API Tool
                     +--------------------+
                               | (Structured Payload)
                               v
                     +--------------------+
                     |  Stage 2: Outliner |  (SemVer Architectural Clustering)
                     +--------------------+
                               | (Categorized Outline)
                               v
                     +--------------------+
                     |  Stage 3: Drafter  |  (Customer Release Document)
                     +--------------------+
                               | (Draft Markdown)
                               v
                     +--------------------+
                     |  Stage 4: Editor   |  (Syntax & Editorial Polish)
                     +--------------------+
                               |
                               v
    +-------------------------------------------------------+
    |              Final Publication-Ready Doc              |
    +-------------------------------------------------------+

When to Use:
------------
- Content generation, software feature delivery, data extraction pipelines.
- Workflows requiring predictable, audited checkpoints between distinct lifecycle stages.
- When each stage requires very different prompt instructions (e.g. brainstorming vs. strict editing).

OpenAI Agents SDK Primitives:
-----------------------------
- Multiple distinct `Agent` instances with focused single-purpose instructions.
- Chained `Runner.run(...)` invocations where output of stage $N$ is passed as input to stage $N+1$.
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
    CommsTracer,
)

# -------------------------------------------------------------------------
# Real Public API Pipeline Ingestion Tools
# -------------------------------------------------------------------------

@function_tool
def fetch_github_releases(owner: str, repo: str) -> str:
    """Fetch REAL recent releases and tag changelogs from the GitHub REST API.

    Args:
        owner: GitHub org or username (e.g. 'pallets', 'openai', 'astral-sh').
        repo: Repository name (e.g. 'flask', 'openai-agents-python', 'uv').
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    params = {"per_page": 2}
    data = fetch_json(url, params=params)

    if isinstance(data, list) and len(data) > 0:
        releases = []
        for r in data[:2]:
            releases.append({
                "tag_name": r.get("tag_name"),
                "name": r.get("name"),
                "published_at": r.get("published_at"),
                "body_preview": (r.get("body") or "")[:400],
            })
        return json.dumps({"repository": f"{owner}/{repo}", "source": "GitHub Releases API", "releases": releases})

    # Fallback to repo tags if releases are empty
    tags_url = f"https://api.github.com/repos/{owner}/{repo}/tags"
    tags_data = fetch_json(tags_url, params={"per_page": 3})
    if isinstance(tags_data, list):
        return json.dumps({
            "repository": f"{owner}/{repo}",
            "source": "GitHub Tags API",
            "tags": [t.get("name") for t in tags_data[:3]],
        })

    return json.dumps({"error": "No releases or tags found", "repo": f"{owner}/{repo}"})


@function_tool
def fetch_github_issues(owner: str, repo: str) -> str:
    """Fetch REAL open bug reports and feature requests from the GitHub REST API.

    Args:
        owner: GitHub org or username (e.g. 'astral-sh', 'tiangolo').
        repo: Repository name (e.g. 'uv', 'fastapi').
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    params = {"state": "open", "per_page": 3}
    data = fetch_json(url, params=params)

    if isinstance(data, list):
        issues = [
            {
                "number": i.get("number"),
                "title": i.get("title"),
                "author": (i.get("user") or {}).get("login"),
                "labels": [l.get("name") for l in i.get("labels", [])],
                "created_at": i.get("created_at"),
            }
            for i in data
        ]
        return json.dumps({"repository": f"{owner}/{repo}", "source": "GitHub Issues API", "recent_issues": issues})

    return json.dumps({"error": "Unable to fetch issues", "repo": f"{owner}/{repo}"})


# -------------------------------------------------------------------------
# Define Specialized Pipeline Stage Agents
# -------------------------------------------------------------------------

spec_extractor = Agent(
    name="SpecExtractor",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Technical Specification & Release Extractor (Stage 1). "
        "When given a target repository, call `fetch_github_releases` or `fetch_github_issues` "
        "to pull REAL live data from GitHub. "
        "Extract the raw technical details: version numbers, timestamps, and core changes."
    ),
    tools=[fetch_github_releases, fetch_github_issues],
)

curriculum_architect = Agent(
    name="CurriculumArchitect",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an Architectural Release Categorizer (Stage 2). "
        "Take the raw repository changes and organize them into a clean SemVer structure:\n"
        "1. Breaking Changes (Major changes requiring developer migration)\n"
        "2. New Features & Improvements (Minor version enhancements)\n"
        "3. Bug Fixes & Security Patches (Patch level fixes)\n"
        "Ensure every item has an impact summary."
    ),
)

tutorial_writer = Agent(
    name="TutorialWriter",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Senior Technical Writer & Release Drafter (Stage 3). "
        "Take the structured categorization and draft an engaging, customer-ready release document. "
        "Include an executive summary, highlighted features, code upgrade snippets, and upgrade instructions."
    ),
)

editorial_reviewer = Agent(
    name="EditorialReviewer",
    model=DEFAULT_MODEL,
    instructions=(
        "You are the Principal Editorial Auditor (Stage 4). "
        "Review the draft release document for formatting precision, markdown syntax, clarity, and tone. "
        "Polish the markdown, add badges or callouts if helpful, and output the final publication-ready version."
    ),
)


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(query: str | None = None, example_id: int = 1, tracer: CommsTracer | None = None) -> str:
    """Execute Sequential Pipeline across 4 stages with real GitHub API ingestion."""
    ensure_api_key()

    if example_id == 2:
        default_query = (
            "Analyze recent open issues for 'astral-sh/uv' via GitHub API, "
            "categorize the developer pain points, and draft an issue triage report."
        )
        scenario_title = "Example 2: Astral uv Issue Triage & Engineering Digest"
    else:
        default_query = (
            "Generate official release documentation for the 'pallets/flask' repository. "
            "Fetch recent releases via GitHub API, categorize the changes, and draft polished release notes."
        )
        scenario_title = "Example 1: Flask Official GitHub Release Notes Pipeline"

    user_prompt = query or default_query

    print_header(
        "Pattern 05: Sequential Pipeline",
        f"4-Stage Assembly Line: {scenario_title}",
    )

    print_explainer(
        summary="A deterministic 4-stage assembly line ($A \\to B \\to C \\to D$). Stage 1 pulls live data from GitHub REST API, passing transformed context sequentially.",
        communication_mechanism="Chained Runner executions where each agent's output becomes the prompt for the next downstream station.",
        when_to_use=[
            "Deterministic multi-stage transformation workflows.",
            "Rigorous separation between research, drafting, and editorial review.",
            "Audit trails where each stage's intermediate output can be inspected or persisted.",
        ],
    )

    console.print(f"[bold cyan]Pipeline Input:[/bold cyan] {user_prompt}\n")

    if tracer is None:
        tracer = CommsTracer(scenario_title="Pattern 05: Sequential Pipeline")
    tracer.record_user_query(user_prompt, spec_extractor.name)

    # Stage 1: Extractor (queries real GitHub API)
    print_agent_step(spec_extractor.name, "Stage 1: Fetching and extracting live GitHub data...")
    res1 = await Runner.run(spec_extractor, user_prompt, hooks=tracer)
    output1 = str(res1.final_output)

    # Trace tools in Stage 1
    for item in res1.new_items:
        if getattr(item, "type", "") == "tool_call_item":
            raw = getattr(item, "raw_item", None)
            name = getattr(raw, "name", "tool")
            args = getattr(raw, "arguments", "{}")
            print_tool_call(name, args)

    console.print(f"  [dim green]Stage 1 Output:[/dim green] [dim]{output1[:120]}...[/dim]\n")

    # Stage 2: Categorizer / Architect
    tracer.record_packet(spec_extractor.name, curriculum_architect.name, "HANDOFF", "Forward structured API extraction to Architect", {"stage": 1})
    print_agent_step(curriculum_architect.name, "Stage 2: Structuring changes into SemVer hierarchy...")
    res2 = await Runner.run(
        curriculum_architect,
        f"Structure and categorize these extracted changes:\n\n{output1}",
        hooks=tracer,
    )
    output2 = str(res2.final_output)
    console.print(f"  [dim green]Stage 2 Output:[/dim green] [dim]{output2[:120]}...[/dim]\n")

    # Stage 3: Writer
    tracer.record_packet(curriculum_architect.name, tutorial_writer.name, "HANDOFF", "Forward SemVer architecture to Writer", {"stage": 2})
    print_agent_step(tutorial_writer.name, "Stage 3: Drafting customer-facing release notes...")
    res3 = await Runner.run(
        tutorial_writer,
        f"Draft comprehensive release documentation based on this structure:\n\n{output2}",
        hooks=tracer,
    )
    output3 = str(res3.final_output)
    console.print(f"  [dim green]Stage 3 Output:[/dim green] [dim]{output3[:120]}...[/dim]\n")

    # Stage 4: Editor
    tracer.record_packet(tutorial_writer.name, editorial_reviewer.name, "HANDOFF", "Forward draft release notes to Editor", {"stage": 3})
    print_agent_step(editorial_reviewer.name, "Stage 4: Polishing markdown and auditing publication rigor...")
    res4 = await Runner.run(
        editorial_reviewer,
        f"Perform final editorial review and polish for publication:\n\n{output3}",
        hooks=tracer,
    )
    final_output = str(res4.final_output)

    tracer.render_summary_ledger()
    tracer.render_sequence_diagram()

    print_result_panel("Final Publication-Ready Release Notes", final_output)
    return final_output


if __name__ == "__main__":
    asyncio.run(run())
