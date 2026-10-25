r"""
Pattern 09: Human-in-the-Loop & Safety Guardrails
=================================================

Architecture Overview:
----------------------
In production environments, giving autonomous agents unrestricted access to execute
irreversible mutations (financial transfers, database wipes, cloud server terminations)
is a massive liability. The Human-in-the-Loop pattern creates an enforceable defense-in-depth:
  1. Input Guardrails (`@input_guardrail`): Validates user inputs before LLM execution,
     tripping an exception if prompt injections or safety violations occur.
  2. Tool Approvals (`needs_approval=True`): High-stakes tools automatically suspend
     execution into an `interruption` item. The runner pauses, yields execution state,
     and awaits human verification.
  3. Resume via RunState (`result.to_state()`): Once approved by a human operator, the
     state is resumed and execution completes deterministically.
  4. Output Guardrails (`@output_guardrail`): Scans the generated output to ensure no
     sensitive tokens, passwords, or policy violations leak to the end user.

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
                                    [Tool: drop_table]
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
- `@input_guardrail`: Pre-execution boundary check with `GuardrailFunctionOutput`.
- `@output_guardrail`: Post-execution response scrubber.
- `@function_tool(needs_approval=True)`: Creates paused tool execution checkpoints.
- `result.to_state()`, `state.approve(item)`: Resumes execution from interruptions.
"""

import asyncio
import json
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
)

# -------------------------------------------------------------------------
# Define Input & Output Guardrails
# -------------------------------------------------------------------------

@input_guardrail
async def prompt_injection_guardrail(context, agent, user_input) -> GuardrailFunctionOutput:
    """Detect obvious prompt injection or jailbreak attempts."""
    text = str(user_input).lower()
    forbidden_triggers = ["ignore all previous instructions", "jailbreak", "bypass safety"]
    for trigger in forbidden_triggers:
        if trigger in text:
            return GuardrailFunctionOutput(
                output_info=f"Security alert: Malicious prompt injection pattern '{trigger}' detected.",
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
    return GuardrailFunctionOutput(output_info="Output passed data privacy checks.", tripwire_triggered=False)


# -------------------------------------------------------------------------
# Tools: Safe vs Sensitive (Requiring Human Approval)
# -------------------------------------------------------------------------

@function_tool
def get_cluster_status(cluster_id: str) -> str:
    """Safe read-only operation: returns cluster node health and utilization."""
    return json.dumps({
        "cluster_id": cluster_id,
        "nodes": 12,
        "healthy_nodes": 12,
        "cpu_utilization": "68%",
        "region": "us-east-1",
    })


@function_tool(needs_approval=True)
def execute_database_migration(database_name: str, migration_script: str) -> str:
    """HIGH-RISK ACTION: Executes destructive database schema mutation or data migration.

    Requires explicit human approval before execution.
    """
    return json.dumps({
        "status": "APPLIED_SUCCESSFULLY",
        "database": database_name,
        "migration": migration_script,
        "records_affected": 48200,
        "audit_log_id": "audit_mig_773918",
    })


# -------------------------------------------------------------------------
# Define Guarded Agent
# -------------------------------------------------------------------------

devops_agent = Agent(
    name="DevOpsReliabilityEngineer",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an automated DevOps SRE assistant. "
        "Help engineers check cluster status and run database migrations. "
        "When asked to apply a migration, invoke `execute_database_migration`."
    ),
    tools=[get_cluster_status, execute_database_migration],
    input_guardrails=[prompt_injection_guardrail],
    output_guardrails=[data_leakage_guardrail],
)


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(query: str | None = None, auto_approve: bool = True) -> str:
    """Execute guarded agent loop demonstrating human interruption and approval."""
    ensure_api_key()

    default_query = "Please apply database migration '2026_drop_legacy_auth_tables.sql' to production DB 'prod_users_v3'."
    user_prompt = query or default_query

    print_header(
        "Pattern 09: Human-in-the-Loop & Safety Guardrails",
        "Enforcing safety boundaries, prompt injection traps, and human approval checkpoints",
    )

    print_explainer(
        summary="A defense-in-depth pattern where input/output guardrails protect boundaries and critical tools pause for human approval.",
        communication_mechanism="Execution interruption: the Runner suspends when `needs_approval=True`, returning a resumable `RunState`.",
        when_to_use=[
            "Destructive actions (financial transactions, database migrations, deleting resources).",
            "Preventing prompt injections, jailbreaks, and sensitive credential leakage.",
            "Audited enterprise environments where human accountability is non-negotiable.",
        ],
    )

    console.print(f"[bold cyan]DevOps Request:[/bold cyan] {user_prompt}\n")

    try:
        print_agent_step("DevOpsReliabilityEngineer", "Evaluating input through input guardrails and starting run...")
        initial_result = await Runner.run(devops_agent, user_prompt)
    except InputGuardrailTripwireTriggered as e:
        console.print(f"[bold red]⛔ Input Guardrail Tripwire Triggered:[/bold red] {e}")
        return f"Blocked: {e}"

    # Check for human approval interruptions
    if initial_result.interruptions:
        print_agent_step("System", f"⚠️  Execution PAUSED: {len(initial_result.interruptions)} tool call(s) require human approval!", style="bold yellow")
        for item in initial_result.interruptions:
            raw = getattr(item, "raw_item", None)
            tool_name = getattr(raw, "name", "tool")
            args = getattr(raw, "arguments", "{}")
            console.print(f"    [bold red]🛑 PENDING SENSITIVE ACTION:[/bold red] [bold yellow]{tool_name}[/bold yellow]({args})")

        if auto_approve:
            console.print("\n    [bold green]✓ Human Operator Decision: [APPROVED via automated audit policy][/bold green]\n")
            state = initial_result.to_state()
            for item in initial_result.interruptions:
                state.approve(item)

            print_agent_step("System", "Resuming Runner with approved RunState...")
            resumed_result = await Runner.run(devops_agent, state)
            print_result_panel("Final Action Confirmation", str(resumed_result.final_output))
            return str(resumed_result.final_output)
        else:
            console.print("\n    [bold red]✗ Action rejected by human operator.[/bold red]\n")
            return "Operation aborted by user."
    else:
        print_result_panel("DevOps Output", str(initial_result.final_output))
        return str(initial_result.final_output)


if __name__ == "__main__":
    asyncio.run(run())
