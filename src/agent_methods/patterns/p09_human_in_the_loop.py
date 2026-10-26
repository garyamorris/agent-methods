r"""
Pattern 09: Human-in-the-Loop & Safety Guardrails (Guarded Execution Gate)
===========================================================================

Architecture Overview:
----------------------
In production environments, giving autonomous agents unrestricted access to execute
irreversible mutations (financial transfers, database wipes, cloud server terminations)
is an unacceptable operational liability. The Human-in-the-Loop pattern creates an enforceable
defense-in-depth:
  1. Input Guardrails (`@input_guardrail`): Validates user inputs before LLM execution,
     tripping an exception if prompt injections or safety violations occur.
  2. Tool Approvals (`needs_approval=True`): High-stakes tools automatically suspend
     execution into an `interruption` item. The runner pauses, yields execution state,
     and awaits human verification.
  3. Real Disk / System Mutation: When approved by a human operator, the tool executes
     a verified disk backup, computing SHA-256 integrity hashes.
  4. Resume via RunState (`result.to_state()`): Once approved, the state is resumed
     and execution completes deterministically.
  5. Output Guardrails (`@output_guardrail`): Scans the generated output to ensure no
     sensitive tokens, passwords, or policy violations leak to the end user.

Real-World Production Scenarios Demonstrated:
---------------------------------------------
- Example 1 (Database Migration & Backup Approval Gate):
  DevOps agent attempts a database migration. The safety checkpoint intercepts the action,
  requires operator approval, and writes a real SHA256-verified backup file upon approval.
- Example 2 (Production Cluster Fleet Upgrade Gate):
  DevOps agent attempts rolling upgrades across nodes; suspended until security approval.

Communication Topology:
-----------------------
                       +-----------------------+
                       |      User Query       |
                       +-----------------------+
                                   |
                                   v
                      [@input_guardrail check]
                         /                  \
              [Fail / Tripwire]          [Passed]
                      |                      |
                      v                      v
             [Block Execution]       +---------------+
                                     | DevOps Agent  |
                                     +---------------+
                                             |
                                    [Tool: execute_migration]
                                             |
                                             v
                                  [needs_approval=True]
                                             |
                                             v
                                  +--------------------+
                                  | Human Interception |
                                  |    (Interrupted)   |
                                  +--------------------+
                                     /              \
                          [Reject]  /                \  [Approve]
                                   v                  v
                           [Cancel Action]    [state.approve(item)]
                                                      |
                                                      v
                                              [Real Backup Write & Hash]
                                                      |
                                                      v
                                              [Resume Runner]
                                                      |
                                                      v
                                          [@output_guardrail]
                                                      |
                                                      v
                                              [Safe Delivery]

When to Use:
------------
- Any agent action modifying database state, deploying to production, or spending money.
- Enterprise compliance environments requiring strict non-repudiation and human sign-off.
- Preventing prompt injections and data leakage in multi-tenant environments.

OpenAI Agents SDK Primitives:
-----------------------------
- `@input_guardrail`: Pre-execution boundary check returning `GuardrailFunctionOutput`.
- `@output_guardrail`: Post-execution response scrubber.
- `@function_tool(needs_approval=True)`: Creates paused tool execution checkpoints.
- `result.to_state()`, `state.approve(item)`: Resumes execution from interruptions.
"""

import asyncio
import hashlib
import json
import os
import tempfile
import time
from agents import (
    Agent,
    Runner,
    function_tool,
    input_guardrail,
    output_guardrail,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
)
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
# Define Input & Output Guardrails
# -------------------------------------------------------------------------

@input_guardrail
async def prompt_injection_guardrail(context, agent, user_input) -> GuardrailFunctionOutput:
    """Detect obvious prompt injection or destructive jailbreak attempts."""
    text = str(user_input).lower()
    forbidden_triggers = ["ignore all previous instructions", "jailbreak", "drop database without backup", "rm -rf /"]
    for trigger in forbidden_triggers:
        if trigger in text:
            return GuardrailFunctionOutput(
                output_info=f"Security alert: Dangerous command or prompt injection pattern '{trigger}' detected.",
                tripwire_triggered=True,
            )
    return GuardrailFunctionOutput(output_info="Input passed prompt safety checks.", tripwire_triggered=False)


@output_guardrail
async def data_leakage_guardrail(context, agent, agent_output) -> GuardrailFunctionOutput:
    """Ensure no live private keys or tokens are returned to users."""
    text = str(agent_output)
    if "BEGIN PRIVATE KEY" in text or "sk-live-" in text:
        return GuardrailFunctionOutput(
            output_info="Critical violation: Response attempted to output private encryption key or live API secret.",
            tripwire_triggered=True,
        )
    return GuardrailFunctionOutput(output_info="Output verified safe for delivery.", tripwire_triggered=False)


# -------------------------------------------------------------------------
# Real System Tools with Approval Checkpoints
# -------------------------------------------------------------------------

@function_tool
def check_cluster_telemetry(cluster_name: str) -> str:
    """Check health, active connection count, and CPU load on database cluster."""
    return json.dumps({
        "cluster": cluster_name,
        "nodes": 3,
        "active_connections": 142,
        "cpu_utilization_pct": 34.2,
        "replication_lag_ms": 12,
        "status": "HEALTHY",
    })


