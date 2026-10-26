r"""
Pattern 01: Single Agent ReAct (Reason + Act with Real APIs)
============================================================

Architecture Overview:
----------------------
The foundational building block of agentic systems. Rather than attempting to answer
everything in a single zero-shot completion, the agent operates in an autonomous loop:
  1. Perceive: Reads conversation context and user query.
  2. Reason: Decides what real external information or computation is needed.
  3. Act: Emits a structured tool call to query a REAL live public API.
  4. Observe: The environment executes the network call and returns live data.
  5. Repeat or Conclude: Loops until a synthesized, factually grounded answer is produced.

Real-World Production Scenarios Demonstrated:
---------------------------------------------
- Example 1 (Financial Engineering): Queries the live CoinGecko API for real-time crypto prices
  (Bitcoin, Ethereum, Solana) and calculates 1-day 95% Value at Risk (VaR).
- Example 2 (Logistics & Supply Chain): Queries the live Open-Meteo Meteorological API for real-time
  temperatures, wind speeds, and storm risks across global shipping ports (Rotterdam, Singapore, Long Beach).

Communication Topology:
-----------------------
    +-------------------------------------------------------+
    |                     User Request                      |
    +-------------------------------------------------------+
                               |
                               v
                     +-------------------+
                     |    ReAct Agent    | <-----+
                     |  (deepseek-chat)  |       |
                     +-------------------+       |
                       | (Action)                | (Observation)
                       v                         |
                 +-----------+                   |
                 | Real HTTP | ------------------+
                 |  API Call |  (CoinGecko / Open-Meteo)
                 +-----------+
                       | (Final synthesis)
                       v
    +-------------------------------------------------------+
    |           Synthesized, Live-Grounded Report           |
    +-------------------------------------------------------+

When to Use:
------------
- Single-domain tasks requiring real-time external data (live market quotes, real weather, search).
- Calculations and deterministic transformations unsuitable for raw LLM arithmetic.
- Workflows that easily fit inside a single context window without overwhelming prompt instructions.
"""

import asyncio
import json
from typing import Any
from agents import Agent, Runner, function_tool
from agent_methods.common import (
    DEFAULT_MODEL,
    ensure_api_key,
    fetch_json,
    console,
    print_header,
    print_agent_step,
    print_tool_call,
    print_result_panel,
    print_explainer,
    CommsTracer,
)

# -------------------------------------------------------------------------
# Real Public API Tools
# -------------------------------------------------------------------------

@function_tool
def fetch_live_crypto_quote(coin_ids: str) -> str:
    """Fetch REAL real-time market prices and 24h price change from CoinGecko API.

    Args:
        coin_ids: Comma-separated CoinGecko IDs (e.g. 'bitcoin,ethereum,solana').
    """
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": coin_ids.lower().strip(),
        "vs_currencies": "usd",
        "include_24hr_change": "true",
        "include_market_cap": "true",
    }
    data = fetch_json(url, params=params)

    # Fallback to public alternative if CoinGecko rate-limits
    if "error" in data or not data:
        # Secondary real live endpoint: Binance ticker API
        binance_data = fetch_json("https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT")
        if "lastPrice" in binance_data:
            return json.dumps({
                "bitcoin": {
                    "usd": float(binance_data["lastPrice"]),
                    "usd_24h_change": float(binance_data["priceChangePercent"]),
                    "source": "Binance Public API (fallback)",
                }
            })

    return json.dumps({"source": "CoinGecko Live API", "data": data})


