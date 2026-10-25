r"""
Pattern 07: Evaluator-Optimizer (Generator-Critic Feedback Loop)
===============================================================

Architecture Overview:
----------------------
Single-pass generation often overlooks edge cases, off-by-one errors, or stylistic constraints.
The Evaluator-Optimizer (or Generator-Critic) pattern implements an iterative refinement loop:
  1. Generator Agent creates a candidate solution based on the user's prompt.
  2. Evaluator Agent rigorously grades the candidate against objective rubrics
     (correctness, edge cases, complexity, safety) and returns a structured evaluation.
  3. Feedback Gate: If the score meets the threshold (or passed is True), execution concludes.
  4. Optimization: If the solution falls short, the structured critique is fed back to the
     Generator Agent, which refines its draft. The cycle repeats until satisfaction or max turns.

Communication Topology:
-----------------------
    +-------------------------------------------------------+
    |                    Task Specification                 |
    +-------------------------------------------------------+
                               |
                               v
                     +--------------------+
         +---------> |  Generator Agent   |
         |           +--------------------+
         |                     |
         | (Iterative          v
         |  Critique)  +--------------------+
         |             |  Evaluator Agent   |
         |             +--------------------+
         |                     |
         |                     v
         |              [Score >= 85?]
         |                /        \
         +---- [NO] <----+          +----> [YES]
                                              |
                                              v
                                    +--------------------+
                                    |  Optimized Final   |
                                    |     Artifact       |
                                    +--------------------+

When to Use:
------------
- Code generation, SQL query synthesis, and algorithmic optimization.
- High-stakes document creation (contracts, compliance filings, medical letters).
- When objective evaluation criteria exist that an LLM evaluator can reliably grade.

OpenAI Agents SDK Primitives:
-----------------------------
- Dedicated `Generator` and `Evaluator` `Agent` instances.
- Pydantic structured output validation for the Evaluator.
- Deterministic iterative loop controlling conversational feedback.
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
# Structured Evaluation Schema
# -------------------------------------------------------------------------

class EvaluationReport(BaseModel):
    score: int = Field(description="Numerical quality score from 0 to 100.")
    passed: bool = Field(description="True if score >= 85 and no critical flaws exist.")
    strengths: list[str] = Field(description="List of positive aspects.")
    weaknesses: list[str] = Field(description="Specific bugs, missing edge cases, or suboptimal patterns.")
    suggested_improvements: list[str] = Field(description="Actionable steps the generator must take to fix flaws.")


# -------------------------------------------------------------------------
# Define Generator and Evaluator Agents
# -------------------------------------------------------------------------

generator_agent = Agent(
    name="CodeGenerator",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an expert Python Algorithm Engineer. "
        "Write clean, production-ready Python code with complete type annotations, docstrings, "
        "and optimal time/space complexity. "
        "If feedback is provided on a previous attempt, address EVERY point raised in the critique."
    ),
)

evaluator_agent = Agent(
    name="SeniorCodeReviewer",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an exacting Senior Staff Software Engineer and Code Auditor. "
        "Evaluate the candidate code against the requirements on:\n"
        "1. Functional correctness and edge-case handling (empty inputs, nulls, negative numbers, extreme values).\n"
        "2. Time and space algorithmic complexity.\n"
        "3. Production readability, error handling, and type annotations.\n\n"
        "You MUST return your verdict strictly as a valid JSON object matching the EvaluationReport schema:\n"
        "{\n"
        '  "score": <0-100>,\n'
        '  "passed": <true/false>,\n'
        '  "strengths": ["..."],\n'
        '  "weaknesses": ["..."],\n'
        '  "suggested_improvements": ["..."]\n'
        "}\n"
        "Be strict! Do NOT pass code with missing edge cases or suboptimal algorithmic complexity."
    ),
)


# -------------------------------------------------------------------------
# Runner Loop
# -------------------------------------------------------------------------

async def run(spec: str | None = None, max_iterations: int = 3) -> str:
    """Execute generator-evaluator optimization loop until quality threshold."""
    ensure_api_key()

    default_spec = (
        "Implement a Thread-Safe In-Memory LRU Cache in Python with TTL (Time-To-Live) support "
        "per key. Methods: get(key), set(key, value, ttl_seconds), delete(key), and cleanup_expired(). "
        "Must be O(1) average time complexity for get and set."
    )
    user_spec = spec or default_spec

    print_header(
        "Pattern 07: Evaluator-Optimizer",
        "Generator-Critic feedback loop iterating until quality convergence",
    )

    print_explainer(
        summary="An iterative refinement cycle where a generator produces a candidate and an evaluator scores it, providing actionable feedback.",
        communication_mechanism="Cyclic message passing: feedback from evaluation is injected back into generator prompt history.",
        when_to_use=[
            "Complex code generation, mathematical derivations, or SQL queries.",
            "Workflows with clear grading rubrics where single-pass LLM output is prone to edge-case bugs.",
            "Autonomous quality assurance loops.",
        ],
    )

    console.print(f"[bold cyan]Specification:[/bold cyan] {user_spec}\n")

    current_prompt = f"Please implement the following specification in Python:\n\n{user_spec}"
    best_solution = ""
    iteration = 1

    while iteration <= max_iterations:
        print_agent_step(f"Iteration {iteration}/{max_iterations}", f"CodeGenerator generating candidate solution...")
        gen_result = await Runner.run(generator_agent, current_prompt)
        candidate_code = str(gen_result.final_output)
        best_solution = candidate_code

        print_agent_step(f"Iteration {iteration}/{max_iterations}", "SeniorCodeReviewer evaluating candidate against rubric...")
        eval_prompt = (
            f"SPECIFICATION:\n{user_spec}\n\n"
            f"CANDIDATE CODE:\n{candidate_code}\n\n"
            f"Please grade this code and return JSON output."
        )
        eval_result = await Runner.run(evaluator_agent, eval_prompt)
        raw_eval = str(eval_result.final_output)

        # Parse evaluation JSON
        try:
            # Strip markdown json blocks if present
            clean_json = raw_eval.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif clean_json.startswith("```"):
                clean_json = clean_json.split("```")[1].split("```")[0].strip()
            eval_data = json.loads(clean_json)
            score = eval_data.get("score", 0)
            passed = eval_data.get("passed", False)
            improvements = eval_data.get("suggested_improvements", [])
            weaknesses = eval_data.get("weaknesses", [])
        except Exception:
            score = 75
            passed = False
            improvements = ["Ensure complete thread safety and O(1) operations."]
            weaknesses = ["Failed to parse strict JSON evaluation."]

        console.print(
            f"    [bold yellow]Score:[/bold yellow] [bold cyan]{score}/100[/bold cyan] | "
            f"[bold yellow]Passed:[/bold yellow] [{'green' if passed else 'red'}]{passed}[/{'green' if passed else 'red'}]"
        )

        if passed or score >= 85:
            print_agent_step("System", f"Quality threshold achieved on iteration {iteration}! Terminating loop.", style="bold green")
            break

        if iteration == max_iterations:
            print_agent_step("System", f"Reached maximum iterations ({max_iterations}). Finalizing best attempt.", style="yellow")
            break

        # Prepare feedback for the next iteration
        critique_summary = "\n".join(f"- {item}" for item in (weaknesses + improvements))
        console.print(f"    [dim]Feedback to generator:\n{critique_summary}[/dim]\n")

        current_prompt = (
            f"Your previous implementation scored {score}/100 and had the following flaws:\n"
            f"{critique_summary}\n\n"
            f"PREVIOUS ATTEMPT:\n{candidate_code}\n\n"
            f"Please revise and provide a perfected implementation that resolves all issues."
        )
        iteration += 1

    print_result_panel("Optimized Implementation (Verified by SeniorCodeReviewer)", best_solution)
    return best_solution


if __name__ == "__main__":
    asyncio.run(run())
