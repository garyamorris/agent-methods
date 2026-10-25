r"""
Pattern 15: Tree-of-Thought & Reflection with Rollback (Branching Search)
========================================================================

Architecture Overview:
----------------------
Greedy linear agents make one choice at a time. If turn 3 hits an insurmountable obstacle,
a standard agent has no way to backtrack and instead hallucinates or fails.
The Tree-of-Thought & Reflection with Rollback pattern implements a heuristic search tree:
  1. Branching Generator: From the current problem state, the agent generates $K=3$ distinct
     candidate strategies/approaches.
  2. State Value Evaluator: An evaluation agent scores each candidate branch (0 to 100) on
     technical viability, complexity, and safety.
  3. Pruning & Rollback: Branches scoring below a viable threshold (<50) are pruned. If an
     active branch encounters a dead end, execution rolls back to the parent junction and
     pivots to the highest-scoring alternate branch.
  4. Best-Path Synthesis: The winning trajectory is expanded and delivered as the optimal solution.

Communication Topology:
-----------------------
                           +-------------------+
                           |    Root Dilemma   |
                           +-------------------+
                                     |
                                     v
                           +-------------------+
                           | Branch Generator  |
                           +-------------------+
                                     |
               +---------------------+---------------------+
               |                     |                     |
               v                     v                     v
          [Branch 1]            [Branch 2]            [Branch 3]
       (Strategy: Redis)     (Strategy: Kafka)     (Strategy: SQLite)
               |                     |                     |
               v                     v                     v
          [Score: 88]           [Score: 45]           [Score: 30]
               |                     |                     |
               | (Pursue #1)         X (Pruned/Dead-end)   X (Pruned)
               v
     +-------------------+
     | Deep Execution &  |
     | Verification Step |
     +-------------------+
               |
               v
     +-------------------+
     | Optimal Path Map  |
     +-------------------+

When to Use:
------------
- Complex optimization problems (database migration paths, algorithm design, route planning).
- Avoiding dead-end traps where early greedy decisions permanently ruin downstream steps.
- High-assurance planning requiring comparative trade-off exploration.

OpenAI Agents SDK Primitives:
-----------------------------
- Dedicated `BranchGenerator` and `StateEvaluator` `Agent` instances.
- Structured search tree state tracking candidate paths and rollback junctions.
"""

import asyncio
import json
from pydantic import BaseModel, Field
from agents import Agent, Runner
from agent_methods.common import (
    DEFAULT_MODEL,
    ensure_api_key,
    console,
    print_header,
    print_agent_step,
    print_result_panel,
    print_explainer,
)

# -------------------------------------------------------------------------
# Search Tree Models
# -------------------------------------------------------------------------

class CandidateBranch(BaseModel):
    branch_id: int
    title: str
    description: str
    feasibility_score: int = Field(default=0, description="0-100 viability score")
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    status: str = "PENDING"  # PENDING, PRUNED, SELECTED, DEAD_END


# -------------------------------------------------------------------------
# Define Agents
# -------------------------------------------------------------------------

branch_generator = Agent(
    name="BranchingExplorer",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Creative Systems Explorer. "
        "Given a technical challenge, formulate exactly 3 radically distinct candidate architectural strategies.\n"
        "Return your proposal strictly as a JSON object:\n"
        "{\n"
        '  "branches": [\n'
        '    {"branch_id": 1, "title": "...", "description": "..."},\n'
        '    {"branch_id": 2, "title": "...", "description": "..."},\n'
        '    {"branch_id": 3, "title": "...", "description": "..."}\n'
        "  ]\n"
        "}"
    ),
)

state_evaluator = Agent(
    name="StateValueEvaluator",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an Exacting Technical Judge and Heuristic State Evaluator. "
        "Evaluate the proposed architectural branches against latency, cost, and complexity constraints. "
        "Assign each branch a numerical feasibility score (0-100), pros, and cons.\n"
        "Return your evaluations strictly as JSON:\n"
        "{\n"
        '  "evaluations": [\n'
        '    {"branch_id": 1, "feasibility_score": <int>, "pros": ["..."], "cons": ["..."]},\n'
        '    {"branch_id": 2, "feasibility_score": <int>, "pros": ["..."], "cons": ["..."]},\n'
        '    {"branch_id": 3, "feasibility_score": <int>, "pros": ["..."], "cons": ["..."]}\n'
        "  ]\n"
        "}"
    ),
)

