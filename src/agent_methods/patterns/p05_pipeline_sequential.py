"""
Pattern 05: Sequential Pipeline (Assembly Line / Chained Agents)
===============================================================

Architecture Overview:
----------------------
In a Sequential Pipeline (Assembly Line), work flows deterministically through a series
of specialized agents arranged in a linear sequence ($A \to B \to C \to D$).
Each agent acts as a specialized station on a conveyor belt:
  1. Agent A takes raw unstructured input and extracts key entities / specs.
  2. Agent B takes Agent A's output and designs a blueprint/outline.
  3. Agent C takes Agent B's blueprint and drafts the complete implementation/content.
  4. Agent D takes Agent C's draft and performs rigorous quality review & editing.

Communication Topology:
-----------------------
    +-------------------------------------------------------+
    |                      Raw User Request                 |
    +-------------------------------------------------------+
                               |
                               v
                     +--------------------+
                     |  Stage 1: Extractor|  (Theme & Audience Specs)
                     +--------------------+
                               |
                               v
                     +--------------------+
                     |  Stage 2: Outliner |  (Structured Technical Outline)
                     +--------------------+
                               |
                               v
                     +--------------------+
                     |  Stage 3: Drafter  |  (Full Draft Implementation)
                     +--------------------+
                               |
                               v
                     +--------------------+
                     |  Stage 4: Editor   |  (Polished Publication Ready)
                     +--------------------+
                               |
                               v
    +-------------------------------------------------------+
    |                    Final Publication                  |
    +-------------------------------------------------------+

When to Use:
------------
- Content generation, software feature delivery, data extraction pipelines.
- Workflows requiring predictable, audited checkpoints between distinct lifecycle stages.
- When each stage requires very different prompt instructions (e.g. brainstorming vs. strict editing).

OpenAI Agents SDK Primitives:
-----------------------------
- Multiple distinct `Agent` instances with focused single-purpose instructions.
- Chained `Runner.run(...)` invocations where output of stage $N$ is formatted into input for stage $N+1$.
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
# Define Specialized Pipeline Stage Agents
# -------------------------------------------------------------------------

spec_extractor = Agent(
    name="SpecExtractor",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Technical Specification Extractor. "
        "Analyze the user's raw topic or problem statement. "
        "Extract:\n"
        "1. Core Objective & Scope\n"
        "2. Target Developer Persona (Junior, Mid, Staff)\n"
        "3. Key Technical Requirements / Constraints\n"
        "Keep your output structured, concise, and focused."
    ),
)

curriculum_architect = Agent(
    name="CurriculumArchitect",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Technical Curriculum Architect. "
        "Based on the extracted specifications, create a logical, step-by-step tutorial outline. "
        "Include section titles, key concepts taught in each section, and clear progression."
    ),
)

tutorial_writer = Agent(
    name="TutorialWriter",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an engaging Technical Author. "
        "Take the provided outline and write a concise, hands-on educational guide. "
        "Include clear explanations, code blocks, and best practice callouts."
    ),
)

editorial_reviewer = Agent(
    name="EditorialReviewer",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Senior Technical Editor. "
        "Review the draft for technical rigor, readability, and formatting. "
        "Polish the markdown, fix any inconsistencies, and produce the final publication-ready version."
    ),
)


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(topic: str | None = None) -> str:
    """Execute sequential pipeline passing outputs through stages."""
    ensure_api_key()

    default_topic = "Building Event-Driven Microservices with Redis Streams and Python"
    raw_input = topic or default_topic

    print_header(
        "Pattern 05: Sequential Pipeline",
        "Deterministic linear assembly line with stage-by-stage transformations",
    )

    print_explainer(
        summary="A linear chain of specialized agents where each agent transforms the previous agent's output.",
        communication_mechanism="Explicit output-to-input handoff across discrete Runner invocations.",
        when_to_use=[
            "Content publishing, code generation, and ETL data transformation pipelines.",
            "Workflows requiring strict quality checkpoints and stage-by-stage verification.",
            "Tasks where dividing responsibilities into distinct phases drastically improves prompt adherence.",
        ],
    )

    console.print(f"[bold cyan]Initial Input:[/bold cyan] {raw_input}\n")

    # Stage 1: Extract Specs
    print_agent_step("Stage 1/4: SpecExtractor", "Extracting technical constraints and developer persona...")
    res_specs = await Runner.run(spec_extractor, raw_input)
    specs_output = str(res_specs.final_output)

    # Stage 2: Create Outline
    print_agent_step("Stage 2/4: CurriculumArchitect", "Designing structural outline from specifications...")
    res_outline = await Runner.run(
        curriculum_architect,
        f"Design an outline based on these specifications:\n\n{specs_output}"
    )
    outline_output = str(res_outline.final_output)

    # Stage 3: Write Draft
    print_agent_step("Stage 3/4: TutorialWriter", "Drafting tutorial sections and code examples...")
    res_draft = await Runner.run(
        tutorial_writer,
        f"Write the tutorial following this outline:\n\n{outline_output}"
    )
    draft_output = str(res_draft.final_output)

    # Stage 4: Polish & Edit
    print_agent_step("Stage 4/4: EditorialReviewer", "Applying final editorial polish and formatting...")
    res_final = await Runner.run(
        editorial_reviewer,
        f"Review and polish this tutorial draft for publication:\n\n{draft_output}"
    )
    final_output = str(res_final.final_output)

    print_result_panel("Final Published Article (from EditorialReviewer)", final_output)
    return final_output


if __name__ == "__main__":
    asyncio.run(run())