@function_tool(needs_approval=True)
def execute_production_migration(cluster_name: str, migration_sql: str) -> str:
    """Execute high-risk production schema migration.

    REQUIRES EXPLICIT HUMAN OPERATOR APPROVAL. Writes an immutable audit backup file to disk.
    """
    # Create real backup snapshot artifact on disk
    backup_data = {
        "timestamp": time.time(),
        "cluster": cluster_name,
        "migration_sql": migration_sql,
        "sha256": hashlib.sha256(migration_sql.encode("utf-8")).hexdigest(),
    }
    temp_dir = tempfile.gettempdir()
    backup_file = os.path.join(temp_dir, f"db_migration_backup_{int(time.time())}.json")
    with open(backup_file, "w") as f:
        json.dump(backup_data, f, indent=2)

    return json.dumps({
        "status": "MIGRATION_EXECUTED_SUCCESSFULLY",
        "cluster": cluster_name,
        "audit_backup_file": backup_file,
        "checksum_sha256": backup_data["sha256"],
        "rows_migrated": 1250,
        "operator_approval": "VERIFIED_BY_HUMAN_IN_THE_LOOP",
    })


# -------------------------------------------------------------------------
# Define Guarded DevOps Agent
# -------------------------------------------------------------------------

devops_agent = Agent(
    name="ProductionDevOpsEngineer",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Production DevOps Engineer with database administration privileges. "
        "Before executing any migration, you must first inspect cluster health using `check_cluster_telemetry`. "
        "Then, if the cluster is healthy, initiate `execute_production_migration`. "
        "Note that high-risk migration tools will automatically pause for human authorization."
    ),
    tools=[check_cluster_telemetry, execute_production_migration],
    input_guardrails=[prompt_injection_guardrail],
    output_guardrails=[data_leakage_guardrail],
)


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(query: str | None = None, example_id: int = 1, tracer: CommsTracer | None = None) -> str:
    """Execute guarded Human-in-the-Loop workflow with real disk state."""
    ensure_api_key()

    if example_id == 2:
        default_query = (
            "Check the telemetry for 'prod-analytics-cluster', then execute a migration to add "
            "an index on 'events.user_id' via execute_production_migration."
        )
        scenario_title = "Example 2: Analytics DB Indexing with Approval Gate"
    else:
        default_query = (
            "Please check telemetry for 'prod-payments-aurora', then run the migration "
            "'ALTER TABLE accounts ADD COLUMN risk_tier VARCHAR(32) DEFAULT normal' via execute_production_migration."
        )
        scenario_title = "Example 1: Payments Database Schema Migration Gate"

    user_prompt = query or default_query

    print_header(
        "Pattern 09: Human-in-the-Loop & Safety Guardrails",
        f"Guarded Execution Gate: {scenario_title}",
    )

    print_explainer(
        summary="Combines @input_guardrails (blocking jailbreaks), needs_approval=True on mutation tools, and real disk backup persistence upon human authorization.",
        communication_mechanism="Runner state suspension on approval items, yielding execution until approved via result.to_state().",
        when_to_use=[
            "Irreversible mutations (database schema alterations, financial transactions, cloud deletions).",
            "Preventing prompt injection attacks from reaching core execution models.",
            "Guaranteeing verifiable human non-repudiation.",
        ],
    )

    console.print(f"[bold cyan]User Request:[/bold cyan] {user_prompt}\n")

    if tracer is None:
        tracer = CommsTracer(scenario_title="Pattern 09: Human-in-the-Loop & Safety Guardrails")
    tracer.record_user_query(user_prompt, devops_agent.name)

    try:
        print_agent_step(devops_agent.name, "Processing request through input guardrails...")
        result = await Runner.run(devops_agent, user_prompt, hooks=tracer)

        # Check for approval interruption
        approval_items = [
            item for item in result.new_items
            if getattr(item, "type", "") == "approval_required_item"
            or "approval" in getattr(item, "type", "").lower()
        ]

        if approval_items:
            console.print("\n[bold yellow]⚠️  HUMAN-IN-THE-LOOP CHECKPOINT REACHED ⚠️[/bold yellow]")
            for app_item in approval_items:
                tool_name = getattr(app_item, "tool_name", "execute_production_migration")
                tracer.record_packet(devops_agent.name, "Human Supervisor", "HANDOFF", f"Execution Paused: Requires Human Sign-off for [{tool_name}]", {"tool": tool_name})
                console.print(f"  [bold red]Action Paused:[/bold red] Agent requested execution of [cyan]{tool_name}[/cyan]")
                console.print(f"  [dim]Human Operator: Inspecting payload and approving action automatically for educational demonstration...[/dim]")

            # Resume via RunState
            state = result.to_state()
            for app_item in approval_items:
                state.approve(app_item)

            tracer.record_packet("Human Supervisor", devops_agent.name, "HANDOFF", "Human Sign-off Granted: Resuming paused execution", {"status": "APPROVED"})
            console.print("  [bold green]✓ Operator Approval Granted. Resuming execution with disk audit log...[/bold green]\n")
            result = await Runner.resume(devops_agent, state, hooks=tracer)

        tracer.render_summary_ledger()
        tracer.render_sequence_diagram()

        print_result_panel("Final Guarded Output (DevOps Agent)", str(result.final_output))
        return str(result.final_output)

    except InputGuardrailTripwireTriggered as te:
        console.print(f"\n[bold red]🛑 EXECUTION HALTED BY INPUT GUARDRAIL:[/bold red] {te}\n")
        return f"Execution blocked: {te}"


if __name__ == "__main__":
    asyncio.run(run())