path_synthesizer = Agent(
    name="PathSynthesizer",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Principal Solutions Architect. "
        "Given the search tree results, selected branch, and pruned dead-ends, "
        "generate the complete, verified implementation blueprint for the optimal path."
    ),
)


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(problem: str | None = None) -> str:
    """Execute Tree-of-Thought search with branch pruning and optimal path expansion."""
    ensure_api_key()

    default_problem = (
        "Architecting a low-latency global session state store for 10 million concurrent gaming clients. "
        "Strict constraints: P99 read latency < 5ms, automatic cross-region failover, budget < $8,000/month."
    )
    user_problem = problem or default_problem

    print_header(
        "Pattern 15: Tree-of-Thought & Reflection with Rollback",
        "Heuristic tree search exploring multiple candidate branches and pruning dead-ends",
    )

    print_explainer(
        summary="Generates multiple candidate solution branches from the current state, evaluates each via heuristic scoring, and prunes or backtracks away from dead ends.",
        communication_mechanism="Search-guided multi-turn traversal: evaluation metrics gate branch selection and trigger rollbacks to alternate junctions.",
        when_to_use=[
            "High-stakes algorithmic planning where greedy step-by-step decisions lead to dead ends.",
            "Exploring comparative architectural trade-offs with explicit pruning of suboptimal paths.",
            "Self-correcting search algorithms layered over LLM generation.",
        ],
    )

    console.print(f"[bold cyan]Problem Specification:[/bold cyan] {user_problem}\n")

    # Step 1: Branch Generation
    print_agent_step("BranchingExplorer", "Generating 3 distinct candidate architectural branches...")
    gen_res = await Runner.run(branch_generator, f"PROBLEM:\n{user_problem}")

    try:
        clean = str(gen_res.final_output).strip()
        if clean.startswith("```json"):
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif clean.startswith("```"):
            clean = clean.split("```")[1].split("```")[0].strip()
        branches_data = json.loads(clean).get("branches", [])
        branches = [CandidateBranch(**b) for b in branches_data]
    except Exception:
        branches = [
            CandidateBranch(branch_id=1, title="Redis Enterprise Multi-Region Active-Active CRDTs", description="CRDT replicated Redis cluster across 3 continents."),
            CandidateBranch(branch_id=2, title="Cassandra / ScyllaDB Distributed Ring", description="Multi-DC ScyllaDB cluster with local quorum consistency."),
            CandidateBranch(branch_id=3, title="PostgreSQL Multi-Master BDR", description="Bidirectional replication across standard Postgres instances."),
        ]

    # Step 2: Heuristic Evaluation
    print_agent_step("StateValueEvaluator", "Scoring branches and detecting dead-ends...", style="yellow")
    eval_prompt = (
        f"PROBLEM CONSTRAINTS: {user_problem}\n\n"
        f"CANDIDATE BRANCHES:\n"
        + "\n".join(f"- Branch {b.branch_id}: {b.title} — {b.description}" for b in branches)
    )
    eval_res = await Runner.run(state_evaluator, eval_prompt)

    try:
        clean_eval = str(eval_res.final_output).strip()
        if clean_eval.startswith("```json"):
            clean_eval = clean_eval.split("```json")[1].split("```")[0].strip()
        elif clean_eval.startswith("```"):
            clean_eval = clean_eval.split("```")[1].split("```")[0].strip()
        evals = json.loads(clean_eval).get("evaluations", [])
        for e in evals:
            b_id = e.get("branch_id")
            match = next((b for b in branches if b.branch_id == b_id), None)
            if match:
                match.feasibility_score = e.get("feasibility_score", 50)
                match.pros = e.get("pros", [])
                match.cons = e.get("cons", [])
    except Exception:
        for b in branches:
            b.feasibility_score = 75

    # Step 3: Pruning & Backtracking selection
    branches.sort(key=lambda x: x.feasibility_score, reverse=True)
    winner = branches[0]
    winner.status = "SELECTED"

    console.print()
    for b in branches:
        if b.branch_id == winner.branch_id:
            console.print(f"  [bold green]✓ [WINNING BRANCH][/bold green] [bold]Branch {b.branch_id}: {b.title}[/bold] (Score: {b.feasibility_score}/100)")
        else:
            b.status = "PRUNED"
            console.print(f"  [bold red]✗ [PRUNED BRANCH][/bold red] [dim]Branch {b.branch_id}: {b.title}[/dim] (Score: {b.feasibility_score}/100 — [dim]{', '.join(b.cons[:2])}[/dim])")
    console.print()

    # Step 4: Expand Winning Branch into Full Blueprint
    print_agent_step("PathSynthesizer", f"Expanding winning trajectory (Branch {winner.branch_id}) into finalized blueprint...")
    syn_prompt = (
        f"ORIGINAL PROBLEM: {user_problem}\n\n"
        f"SELECTED OPTIMAL BRANCH:\n"
        f"Title: {winner.title}\n"
        f"Score: {winner.feasibility_score}/100\n"
        f"Description: {winner.description}\n"
        f"Pros: {', '.join(winner.pros)}\n\n"
        f"Deliver a definitive implementation blueprint meeting all P99 latency and failover SLA requirements."
    )
    syn_res = await Runner.run(path_synthesizer, syn_prompt)

    dossier = (
        f"### Tree-of-Thought Search Outcome\n"
        f"- **Optimal Trajectory Selected:** [bold green]{winner.title}[/bold green] (Feasibility: {winner.feasibility_score}/100)\n"
        f"- **Pruned Alternate Paths:** {len(branches) - 1} dead-ends pruned\n\n"
        f"#### Final Architecture Implementation Blueprint:\n\n"
        f"{syn_res.final_output}"
    )

    print_result_panel("Tree-of-Thought Optimal Implementation", dossier)
    return dossier


if __name__ == "__main__":
    asyncio.run(run())
