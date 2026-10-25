"""
Pattern 03: Peer-to-Peer Swarm (Mesh Handoff Network)
=====================================================

Architecture Overview:
----------------------
Unlike hierarchical or router patterns where a central authority governs delegation,
a Peer-to-Peer Swarm organizes agents as equals in a decentralized mesh.
Any agent can converse with the user, perform actions, and dynamically hand off
the entire conversation thread to any other peer when the conversation flows into
another peer's realm of expertise.

Communication Topology:
-----------------------
                       +-----------------------+
                       |   Initial User Query  |
                       +-----------------------+
                                   |
                                   v
             +-------------------------------------------+
             |                                           |
             v                                           v
    +-----------------+      handoff      +-----------------+
    |  Flight Expert  | <===============> |   Hotel Expert  |
    +-----------------+                   +-----------------+
             ^                                     ^
             |               handoff               |
             +===============>   <=================+
                             |   |
                             v   v
                      +-----------------+
                      | Activity Expert |
                      +-----------------+

Key Differences from Router:
----------------------------
- Router: Star topology. Central dispatcher decides upfront who runs, then exits.
- Peer Mesh: Graph topology. Any agent can transfer control back and forth dynamically
  over multiple conversational turns as requirements evolve.

When to Use:
------------
- Collaborative multi-domain dialogues (Travel planning, Full-stack troubleshooting,
  Creative brainstorming).
- Conversational workflows where the user shifts topics fluidly between related specialties.
- When you want decentralized autonomy without an orchestrator bottleneck.

OpenAI Agents SDK Primitives:
-----------------------------
- Mutual `handoffs=[...]` passed between peer `Agent` instances.
- State preservation: the entire conversation history travels with the handoff.
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
# Peer Specialist Tools
# -------------------------------------------------------------------------

@function_tool
def search_flights(origin: str, destination: str, date: str) -> str:
    """Find available non-stop and one-stop flights between city pairs.

    Args:
        origin: 3-letter airport code (e.g. SFO).
        destination: 3-letter airport code (e.g. HND or NRT).
        date: Travel date (YYYY-MM-DD).
    """
    return json.dumps({
        "route": f"{origin.upper()} -> {destination.upper()}",
        "date": date,
        "recommended_flight": "NH007 (ANA 777-300ER)",
        "departure": "11:20 AM",
        "arrival": "15:30 +1 day",
        "fare_usd": 1140.0,
        "cabin": "Economy Premium",
    })


@function_tool
def book_hotel_stay(city: str, district: str, nights: int, style: str) -> str:
    """Find luxury, boutique, or traditional accommodations.

    Args:
        city: City name (e.g. Tokyo).
        district: Desired neighborhood (e.g. Asakusa, Shinjuku, Ginza).
        nights: Number of nights.
        style: Lodging style (e.g. 'ryokan', 'modern-boutique').
    """
    return json.dumps({
        "city": city,
        "property": "Ryokan Kamogawa Asakusa" if "ryokan" in style.lower() else "Park Hyatt Tokyo",
        "district": district,
        "nights": nights,
        "total_rate_usd": 320.0 * nights,
        "amenities": ["Onsen hot spring", "Kaiseki multi-course breakfast", "Tatami mats"],
    })


@function_tool
def reserve_cultural_experience(city: str, activity_type: str) -> str:
    """Reserve unique cultural experiences, dining reservations, or tours.

    Args:
        city: City name.
        activity_type: Type of experience (e.g. 'tea_ceremony', 'sushi_omakase').
    """
    return json.dumps({
        "city": city,
        "reservation": "Private Urasenke Tea Ceremony & Zen Garden Walk",
        "location": "Daitoku-ji precinct",
        "duration_hours": 2.5,
        "cost_usd": 140.0,
        "status": "Confirmed Reservation Code: ZEN-902",
    })


# -------------------------------------------------------------------------
# Define Peer Agents with Mutual Handoffs
# -------------------------------------------------------------------------

# We define empty handoff lists first to allow bidirectional circular references
flight_agent = Agent(
    name="FlightSpecialist",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an expert Flight Specialist. "
        "Search and recommend flights using `search_flights`. "
        "Once flight logistics are addressed, if the traveler asks about lodging or hotels, "
        "hand off to HotelSpecialist. If they ask about tours or cultural activities, "
        "hand off to ActivitySpecialist."
    ),
    tools=[search_flights],
)

hotel_agent = Agent(
    name="HotelSpecialist",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an expert Hotel & Accommodations Specialist. "
        "Find properties and rooms using `book_hotel_stay`. "
        "If the customer needs flight adjustments, hand off to FlightSpecialist. "
        "If they need local experiences, tours, or culinary bookings, hand off to ActivitySpecialist."
    ),
    tools=[book_hotel_stay],
)

activity_agent = Agent(
    name="ActivitySpecialist",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a local Culture & Activities Curator. "
        "Book authentic local experiences using `reserve_cultural_experience`. "
        "If questions shift back to hotels, hand off to HotelSpecialist. "
        "If questions shift back to flights, hand off to FlightSpecialist."
    ),
    tools=[reserve_cultural_experience],
)

# Connect them into a full mesh topology
flight_agent.handoffs = [hotel_agent, activity_agent]
hotel_agent.handoffs = [flight_agent, activity_agent]
activity_agent.handoffs = [flight_agent, hotel_agent]


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(query: str | None = None) -> str:
    """Execute dynamic multi-agent peer mesh collaboration."""
    ensure_api_key()

    default_query = (
        "I'm planning a 5-night trip to Tokyo next month leaving from SFO. "
        "First find me a good non-stop flight, then find a traditional Ryokan in Asakusa for 5 nights, "
        "and finally book an authentic Zen tea ceremony experience!"
    )
    user_prompt = query or default_query

    print_header(
        "Pattern 03: Peer-to-Peer Swarm",
        "Decentralized mesh topology where peers hand off control fluidly",
    )

    print_explainer(
        summary="A mesh of peer agents without a central supervisor. Any peer can act and pass conversational state to other peers.",
        communication_mechanism="Dynamic, bidirectional SDK handoffs passing complete conversation context across domain boundaries.",
        when_to_use=[
            "Fluid multi-step customer journeys where users change topics naturally.",
            "Domain specialists needing peer collaboration without top-down bottlenecking.",
            "Building modular, decentralized agent networks.",
        ],
    )

    console.print(f"[bold cyan]User Query:[/bold cyan] {user_prompt}\n")

    # Start with FlightSpecialist
    print_agent_step("FlightSpecialist", "Initiating peer swarm conversation...")
    result = await Runner.run(flight_agent, user_prompt)

    # Trace tool calls and handoffs
    for item in result.new_items:
        item_type = getattr(item, "type", type(item).__name__)
        if "handoff" in item_type.lower():
            target = getattr(item, "target_agent_name", None) or getattr(item, "agent", None)
            target_name = getattr(target, "name", str(target))
            print_handoff("Peer", target_name, "Contextual handoff")
        elif item_type == "tool_call_item":
            raw = getattr(item, "raw_item", None)
            name = getattr(raw, "name", "tool")
            args = getattr(raw, "arguments", "{}")
            try:
                parsed_args = json.loads(args) if isinstance(args, str) else args
            except Exception:
                parsed_args = {"raw": args}
            print_tool_call(name, parsed_args)

    print_agent_step("System", f"Swarm journey finalized by: [bold cyan]{result.last_agent.name}[/bold cyan]")
    print_result_panel(f"Consolidated Trip Plan (from {result.last_agent.name})", str(result.final_output))
    return str(result.final_output)


if __name__ == "__main__":
    asyncio.run(run())
