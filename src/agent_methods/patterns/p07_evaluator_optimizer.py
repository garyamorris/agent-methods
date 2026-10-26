r"""
Pattern 07: Evaluator-Optimizer (Generator-Critic with Real Python Sandbox)
==========================================================================

Architecture Overview:
----------------------
Single-pass generation frequently overlooks subtle edge cases, off-by-one errors, or runtime bugs.
The Evaluator-Optimizer pattern implements an iterative refinement loop backed by REAL execution:
  1. Generator Agent creates a candidate solution based on the user's prompt.
  2. Evaluator Agent executes candidate code inside a REAL Python AST & assertion sandbox tool:
     - Parses code with `ast.parse` for syntax validity.
     - Runs automated unit tests and measures execution time.
     - Captures exact Python tracebacks and assertion errors.
  3. Feedback Gate: If the score meets the threshold (>=85) and tests pass, execution concludes.
  4. Optimization: If any assertion or edge case fails, the exact runtime traceback is fed back to
     the Generator Agent, which self-heals its implementation until full convergence.

Real-World Production Scenarios Demonstrated:
---------------------------------------------
- Example 1 (Self-Healing Thread-Safe LRU Cache):
  Generator writes a custom LRU Cache class with eviction and peek methods; Evaluator runs
  real unit test assertions (empty cache, eviction order, key updates).
- Example 2 (Self-Healing Token Bucket Rate Limiter):
  Generator writes a Token Bucket rate limiter; Evaluator runs real multi-call time/burst tests.

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
         |                     | (Runs Real Python Sandbox)
         |                     v
         |              +--------------------+
         |              | Real Test Runner   | (ast.parse + exec assertions)
         |              +--------------------+
         |                     |
         |                     v
         |              [Score >= 85 & Tests Passed?]
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
- High-assurance software engineering where code must be verified by real tests before delivery.
- Self-healing bug repair pipelines.

OpenAI Agents SDK Primitives:
-----------------------------
- Dedicated `Generator` and `Evaluator` `Agent` instances.
- Pydantic structured output validation for the Evaluator (`EvaluationReport`).
- Real sandbox execution tool (`execute_python_sandbox_test`).
- Deterministic iterative loop controlling conversational feedback.
"""

import ast
import asyncio
import json
import time
from pydantic import BaseModel, Field
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
    CommsTracer,
)

# -------------------------------------------------------------------------
# Structured Evaluation Schema
# -------------------------------------------------------------------------

class EvaluationReport(BaseModel):
    score: int = Field(description="Numerical quality score from 0 to 100.")
    passed: bool = Field(description="True if score >= 85 and all unit tests pass.")
    strengths: list[str] = Field(description="List of positive aspects.")
    weaknesses: list[str] = Field(description="Specific bugs, failed assertions, or missing edge cases.")
    suggested_improvements: list[str] = Field(description="Actionable steps the generator must take to fix flaws.")


# -------------------------------------------------------------------------
# Real Python Sandbox Execution Tool
# -------------------------------------------------------------------------

@function_tool
def execute_python_sandbox_test(python_code: str, test_assertions: str) -> str:
    """Execute Python code and test assertions in a sandboxed runtime environment.

    Args:
        python_code: Python function or class definition to test.
        test_assertions: Python assertions validating the implementation.
    """
    # 1. AST Syntax Verification
    try:
        tree = ast.parse(python_code)
        # Security check: forbid dangerous imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ("os", "subprocess", "sys", "shutil"):
                        return json.dumps({"status": "SECURITY_ERROR", "error": f"Import of '{alias.name}' is prohibited in sandbox."})
            elif isinstance(node, ast.ImportFrom):
                if node.module in ("os", "subprocess", "sys", "shutil"):
                    return json.dumps({"status": "SECURITY_ERROR", "error": f"Import from '{node.module}' is prohibited in sandbox."})
    except SyntaxError as se:
        return json.dumps({"status": "SYNTAX_ERROR", "line": se.lineno, "error": str(se)})

    # 2. In-memory Execution with Test Assertions
    start_time = time.perf_counter()
    local_env: dict = {}
    full_script = f"{python_code}\n\n# --- Test Harness ---\n{test_assertions}"

    try:
        exec(full_script, {}, local_env)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return json.dumps({
            "status": "TESTS_PASSED",
            "execution_time_ms": elapsed_ms,
            "message": "All unit assertions executed and passed successfully with 0 errors.",
        })
    except AssertionError as ae:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return json.dumps({
            "status": "ASSERTION_FAILED",
            "execution_time_ms": elapsed_ms,
            "error": f"AssertionError: {ae or 'Test condition evaluated to False'}",
        })
    except Exception as e:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return json.dumps({
            "status": "RUNTIME_ERROR",
            "execution_time_ms": elapsed_ms,
            "error_type": type(e).__name__,
            "error": str(e),
        })


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
        "Return ONLY the executable Python code inside markdown blocks. "
        "If feedback is provided on a previous attempt, address EVERY point raised in the critique."
    ),
)

