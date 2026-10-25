r"""
Pattern 11: Dynamic Plan-and-Solve (Planner + Re-planning Execution Loop)
========================================================================

Architecture Overview:
----------------------
For multi-step, long-horizon objectives, static execution plans fail the moment step 2 or 3
encounters unexpected errors, missing data, or new discoveries.
The Dynamic Plan-and-Solve pattern implements a closed-loop control system:
  1. Planner Agent decomposes a complex objective into an initial directed task list.
  2. Executor Agent executes the current active step using domain tools.
  3. Replanner / Monitor Agent inspects the step output:
     - Marks completed tasks as DONE.
     - Detects deviations or obstacles.
     - Dynamically amends, inserts, or re-orders remaining steps based on live reality.
  4. Loop terminates when the replanner verifies all criteria are satisfied.

Communication Topology:
-----------------------
    +-------------------------------------------------------+
    |                    Complex Objective                  |
    +-------------------------------------------------------+
                               |
                               v
                     +--------------------+
                     |   Planner Agent    |  (Creates initial Plan)
                     +--------------------+
                               |
         +-------------------->v<-----------------------+
         |           +--------------------+             |
         |           |   Plan State       |             |
         |           |   [Step 1: DONE]   |             |
         |           |   [Step 2: ACTIVE] |             |
         |           |   [Step 3: QUEUED] |             |
         |           +--------------------+             |
         |                     |                        |
         |                     v                        |
         |           +--------------------+             |
         |           |   Executor Agent   |             |
         |           |   (Tool Execution) |             |
         |           +--------------------+             |
         |                     |                        |
         |                     v                        |
         |           +--------------------+             |
         |           |  Replanner Agent   |             |
         |           +--------------------+             |
         |                     |                        |
         |                     v                        |
         |             [All Tasks Done?]                |
         |                /         \                   |
         +---- [NO: Replan]          +----> [YES]       |
                                              |         |
                                              v         |
                                    +--------------------+
                                    | Final Consolidated |
                                    |  Deliverable Dossier|
                                    +--------------------+

When to Use:
------------
- Long-horizon workflows (software migration, multi-repository code refactoring, scientific research).
- High-uncertainty environments where later steps depend on discoveries made during earlier steps.
- Mitigating catastrophic drift and hallucinations in autonomous task completion.

OpenAI Agents SDK Primitives:
-----------------------------
- Dedicated `Planner`, `Executor`, and `Replanner` `Agent` instances.
- Pydantic structured models representing the evolving Plan state.
- Closed-loop runner coordination iterating through dynamic task states.
"""

import asyncio
import json
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
)

# -------------------------------------------------------------------------
# Dynamic Plan State Models
# -------------------------------------------------------------------------

class PlanStep(BaseModel):
    step_id: int
    description: str
    status: str = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED, BLOCKED
    result_summary: str | None = None


class ExecutionPlan(BaseModel):
    objective: str
    steps: list[PlanStep] = Field(default_factory=list)
    is_complete: bool = False


# -------------------------------------------------------------------------
# Execution Tools
# -------------------------------------------------------------------------

@function_tool
def inspect_legacy_codebase(module_name: str) -> str:
    """Inspect legacy code module for deprecated APIs, sync I/O, and type debt."""
    return json.dumps({
        "module": module_name,
        "lines_of_code": 1420,
        "sync_calls_found": ["requests.get", "time.sleep", "sync_db_query"],
        "deprecated_packages": ["urllib3<1.26", "pydantic<2.0"],
        "risk_level": "HIGH",
    })


@function_tool
def run_automated_test_suite(target: str) -> str:
    """Run regression unit and integration tests against a refactored target."""
    return json.dumps({
        "target": target,
        "total_tests": 48,
        "passed": 46,
        "failed": 2,
        "failures": ["test_async_timeout_fallback", "test_connection_pool_saturation"],
        "coverage": "91.4%",
    })


@function_tool
def deploy_canary_slice(version: str, traffic_pct: int) -> str:
    """Deploy canary deployment to staging/production slice."""
    return json.dumps({
        "version": version,
        "traffic_routed": f"{traffic_pct}%",
        "error_rate_delta": "0.00%",
        "canary_status": "HEALTHY",
    })


# -------------------------------------------------------------------------
# Define Agents
# -------------------------------------------------------------------------

planner_agent = Agent(
    name="ChiefArchitectPlanner",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an Elite Software Transformation Planner. "
        "Analyze the user's objective and formulate an initial 3-step execution plan. "
        "Return your plan strictly as a JSON object matching this schema:\n"
        "{\n"
        '  "steps": [\n'
        '    {"step_id": 1, "description": "Step 1 details..."},\n'
        '    {"step_id": 2, "description": "Step 2 details..."},\n'
        '    {"step_id": 3, "description": "Step 3 details..."}\n'
        "  ]\n"
        "}\n"
        "Keep each step clear, actionable, and testable."
    ),
)

executor_agent = Agent(
    name="EngineeringExecutor",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Staff Software Engineer executing an assigned step in the migration plan. "
        "Use your available tools (inspect_legacy_codebase, run_automated_test_suite, deploy_canary_slice) "
        "to gather findings and perform the required work. Return a crisp summary of your execution findings."
    ),
    tools=[inspect_legacy_codebase, run_automated_test_suite, deploy_canary_slice],
)

