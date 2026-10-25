"""
Pattern 02: Router / Triage Dispatcher (Star Topology)
======================================================

Architecture Overview:
----------------------
In enterprise systems, forcing a single agent to possess every prompt instruction and tool
leads to prompt bloat, hallucination, tool collisions, and high token costs.
The Router (or Triage) pattern separates concerns:
  1. A lightweight "Front Door" Router agent analyzes the user's intent.
  2. The Router immediately executes a handoff to a specialized domain agent.
  3. The specialist takes ownership of the conversation and resolves the issue.

Communication Topology:
-----------------------
                           +-------------------+
                           |    User Query     |
                           +-------------------+
                                     |
                                     v
                           +-------------------+
                           |   Triage Router   |
                           +-------------------+
                                     |
                +--------------------+--------------------+
                | (handoff)          | (handoff)          | (handoff)
                v                    v                    v
      +-------------------+ +-------------------+ +-------------------+
      | BillingSpecialist | | TechnicalSupport  | |  SalesSpecialist  |
      +-------------------+ +-------------------+ +-------------------+
                |                    |                    |
                v                    v                    v
         [process_refund]    [run_diagnostics]    [calculate_quote]
                |                    |                    |
                +--------------------+--------------------+
                                     |
                                     v
                           +-------------------+
                           |  Final Specialist |
                           |     Response      |
                           +-------------------+

When to Use:
------------
- Multi-domain platforms (Customer Support, IT Service Desks, E-commerce).
- When specialists need vastly different system instructions, system prompts, or toolsets.
- Keeping context clean by not leaking billing tools to technical support agents.

OpenAI Agents SDK Primitives:
-----------------------------
- `Agent(handoffs=[agent_a, agent_b, agent_c])`: Declares available handoff targets.
- The SDK automatically creates handoff tools for each target agent and transfers conversation control.
- `result.last_agent`: Identifies which specialist handled the query.
"""

import asyncio
import json
from agents import Agent, Runner, function_tool
from agent_methods.common import (
    DEFAULT_MODEL,
    ensure_api_key,
    console,
    print_header,
    print_agent_step,
    print_tool_call,
    print_handoff,
    print_result_panel,
    print_explainer,
)

# -------------------------------------------------------------------------
# Specialist Domain Tools
# -------------------------------------------------------------------------

@function_tool
def process_refund(order_id: str, amount_usd: float) -> str:
    """Process a refund for an erroneous or disputed charge.

    Args:
        order_id: The order identifier (e.g. ORD-9812).
        amount_usd: Amount to refund in USD.
    """
    return json.dumps({
        "status": "APPROVED",
        "order_id": order_id,
        "refunded_amount": amount_usd,
        "tx_id": "tx_ref_8829141",
        "message": f"Refund of ${amount_usd:.2f} processed to original payment method.",
    })


@function_tool
def run_system_diagnostics(service_name: str) -> str:
    """Inspect server health, API response latency, and error rates.

    Args:
        service_name: Name of the service (e.g. 'auth-service', 'api-gateway').
    """
    return json.dumps({
        "service": service_name,
        "status": "DEGRADED",
        "uptime": "99.82%",
        "current_error_rate": "4.2%",
        "active_incident": "INC-4029: High connection pool saturation detected in us-east-1.",
    })


@function_tool
def calculate_enterprise_quote(num_seats: int, tier: str) -> str:
    """Calculate discounted pricing tier for enterprise volume accounts.

    Args:
        num_seats: Number of team licenses.
        tier: License tier ('pro' or 'enterprise').
    """
    base_rate = 30 if tier.lower() == "enterprise" else 15
    discount = 0.20 if num_seats >= 50 else (0.10 if num_seats >= 20 else 0.0)
    total_monthly = num_seats * base_rate * (1 - discount)
    return json.dumps({
        "seats": num_seats,
        "tier": tier,
        "discount_applied": f"{int(discount * 100)}%",
        "total_monthly_usd": round(total_monthly, 2),
        "annual_contract_value_usd": round(total_monthly * 12, 2),
    })