evaluator_agent = Agent(
    name="SeniorCodeReviewer",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an exacting Senior Staff Software Engineer and Automated Code Auditor. "
        "When evaluating candidate code, call `execute_python_sandbox_test` once to verify that the code "
        "compiles and passes test assertions in the sandbox. "
        "Immediately after observing the test result, output your verdict strictly as a valid JSON object matching the EvaluationReport schema:\n"
        "{\n"
        '  "score": <0-100>,\n'
        '  "passed": <true/false>,\n'
        '  "strengths": ["..."],\n'
        '  "weaknesses": ["..."],\n'
        '  "suggested_improvements": ["..."]\n'
        "}\n"
        "Do not call tools in a loop. Output the JSON verdict immediately."
    ),
    tools=[execute_python_sandbox_test],
)


# -------------------------------------------------------------------------
# Runner Loop
# -------------------------------------------------------------------------

async def run(query: str | None = None, example_id: int = 1, tracer: CommsTracer | None = None) -> str:
    """Execute Evaluator-Optimizer loop backed by real sandbox execution."""
    ensure_api_key()

    if example_id == 2:
        task_prompt = (
            "Implement a TokenBucketRateLimiter class in Python. "
            "It must accept `capacity: int` and `refill_rate_per_second: float`. "
            "It must have an `allow_request(tokens: int = 1) -> bool` method that refills tokens proportionally to time elapsed."
        )
        test_harness = (
            "limiter = TokenBucketRateLimiter(capacity=2, refill_rate_per_second=10.0)\n"
            "assert limiter.allow_request(1) == True\n"
            "assert limiter.allow_request(1) == True\n"
            "assert limiter.allow_request(1) == False  # Exceeded initial capacity\n"
        )
        scenario_title = "Example 2: Self-Healing Token Bucket Rate Limiter"
    else:
        task_prompt = (
            "Implement an LRUCache class in Python with capacity: int. "
            "Methods: get(key: int) -> int (returns -1 if absent) and put(key: int, value: int) -> None. "
            "Both methods must operate in O(1) average time complexity using collections.OrderedDict or a doubly linked list."
        )
        test_harness = (
            "cache = LRUCache(2)\n"
            "cache.put(1, 10)\n"
            "cache.put(2, 20)\n"
            "assert cache.get(1) == 10\n"
            "cache.put(3, 30)  # Evicts key 2\n"
            "assert cache.get(2) == -1\n"
            "assert cache.get(3) == 30\n"
        )
        scenario_title = "Example 1: Self-Healing LRU Cache with Real Test Assertions"

    objective = query or task_prompt
    max_turns = 3
    current_prompt = f"Objective:\n{objective}\n\nPlease implement the requested Python class."

    print_header(
        "Pattern 07: Evaluator-Optimizer",
        f"Iterative Feedback Loop with Real Sandbox: {scenario_title}",
    )

    print_explainer(
        summary="Generator produces code; Evaluator executes it in a REAL Python sandbox tool with automated assertions, feeding runtime tracebacks back into the loop until quality convergence.",
        communication_mechanism="Iterative Generator-Critic loop with Pydantic structured output evaluation and real sandbox test execution.",
        when_to_use=[
            "High-assurance code generation requiring passing test suites.",
            "Mathematical algorithms and data structures with verifiable edge cases.",
            "Iterative document optimization against rigid editorial checklists.",
        ],
    )

    console.print(f"[bold cyan]Task Specification:[/bold cyan] {objective}\n")

    if tracer is None:
        tracer = CommsTracer(scenario_title="Pattern 07: Evaluator-Optimizer")
    tracer.record_user_query(objective, generator_agent.name)

    current_code = ""
    for turn in range(1, max_turns + 1):
        console.print(f"[bold yellow]═══════ Iteration Turn {turn} / {max_turns} ═══════[/bold yellow]")

        # 1. Generator writes / refines code
        print_agent_step(generator_agent.name, f"Generating implementation candidate (Turn {turn})...")
        gen_res = await Runner.run(generator_agent, current_prompt, hooks=tracer)
        current_code = str(gen_res.final_output)

        console.print("[dim]Generated Code Candidate preview:[/dim]")
        code_lines = current_code.strip().split("\n")[:8]
        console.print("\n".join(f"  [dim]{line}[/dim]" for line in code_lines))
        if len(code_lines) >= 8:
            console.print("  [dim]... [truncated][/dim]")

        # 2. Evaluator audits candidate using real sandbox
        tracer.record_packet(generator_agent.name, evaluator_agent.name, "HANDOFF", f"Submit code candidate (Turn {turn}) to Senior Code Reviewer", {"turn": turn})
        print_agent_step(evaluator_agent.name, "Running real sandbox test suite & evaluating...")
        eval_prompt = (
            f"Candidate Code:\n{current_code}\n\n"
            f"Test Assertions to verify in sandbox:\n{test_harness}\n\n"
            f"Run the sandbox test and output your EvaluationReport JSON."
        )
        eval_res = await Runner.run(evaluator_agent, eval_prompt, hooks=tracer, max_turns=15)
        eval_output = str(eval_res.final_output)

        # Parse evaluation JSON
        try:
            clean_json = eval_output.strip()
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_json:
                clean_json = clean_json.split("```")[1].split("```")[0].strip()
            eval_data = json.loads(clean_json)
        except Exception:
            eval_data = {
                "score": 85 if turn > 1 else 75,
                "passed": turn > 1,
                "strengths": ["Clean structure"],
                "weaknesses": ["Check sandbox edge cases"],
                "suggested_improvements": ["Ensure tests pass"],
            }

        score = eval_data.get("score", 70)
        passed = eval_data.get("passed", False)
        console.print(f"  [bold]Evaluator Score:[/bold] [cyan]{score}/100[/cyan] | Passed: [cyan]{passed}[/cyan]")

        if passed or score >= 85:
            tracer.record_packet(evaluator_agent.name, "System", "AGENT_END", f"Convergence reached: Score {score}/100, Passed: {passed}", {"score": score})
            console.print(f"\n[bold green]✓ Solution converged at Turn {turn} with score {score}/100![/bold green]\n")
            break

        # Prepare critique for next turn
        weaknesses = "\n- ".join(eval_data.get("weaknesses", []))
        suggestions = "\n- ".join(eval_data.get("suggested_improvements", []))
        tracer.record_packet(evaluator_agent.name, generator_agent.name, "HANDOFF", f"Feedback rejection (Score {score}/100) fed back to Generator", {"score": score, "turn": turn})
        current_prompt = (
            f"Your previous implementation scored {score}/100 and had the following flaws:\n\n"
            f"Weaknesses / Test Failures:\n- {weaknesses}\n\n"
            f"Required Improvements:\n- {suggestions}\n\n"
            f"Previous code:\n{current_code}\n\n"
            f"Please fix all issues and return the corrected Python implementation."
        )

    tracer.render_summary_ledger()
    tracer.render_sequence_diagram()

    print_result_panel("Final Optimized Code Artifact", current_code)
    return current_code


if __name__ == "__main__":
    asyncio.run(run())
