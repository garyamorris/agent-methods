r"""
Pattern 08: Multi-Agent Debate & Deliberation (Adversarial Roundtable)
======================================================================

Architecture Overview:
----------------------
Single-agent reasoning often suffers from confirmation bias, sycophancy, or bland neutrality
on complex architectural dilemmas. The Multi-Agent Debate pattern pits two or more agents
with diametrically opposing perspectives against one another in structured deliberation:
  1. Opening Statements: Advocate A and Advocate B independently present their strongest cases.
  2. Cross-Examination & Rebuttal: Each advocate is given the other's transcript to critique
     flaws, hidden risks, and unstated assumptions.
  3. Adjudication & Consensus: An impartial Moderator/Judge evaluates both sides' rigor,
     discounts fallacies, and delivers a balanced, nuanced synthesis with a conditional recommendation.

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
    |   Advocate A    |                         |   Advocate B    |
    | (Pro-Monolith)  |                         | (Microservices) |
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
- Policy evaluation, legal briefs, and investment thesis stress-testing.

OpenAI Agents SDK Primitives:
-----------------------------
- Multiple `Agent` instances parameterized with contrasting personas and strict instructions.
- Controlled conversational turn passing through `Runner.run`.
- Impartial synthesis agent acting as the jury/moderator.
"""

import asyncio
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
# Define Debater and Judge Agents
# -------------------------------------------------------------------------

advocate_monolith = Agent(
    name="AdvocateModularMonolith",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an elite Principal Systems Architect championing Modular Monoliths. "
        "Argue vigorously why modular monoliths maximize developer velocity, reduce operational complexity, "
        "simplify transactional integrity (ACID), and prevent distributed systems overhead for early-to-mid stage companies. "
        "Be sharp, fact-based, and compelling."
    ),
)

advocate_microservices = Agent(
    name="AdvocateMicroservices",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Cloud-Native Distributed Systems Fellow championing Microservices. "
        "Argue vigorously why decoupled microservices are essential for independent deployability, "
        "fault isolation, granular auto-scaling, polyglot technology stacks, and enterprise organizational scaling (Conway's Law). "
        "Be sharp, fact-based, and compelling."
    ),
)

judge_moderator = Agent(
    name="JudicialModerator",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a neutral Chief Technology Officer and Supreme Arbiter. "
        "You have observed a rigorous debate between AdvocateModularMonolith and AdvocateMicroservices. "
        "Evaluate the merits and rebuttals of both arguments.\n"
        "1. Identify the strongest points conceded or made by each side.\n"
        "2. Identify flaws or unrealistic assumptions in each position.\n"
        "3. Provide a definitive, situational verdict: when to choose Option A vs Option B based on team size, "
        "revenue, latency, and business maturity."
    ),
)


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(topic: str | None = None) -> str:
    """Execute multi-round debate with rebuttals and impartial verdict."""
    ensure_api_key()

    default_topic = (
        "Should a 15-person engineering startup building an AI-powered SaaS product "
        "start with a Modular Monolith or a Distributed Microservices architecture?"
    )
    dilemma = topic or default_topic

    print_header(
        "Pattern 08: Multi-Agent Debate & Deliberation",
        "Adversarial multi-turn deliberation mitigating biases through structured rebuttal",
    )

    print_explainer(
        summary="Competing agents argue contrasting theses across rounds, followed by an impartial judge synthesizing consensus.",
        communication_mechanism="Turn-based multi-party dialogue where agents consume and challenge prior transcripts.",
        when_to_use=[
            "High-stakes architectural, financial, or strategic decisions.",
            "Surfacing hidden failure modes that a single agreeable agent would miss.",
            "Nuanced technical evaluations where trade-offs depend heavily on context.",
        ],
    )

    console.print(f"[bold cyan]Debate Dilemma:[/bold cyan] {dilemma}\n")

    # Round 1: Opening Arguments
    print_agent_step("Round 1", "AdvocateModularMonolith delivering opening statement...", style="cyan")
    res_mono_open = await Runner.run(
        advocate_monolith,
        f"Present your opening argument on this topic:\n{dilemma}"
    )
    mono_opening = str(res_mono_open.final_output)

    print_agent_step("Round 1", "AdvocateMicroservices delivering opening statement...", style="magenta")
    res_micro_open = await Runner.run(
        advocate_microservices,
        f"Present your opening argument on this topic:\n{dilemma}"
    )
    micro_opening = str(res_micro_open.final_output)

    # Round 2: Rebuttals
    print_agent_step("Round 2", "AdvocateModularMonolith rebutting microservices claims...", style="cyan")
    res_mono_rebuttal = await Runner.run(
        advocate_monolith,
        f"DILEMMA: {dilemma}\n\n"
        f"YOUR OPPONENT ARGUED:\n{micro_opening}\n\n"
        f"Deliver a targeted rebuttal exposing the operational traps and overhead in their argument."
    )
    mono_rebuttal = str(res_mono_rebuttal.final_output)

    print_agent_step("Round 2", "AdvocateMicroservices rebutting modular monolith claims...", style="magenta")
    res_micro_rebuttal = await Runner.run(
        advocate_microservices,
        f"DILEMMA: {dilemma}\n\n"
        f"YOUR OPPONENT ARGUED:\n{mono_opening}\n\n"
        f"Deliver a targeted rebuttal exposing the scaling and organizational bottlenecks in their argument."
    )
    micro_rebuttal = str(res_micro_rebuttal.final_output)

    # Round 3: Judicial Adjudication
    print_agent_step("JudicialModerator", "Deliberating on arguments and drafting synthesis verdict...", style="bold yellow")
    docket = (
        f"DEBATE TOPIC:\n{dilemma}\n\n"
        f"=== ADVOCATE MODULAR MONOLITH OPENING ===\n{mono_opening}\n\n"
        f"=== ADVOCATE MICROSERVICES OPENING ===\n{micro_opening}\n\n"
        f"=== ADVOCATE MODULAR MONOLITH REBUTTAL ===\n{mono_rebuttal}\n\n"
        f"=== ADVOCATE MICROSERVICES REBUTTAL ===\n{micro_rebuttal}"
    )

    verdict_res = await Runner.run(judge_moderator, docket)
    verdict = str(verdict_res.final_output)

    print_result_panel("CTO Consensus & Judicial Verdict", verdict)
    return verdict


if __name__ == "__main__":
    asyncio.run(run())