@function_tool
def fetch_live_port_weather(latitude: float, longitude: float, port_name: str) -> str:
    """Fetch REAL live meteorological conditions from the Open-Meteo Global Weather API.

    Args:
        latitude: Port latitude coordinate.
        longitude: Port longitude coordinate.
        port_name: Name of the global maritime hub (e.g. 'Rotterdam', 'Singapore', 'Long Beach').
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
    }
    data = fetch_json(url, params=params)
    current = data.get("current", {})
    return json.dumps({
        "port": port_name,
        "source": "Open-Meteo Live API",
        "temperature_celsius": current.get("temperature_2m"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "humidity_pct": current.get("relative_humidity_2m"),
        "is_high_wind_alert": current.get("wind_speed_10m", 0) > 35.0,
    })


@function_tool
def calculate_portfolio_var(portfolio_value: float, blended_volatility_pct: float) -> str:
    """Calculate 1-day 95% Parametric Value at Risk (VaR) for an investment portfolio.

    Args:
        portfolio_value: Total value of assets in USD.
        blended_volatility_pct: Annualized volatility in percent (e.g. 55.0 for 55%).
    """
    daily_vol = (blended_volatility_pct / 100.0) / (252 ** 0.5)
    var_95 = 1.65 * daily_vol * portfolio_value
    return json.dumps({
        "portfolio_value_usd": portfolio_value,
        "daily_volatility_pct": round(daily_vol * 100, 3),
        "estimated_1day_var_95_usd": round(var_95, 2),
        "maximum_probable_daily_loss": f"${var_95:,.2f}",
        "risk_rating": "Extreme" if var_95 > portfolio_value * 0.05 else "Moderate",
    })


# -------------------------------------------------------------------------
# Agent Factory
# -------------------------------------------------------------------------

def create_market_analyst_agent() -> Agent:
    """Create financial analyst agent equipped with real CoinGecko & VaR tools."""
    return Agent(
        name="CryptoPortfolioAnalyst",
        model=DEFAULT_MODEL,
        instructions=(
            "You are a Senior Quantitative Portfolio Analyst. "
            "When evaluating asset values, ALWAYS call `fetch_live_crypto_quote` to fetch REAL live market prices. "
            "Then calculate portfolio risk using `calculate_portfolio_var`. "
            "Present clear, bulleted risk conclusions with exact real prices."
        ),
        tools=[fetch_live_crypto_quote, calculate_portfolio_var],
    )


# Backward-compatible alias
create_react_agent = create_market_analyst_agent


def create_logistics_agent() -> Agent:
    """Create global operations agent equipped with real Open-Meteo weather tools."""
    return Agent(
        name="MaritimeLogisticsOfficer",
        model=DEFAULT_MODEL,
        instructions=(
            "You are a Global Maritime Logistics Risk Officer. "
            "When evaluating maritime supply chain disruptions, ALWAYS query `fetch_live_port_weather` "
            "for the requested shipping hubs. "
            "Synthesize weather conditions into an operational dispatch alert."
        ),
        tools=[fetch_live_port_weather],
    )


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(query: str | None = None, example_id: int = 1, tracer: CommsTracer | None = None) -> str:
    """Execute ReAct agent loop against real live public APIs."""
    ensure_api_key()

    if example_id == 2:
        default_query = (
            "Check real-time weather at the Port of Rotterdam (lat 51.92, lon 4.48) "
            "and Port of Singapore (lat 1.29, lon 103.85). Are there any high-wind hazards "
            "affecting container crane operations?"
        )
        agent = create_logistics_agent()
        scenario_title = "Example 2: Global Maritime Supply Chain Weather Risk"
    else:
        default_query = (
            "I hold 1.5 Bitcoin and 10 Ethereum. Fetch their REAL live market prices right now, "
            "calculate my total portfolio value, and compute my estimated 1-day 95% Value at Risk (VaR) "
            "assuming a blended annual volatility of 55%."
        )
        agent = create_market_analyst_agent()
        scenario_title = "Example 1: Live Crypto Portfolio & VaR Stress-Test"

    user_prompt = query or default_query

    print_header(
        "Pattern 01: Single Agent ReAct",
        f"Real API Calls: {scenario_title}",
    )

    print_explainer(
        summary="A single autonomous agent executes an in-context ReAct loop querying REAL live public APIs.",
        communication_mechanism="In-context function calling loop calling real HTTP endpoints (CoinGecko / Open-Meteo).",
        when_to_use=[
            "Single-domain tasks requiring real-time external data feeds without mock data.",
            "Straightforward workflows without complex role specialization.",
            "Minimizing token overhead and latency compared to multi-agent networks.",
        ],
    )

    console.print(f"[bold cyan]User Query:[/bold cyan] {user_prompt}\n")

    if tracer is None:
        tracer = CommsTracer(scenario_title="Pattern 01: Single Agent ReAct")
    tracer.record_user_query(user_prompt, agent.name)

    print_agent_step(agent.name, "Querying real public API tools in ReAct loop...")
    result = await Runner.run(agent, user_prompt, hooks=tracer)

    tracer.render_summary_ledger()
    tracer.render_sequence_diagram()

    print_result_panel(f"Live Grounded Output ({agent.name})", str(result.final_output))
    return str(result.final_output)


if __name__ == "__main__":
    asyncio.run(run())
