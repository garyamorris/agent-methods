r"""
Pattern 12: Memory-Augmented Architecture (Working + Episodic + Semantic)
=========================================================================

Architecture Overview:
----------------------
Standard LLM agents suffer from catastrophic amnesia between turns or sessions.
The Memory-Augmented Agent pattern models human cognitive memory tiers:
  1. Working Memory (Scratchpad): The immediate conversation context and active reasoning buffer.
  2. Episodic Memory (Events & Episodes): Timestamped records of past interactions, user preferences,
     decisions made, and user feedback.
  3. Semantic Memory (Knowledge Base): Searchable domain facts, company policies, and technical docs
     retrieved via semantic lookup.

The agent actively reads from episodic/semantic memory before deciding actions, and writes
new memories to disk/store upon completing tasks.

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
         |  (User Profiles   |           |  (Vector Store /  |
         |   & Past Events)  |           |   Domain Facts)   |
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
             | User View |   | New Event |   | New Fact  |
             +-----------+   +-----------+   +-----------+

When to Use:
------------
- Long-running personal assistants, executive companions, customer relationship managers (CRM).
- Systems requiring personalization across sessions without stuffing mega-prompts.
- Domain agents that must adhere to evolving organizational knowledge.

OpenAI Agents SDK Primitives:
-----------------------------
- `Agent` configured with memory inspection tools (`recall_user_profile`, `query_semantic_kb`, `save_episodic_memory`).
- Structured in-memory / persistent memory stores connected via `@function_tool`.
"""

import asyncio
import json
from datetime import datetime
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
# Simulated Episodic & Semantic Memory Stores
# -------------------------------------------------------------------------

EPISODIC_MEMORY_STORE = {
    "user_gary": {
        "preferred_language": "Python 3.12",
        "cloud_provider": "AWS & Cloudflare",
        "past_incident_notes": "Gary strictly prioritizes low latency, clean typography, and zero npm build bloat.",
        "favorite_architecture": "Decoupled Shared Blackboard and Event-Driven topolgies.",
    }
}

SEMANTIC_KNOWLEDGE_STORE = {
    "latency_policy": "Company SLA dictates that P99 user-facing API latency must remain below 200ms.",
    "waf_rate_limit": "Edge WAF rate limit thresholds are set to 100 requests per second per IP subnet.",
    "deployment_window": "Production migrations are strictly forbidden on Fridays after 2:00 PM UTC.",
}


@function_tool
def recall_user_profile(user_id: str) -> str:
    """Retrieve episodic memories, preferences, and past interaction history for a user.

    Args:
        user_id: Identifier of the user (e.g. 'user_gary').
    """
    profile = EPISODIC_MEMORY_STORE.get(user_id, {})
    return json.dumps({"user_id": user_id, "memory_type": "episodic", "profile": profile})


@function_tool
def query_semantic_knowledge(topic: str) -> str:
    """Search semantic memory and organizational knowledge base.

    Args:
        topic: Search query or keyword (e.g. 'latency_policy', 'deployment_window').
    """
    matches = {k: v for k, v in SEMANTIC_KNOWLEDGE_STORE.items() if any(word in k or word in v.lower() for word in topic.lower().split())}
    if not matches:
        matches = {"general": "Standard operational procedures apply."}
    return json.dumps({"query": topic, "memory_type": "semantic", "results": matches})


@function_tool
def save_episodic_memory(user_id: str, new_fact: str) -> str:
    """Commit a new episodic memory to the persistent store.

    Args:
        user_id: Identifier of the user.
        new_fact: The new fact or preference to persist.
    """
    if user_id not in EPISODIC_MEMORY_STORE:
        EPISODIC_MEMORY_STORE[user_id] = {}
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    EPISODIC_MEMORY_STORE[user_id][f"fact_{timestamp}"] = new_fact
    return json.dumps({"status": "SAVED", "user_id": user_id, "committed_fact": new_fact})


# -------------------------------------------------------------------------
# Define Memory-Augmented Agent
# -------------------------------------------------------------------------

memory_agent = Agent(
    name="CognitiveMemoryAssistant",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an Intelligent Cognitive Companion equipped with Multi-Tier Memory. "
        "Before answering user inquiries:\n"
        "1. Use `recall_user_profile` to remember the user's specific preferences, background, and history.\n"
        "2. Use `query_semantic_knowledge` to check organizational policies or technical requirements.\n"
        "3. Synthesize your answer tailoring it to their exact profile.\n"
        "4. If the user shares new personal preferences or rules, call `save_episodic_memory` to commit them."
    ),
    tools=[recall_user_profile, query_semantic_knowledge, save_episodic_memory],
)


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(query: str | None = None) -> str:
    """Execute memory-augmented agent querying episodic and semantic stores."""
    ensure_api_key()

    default_query = (
        "Hi, I'm user_gary. We're planning to migrate our payment webhook handler this Friday at 4:00 PM UTC. "
        "Based on my personal technical preferences and our company policies, evaluate this plan and advise me!"
    )
    user_prompt = query or default_query

    print_header(
        "Pattern 12: Memory-Augmented Architecture",
        "Multi-tier cognitive memory uniting working, episodic, and semantic knowledge stores",
    )

    print_explainer(
        summary="An agent queries separate episodic (user history) and semantic (policy/facts) memory stores to personalize and ground its reasoning.",
        communication_mechanism="In-context memory tool retrieval: explicit queries enrich the working memory buffer with persistent state.",
        when_to_use=[
            "Personalized executive assistants and long-term customer relationships.",
            "Enterprise compliance where organizational rules change dynamically.",
            "Eliminating catastrophic session amnesia without stuffing the initial prompt.",
        ],
    )

    console.print(f"[bold cyan]User Query:[/bold cyan] {user_prompt}\n")

    print_agent_step("CognitiveMemoryAssistant", "Querying episodic profile and semantic policies...")
    result = await Runner.run(memory_agent, user_prompt)

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

    print_result_panel("Personalized Memory-Grounded Advisory", str(result.final_output))
    return str(result.final_output)


if __name__ == "__main__":
    asyncio.run(run())
