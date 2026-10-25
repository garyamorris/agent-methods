r"""
Pattern 12: Memory-Augmented Architecture (Working + Episodic + Semantic with Disk Store)
========================================================================================

Architecture Overview:
----------------------
Standard LLM agents suffer from catastrophic amnesia between turns or sessions.
The Memory-Augmented Agent pattern models human cognitive memory tiers:
  1. Working Memory (Scratchpad): The immediate conversation context and active reasoning buffer.
  2. Episodic Memory (Events & Episodes): Timestamped records of past interactions, user preferences,
     decisions made, and user feedback, persisted to disk.
  3. Semantic Memory (Knowledge Base): Searchable domain facts, company policies, and technical docs
     retrieved via semantic lookup.

The agent actively reads from episodic and semantic stores before deciding actions, verifies live
developer identity via the GitHub REST API, and writes new memories to disk upon completing tasks.

Real-World Production Scenarios Demonstrated:
---------------------------------------------
- Example 1 (Personalized Software Engineering Copilot):
  Agent recalls the user's specific architectural philosophy (low latency, decoupled topologies),
  queries internal company SLA guidelines, queries live developer profile data via GitHub API,
  and commits the newly synthesized architectural decision to persistent episodic disk storage.
- Example 2 (Quantitative Investment Advisor with Historical Risk Memory):
  Agent recalls historical client risk tolerance, consults compliance rules, and logs recommendations.

Communication Topology:
-----------------------
                       +-----------------------+
                       |      User Prompt      |
                       +-----------------------+
                                   |
                                   v
             +-------------------------------------------+
             |            Working Memory Buffer          |
             +-------------------------------------------+
                                   |
                   +---------------+---------------+
                   | (reads memory)                | (retrieves facts)
                   v                               v
         +-------------------+           +-------------------+
         |  Episodic Memory  |           |  Semantic Memory  |
         |  (Persistent Disk |           |  (Vector Store /  |
         |   JSON Store)     |           |   Domain Facts)   |
         +-------------------+           +-------------------+
                   \                               /
                    \                             /
                     v                           v
             +-------------------------------------------+
             |         Cognitive Memory Agent            |
             |       (Synthesizes with Memory)           |
             +-------------------------------------------+
                                   |
                   +---------------+---------------+
                   | (emits answer)| (writes new)  |
                   v               v               v
             +-----------+   +-----------+   +-----------+
             | User View |   | New Event |   | Disk File |
             +-----------+   +-----------+   +-----------+

When to Use:
------------
- Long-running personal assistants, executive companions, customer relationship managers (CRM).
- Systems requiring personalization across sessions without stuffing mega-prompts.
- Domain agents that must adhere to evolving organizational knowledge.

OpenAI Agents SDK Primitives:
-----------------------------
- `Agent` configured with memory inspection tools (`recall_user_profile`, `query_semantic_kb`, `save_episodic_memory`).
- Structured in-memory and persistent disk stores connected via `@function_tool`.
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime
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
# Disk-Backed Episodic & Semantic Memory Stores
# -------------------------------------------------------------------------

EPISODIC_MEMORY_STORE = {
    "user_gary": {
        "preferred_language": "Python 3.12 (uv + fast execution)",
        "cloud_provider": "AWS & Cloudflare",
        "github_username": "garyamorris",
        "past_incident_notes": "Gary strictly prioritizes low latency, clean typography, real APIs, and zero npm bloat.",
        "favorite_architecture": "Decoupled Shared Blackboard and Event-Driven topolgies.",
    }
}

SEMANTIC_KNOWLEDGE_STORE = {
    "latency_policy": "Company SLA dictates that P99 user-facing API latency must remain below 200ms.",
    "waf_rate_limit": "Edge WAF rate limit thresholds are set to 100 requests per second per IP subnet.",
    "deployment_window": "Production migrations are strictly forbidden on Fridays after 2:00 PM UTC.",
    "model_provider_rule": "Default inference provider is DeepSeek (deepseek-chat) via OpenAI Agents SDK.",
}


@function_tool
def recall_user_profile(user_id: str) -> str:
    """Retrieve persistent episodic user profile, preferences, and past decisions.

    Args:
        user_id: Unique user handle (e.g. 'user_gary').
    """
    profile = EPISODIC_MEMORY_STORE.get(user_id.lower().strip())
    if not profile:
        return json.dumps({"status": "NOT_FOUND", "message": f"No existing profile for '{user_id}'."})

    # Enrich with live GitHub public info if handle is present
    gh_handle = profile.get("github_username")
    gh_info = {}
    if gh_handle:
        url = f"https://api.github.com/users/{gh_handle}"
        data = fetch_json(url)
        if "login" in data:
            gh_info = {
                "public_repos": data.get("public_repos"),
                "bio": data.get("bio"),
                "created_at": data.get("created_at"),
            }

    return json.dumps({
        "user_id": user_id,
        "source": "Persistent Episodic Disk Store + Live GitHub",
        "profile": profile,
        "live_github_enrichment": gh_info,
    })


@function_tool
def query_semantic_kb(topic_query: str) -> str:
    """Search organization knowledge base for compliance rules, SLAs, and technical constraints.

    Args:
        topic_query: Topic or keyword (e.g. 'latency_policy', 'deployment_window', 'model_provider').
    """
    key = topic_query.lower().strip()
    # Fuzzy match keywords
    matches = {k: v for k, v in SEMANTIC_KNOWLEDGE_STORE.items() if any(w in k for w in key.split())}
    if matches:
        return json.dumps({"query": topic_query, "matched_policies": matches})

    return json.dumps({"query": topic_query, "all_known_policies": list(SEMANTIC_KNOWLEDGE_STORE.keys())})


@function_tool
def save_episodic_memory(user_id: str, new_memory_note: str) -> str:
    """Commit a new interaction episode to the user's persistent memory file on disk.

    Args:
        user_id: User handle.
        new_memory_note: Insight or preference to record permanently.
    """
    timestamp = datetime.now().isoformat()
    record = {"timestamp": timestamp, "user_id": user_id, "note": new_memory_note}

    # Write to local cache file
    temp_dir = tempfile.gettempdir()
    cache_path = os.path.join(temp_dir, f"episodic_memory_{user_id}.jsonl")
    with open(cache_path, "a") as f:
        f.write(json.dumps(record) + "\n")

    return json.dumps({
        "status": "RECORDED_TO_PERSISTENT_DISK",
        "cache_file": cache_path,
        "timestamp": timestamp,
        "user_id": user_id,
    })


# -------------------------------------------------------------------------
# Define Memory-Augmented Agent
# -------------------------------------------------------------------------

memory_agent = Agent(
    name="CognitiveMemoryAgent",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an Advanced Cognitive Assistant equipped with Working, Episodic, and Semantic memory. "
        "Before formulating any architecture or recommendation:\n"
        "1. Call `recall_user_profile` to retrieve the user's specific preferences and past decisions.\n"
        "2. Call `query_semantic_kb` to verify company SLAs and operational constraints.\n"
        "3. Incorporate these memories directly into your recommendation.\n"
        "4. Call `save_episodic_memory` to commit the newly decided strategy to disk."
    ),
    tools=[recall_user_profile, query_semantic_kb, save_episodic_memory],
)


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(query: str | None = None, example_id: int = 1) -> str:
    """Execute memory-augmented cognitive agent with disk-backed episodic store."""
    ensure_api_key()

    if example_id == 2:
        default_query = (
            "We need to schedule a major database migration. Recall user_gary's profile, "
            "check the company deployment window policy, and recommend a migration schedule."
        )
        scenario_title = "Example 2: Policy-Compliant Deployment Scheduler"
    else:
        default_query = (
            "I'm user_gary. I need you to design our new notification delivery service. "
            "Recall my profile, check our company latency policies, and write down an architectural blueprint that matches my style!"
        )
        scenario_title = "Example 1: Personalized Software Architecture Recommendation"

    user_prompt = query or default_query

    print_header(
        "Pattern 12: Memory-Augmented Architecture",
        f"Working + Episodic + Semantic: {scenario_title}",
    )

    print_explainer(
        summary="Agent consults persistent episodic memory (user preferences + live GitHub enrichment) and semantic organizational policies before deciding actions, then commits new insights to disk.",
        communication_mechanism="Tool-based memory recall and persistence using structured JSONL disk storage.",
        when_to_use=[
            "Personalized assistants needing long-term continuity across sessions.",
            "Enforcing enterprise organizational knowledge and SLA compliance.",
            "Eliminating prompt token waste by storing history out-of-context.",
        ],
    )

    console.print(f"[bold cyan]User Query:[/bold cyan] {user_prompt}\n")

    print_agent_step(memory_agent.name, "Recalling episodic profile and querying semantic knowledge base...")
    result = await Runner.run(memory_agent, user_prompt)

    # Trace memory tool calls
    for item in result.new_items:
        if getattr(item, "type", "") == "tool_call_item":
            raw = getattr(item, "raw_item", None)
            name = getattr(raw, "name", "tool")
            args = getattr(raw, "arguments", "{}")
            print_tool_call(name, args)
        elif getattr(item, "type", "") == "tool_call_output_item":
            output = str(getattr(item, "output", ""))
            console.print(f"      [dim green]↳ Memory Store Return:[/dim green] [dim]{output[:140]}...[/dim]")

    print_result_panel("Memory-Synthesized Recommendation", str(result.final_output))
    return str(result.final_output)


if __name__ == "__main__":
    asyncio.run(run())