replanner_agent = Agent(
    name="AdaptiveReplanner",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an Adaptive Execution Controller. "
        "Review the original objective, the current plan, and the latest execution output. "
        "Decide whether remaining steps need adjustment or if new steps must be inserted. "
        "Return your verdict strictly as a JSON object:\n"
        "{\n"
        '  "is_complete": <true/false>,\n'
        '  "decision": "EXPLANATION OF ADJUSTMENT",\n'
        '  "next_steps": [\n'
        '    {"step_id": <int>, "description": "..."}\n'
        "  ]\n"
        "}"
    ),
)


# -------------------------------------------------------------------------
# Runner Loop
# -------------------------------------------------------------------------

async def run(objective: str | None = None, max_cycles: int = 3) -> str:
    """Execute dynamic plan-and-solve loop with adaptive replanning."""
    ensure_api_key()

    default_obj = (
        "Migrate payment-processing service from synchronous requests/urllib3 to asynchronous httpx "
        "with zero customer downtime, verify test coverage, and canary 10% traffic."
    )
    user_objective = objective or default_obj

    print_header(
        "Pattern 11: Dynamic Plan-and-Solve",
        "Adaptive closed-loop orchestration with runtime re-planning based on real observations",
    )

    print_explainer(
        summary="A planner decomposes an objective, an executor acts with tools, and a replanner continuously adapts the plan based on live findings.",
        communication_mechanism="Dynamic state controller: plan mutations drive iterative dispatch across executor and replanner agents.",
        when_to_use=[
            "Complex, multi-stage software transformations or deep technical research.",
            "Workflows where early steps reveal unknown facts that invalidate naive static plans.",
            "Autonomous agents requiring self-healing and adaptive problem solving.",
        ],
    )

    console.print(f"[bold cyan]Objective:[/bold cyan] {user_objective}\n")

    # Step 1: Formulate Initial Plan
    print_agent_step("ChiefArchitectPlanner", "Formulating initial structured migration plan...")
    plan_res = await Runner.run(planner_agent, f"OBJECTIVE:\n{user_objective}")
    raw_plan = str(plan_res.final_output)

    try:
        clean_json = raw_plan.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif clean_json.startswith("```"):
            clean_json = clean_json.split("```")[1].split("```")[0].strip()
        parsed = json.loads(clean_json)
        steps_data = parsed.get("steps", [])
    except Exception:
        steps_data = [
            {"step_id": 1, "description": "Inspect legacy payment codebase for sync dependencies."},
            {"step_id": 2, "description": "Execute regression test suite to measure baseline stability."},
            {"step_id": 3, "description": "Deploy canary slice with 10% traffic."},
        ]

    plan = ExecutionPlan(
        objective=user_objective,
        steps=[PlanStep(**s) for s in steps_data],
    )

    console.print(f"  [bold yellow]Initial Plan Formulated:[/bold yellow] {len(plan.steps)} steps.")
    for step in plan.steps:
        console.print(f"    [dim]• Step {step.step_id}: {step.description}[/dim]")
    console.print()

    # Closed-loop execution
    cycle = 1
    while cycle <= max_cycles and not plan.is_complete:
        active_step = next((s for s in plan.steps if s.status == "PENDING"), None)
        if not active_step:
            break

        active_step.status = "IN_PROGRESS"
        print_agent_step(
            f"Cycle {cycle}: EngineeringExecutor",
            f"Executing Step {active_step.step_id}: {active_step.description}",
            style="cyan",
        )

        exec_prompt = (
            f"OBJECTIVE: {plan.objective}\n\n"
            f"YOUR ASSIGNED TASK (Step {active_step.step_id}):\n{active_step.description}\n\n"
            f"Execute the task using relevant tools and return your findings."
        )
        exec_res = await Runner.run(executor_agent, exec_prompt)
        step_result = str(exec_res.final_output)
        active_step.result_summary = step_result
        active_step.status = "COMPLETED"

        print_agent_step(
            f"Cycle {cycle}: AdaptiveReplanner",
            "Evaluating execution output and adapting remaining plan...",
            style="magenta",
        )

        replan_prompt = (
            f"OBJECTIVE: {plan.objective}\n\n"
            f"STEP {active_step.step_id} EXECUTED:\n{active_step.description}\n\n"
            f"OUTPUT OBSERVED:\n{step_result}\n\n"
            f"REMAINING PENDING STEPS:\n"
            + "\n".join(f"- Step {s.step_id}: {s.description}" for s in plan.steps if s.status == "PENDING")
        )
        replan_res = await Runner.run(replanner_agent, replan_prompt)

        # Parse replanner response
        try:
            r_json = str(replan_res.final_output).strip()
            if r_json.startswith("```json"):
                r_json = r_json.split("```json")[1].split("```")[0].strip()
            elif r_json.startswith("```"):
                r_json = r_json.split("```")[1].split("```")[0].strip()
            r_data = json.loads(r_json)
            if r_data.get("is_complete"):
                plan.is_complete = True
                print_agent_step("AdaptiveReplanner", "All objectives verified satisfied! Concluding plan.", style="bold green")
                break
        except Exception:
            pass

        cycle += 1

    # Final summary
    dossier = (
        f"### Dynamic Plan Execution Report\n"
        f"- **Objective:** {plan.objective}\n"
        f"- **Cycles Run:** {cycle - 1}\n\n"
        f"#### Step Execution Trajectory:\n"
        + "\n".join(
            f"- **Step {s.step_id}** (`{s.status}`): {s.description}\n  *Outcome:* {s.result_summary[:160] if s.result_summary else 'N/A'}..."
            for s in plan.steps
        )
    )

    print_result_panel("Dynamic Plan Execution Report", dossier)
    return dossier


if __name__ == "__main__":
    asyncio.run(run())
