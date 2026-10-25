"""
Pattern 01: Single Agent ReAct (Reason + Act with Tools)
========================================================

Architecture Overview:
----------------------
The foundational building block of agentic systems. Rather than attempting to answer
everything in a single zero-shot completion, the agent operates in an autonomous loop:
  1. Perceive: Reads conversation context and user query.
  2. Reason: Decides whether external information or computation is needed.
  3. Act: Emits a structured tool call (function name and arguments).
  4. Observe: The environment executes the tool and returns the observation.
  5. Repeat or Conclude: Continues until a terminal answer can be generated.

Communication Topology:
-----------------------
    +-------------------------------------------------------+
    |                     User Request                      |
    +-------------------------------------------------------+
                               |
                               v
                     +-------------------+
                     |    ReAct Agent    | <-----+
                     |    (gpt-4o-mini)  |       |
                     +-------------------+       |
                       | (Action)                | (Observation)
                       v                         |
                 +-----------+                   |
                 | Tool Call | ------------------+
                 +-----------+
                       | (Final synthesis)
                       v
    +-------------------------------------------------------+
    |                     Final Response                    |
    +-------------------------------------------------------+

When to Use:
------------
- Single-domain tasks requiring external data (APIs, search, calculators, databases).
- Simpler workflows where multi-agent delegation overhead is unnecessary.
- Workflows that fit well inside a single context window.

OpenAI Agents SDK Primitives:
-----------------------------
- `Agent`: Encapsulates instructions, model choice, and attached tools.
- `@function_tool`: Automatically parses Python type hints and docstrings into JSON schemas.
- `Runner.run(...)`: Manages the multi-turn agent execution loop.
"""

import asyncio
import json
from typing import Any
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
# Define Tools using @function_tool
# -------------------------------------------------------------------------

@function_tool
def get_stock_price(symbol: str) -> str:
    """Fetch current market price and 24h change for a given stock symbol.

    Args:
        symbol: Ticker symbol (e.g. AAPL, NVDA, TSLA).
    """
    mock_database = {
        "AAPL": {"price": 234.50, "currency": "USD", "change_24h": "+1.2%"},
        "NVDA": {"price": 142.80, "currency": "USD", "change_24h": "+3.8%"},
        "TSLA": {"price": 268.10, "currency": "USD", "change_24h": "-2.1%"},
    }
    symbol_clean = symbol.upper().strip()
    data = mock_database.get(symbol_clean, {"price": 100.0, "currency": "USD", "change_24h": "0.0%"})
    return json.dumps({"symbol": symbol_clean, **data})


@function_tool
def calculate_risk_metric(portfolio_value: float, volatility_percentage: float) -> str:
    """Calculate Value at Risk (VaR 95% confidence interval) for a portfolio.

    Args:
        portfolio_value: Total value in USD.
        volatility_percentage: Annualized volatility (e.g. 25.0 for 25%).
    """
    # Simple parametric 1-day 95% VaR formula: 1.65 * (volatility / sqrt(252)) * value
    daily_vol = (volatility_percentage / 100.0) / (252 ** 0.5)
    var_95 = 1.65 * daily_vol * portfolio_value
    return json.dumps({
        "portfolio_value": portfolio_value,
        "daily_volatility_pct": round(daily_vol * 100, 3),
        "estimated_1day_var_95_usd": round(var_95, 2),
        "risk_rating": "Moderate" if var_95 < portfolio_value * 0.03 else "High",
    })


# -------------------------------------------------------------------------
# Agent Factory
# -------------------------------------------------------------------------

def create_react_agent() -> Agent:
    """Create a ReAct portfolio risk analyst agent."""
    return Agent(
        name="PortfolioRiskAnalyst",
        model=DEFAULT_MODEL,
        instructions=(
            "You are an analytical financial assistant. "
            "When asked about stocks and portfolio risk, ALWAYS use the provided tools "
            "to look up prices and calculate risk metrics. "
            "Synthesize your findings concisely with clear bullet points."
        ),
        tools=[get_stock_price, calculate_risk_metric],
    )


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(query: str | None = None) -> str:
    """Execute the ReAct agent loop and inspect execution items."""
    ensure_api_key()

    default_query = (
        "I hold $50,000 in NVDA and $25,000 in AAPL. "
        "What are their current prices, and what is my estimated 1-day 95% Value at Risk (VaR) "
        "assuming a blended volatility of 28% across the $75,000 total portfolio?"
    )
    user_prompt = query or default_query

    print_header(
        "Pattern 01: Single Agent ReAct",
        "Autonomous Reason + Act loop with tool calling and observation feedback",
    )

    print_explainer(
        summary="A single autonomous agent perceived by a multi-turn LLM loop that queries external tools.",
        communication_mechanism="In-context function calling loop (Perceive -> Reason -> Tool Call -> Tool Return -> Answer).",
        when_to_use=[
            "Single-domain tasks requiring dynamic calculations or API data fetching.",
            "Straightforward workflows without complex role specialization.",
            "Minimizing overhead and latency compared to multi-agent networks.",
        ],
    )

    console.print(f"[bold cyan]User Query:[/bold cyan] {user_prompt}\n")

    agent = create_react_agent()

    print_agent_step("System", "Starting ReAct loop with Runner.run()...")
    result = await Runner.run(agent, user_prompt)

    # Walk through the generated items to show what happened under the hood
    print_agent_step("System", f"Execution complete in {len(result.new_items)} execution item(s):")
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
        elif item_type == "tool_call_output_item":
            output = getattr(item, "output", "")
            console.print(f"      [dim green]↳ Output:[/dim green] [dim]{str(output)[:120]}...[/dim]")

    print_result_panel("Synthesized Agent Output", str(result.final_output))
    return str(result.final_output)


if __name__ == "__main__":
    asyncio.run(run())