# -------------------------------------------------------------------------
# Specialists & Router Setup
# -------------------------------------------------------------------------

billing_agent = Agent(
    name="BillingSpecialist",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an empathetic Billing Specialist. "
        "Help customers with refunds, invoices, subscription changes, and disputed charges. "
        "When refunding, call the `process_refund` tool."
    ),
    tools=[process_refund],
)

tech_support_agent = Agent(
    name="TechnicalSupportSpecialist",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an experienced Technical Support Engineer. "
        "Help developers debug API errors, outages, and connectivity problems. "
        "Use `run_system_diagnostics` to check real-time service health."
    ),
    tools=[run_system_diagnostics],
)

sales_agent = Agent(
    name="SalesSpecialist",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an energetic Enterprise Sales Specialist. "
        "Help prospective customers understand enterprise volume plans, licensing, and security. "
        "Use `calculate_enterprise_quote` to provide transparent pricing models."
    ),
    tools=[calculate_enterprise_quote],
)

triage_agent = Agent(
    name="TriageRouter",
    model=DEFAULT_MODEL,
    instructions=(
        "You are the frontline triage router. "
        "Determine the primary intent of the user inquiry and immediately hand off "
        "to the corresponding specialist:\n"
        "- Billing inquiries, charges, or refunds -> hand off to BillingSpecialist.\n"
        "- Technical issues, outages, bugs, or API errors -> hand off to TechnicalSupportSpecialist.\n"
        "- Pricing, enterprise plans, or bulk seats -> hand off to SalesSpecialist.\n"
        "Do not attempt to solve domain problems yourself; always hand off promptly."
    ),
    handoffs=[billing_agent, tech_support_agent, sales_agent],
)


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(query: str | None = None) -> str:
    """Execute triage routing with automatic agent handoffs."""
    ensure_api_key()

    default_query = "Our production API gateway is throwing 504 Gateway Timeouts and our webhook delivery is stalling!"
    user_prompt = query or default_query

    print_header(
        "Pattern 02: Router / Triage Dispatcher",
        "Frontline intent classifier delegating to specialized domain agents",
    )

    print_explainer(
        summary="A dispatcher router classifies user queries and hands off conversation ownership to targeted specialists.",
        communication_mechanism="Zero-shot intent classification followed by native SDK handoff (transfer of conversation state).",
        when_to_use=[
            "Large applications with distinct functional domains (Billing vs Support vs Sales).",
            "Eliminating tool overload and hallucinations from bloated agent prompts.",
            "Specialist agents requiring different personas, system instructions, or tool capabilities.",
        ],
    )

    console.print(f"[bold cyan]User Query:[/bold cyan] {user_prompt}\n")

    print_agent_step("TriageRouter", "Analyzing user intent and routing...")
    result = await Runner.run(triage_agent, user_prompt)

    # Inspect the trajectory
    for item in result.new_items:
        item_type = getattr(item, "type", type(item).__name__)
        if "handoff" in item_type.lower():
            target_agent = getattr(item, "target_agent_name", None) or getattr(item, "agent", None)
            target_name = getattr(target_agent, "name", str(target_agent))
            print_handoff("TriageRouter", target_name, "Specialist matched")
        elif item_type == "tool_call_item":
            raw = getattr(item, "raw_item", None)
            name = getattr(raw, "name", "tool")
            args = getattr(raw, "arguments", "{}")
            try:
                parsed_args = json.loads(args) if isinstance(args, str) else args
            except Exception:
                parsed_args = {"raw": args}
            print_tool_call(name, parsed_args)

    print_agent_step("System", f"Final responding agent: [bold cyan]{result.last_agent.name}[/bold cyan]")
    print_result_panel(f"Response from {result.last_agent.name}", str(result.final_output))
    return str(result.final_output)


if __name__ == "__main__":
    asyncio.run(run())
