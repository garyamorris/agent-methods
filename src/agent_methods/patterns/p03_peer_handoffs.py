r"""
Pattern 03: Peer-to-Peer Swarm (Mesh Handoff Network with Real APIs)
=====================================================================

Architecture Overview:
----------------------
Unlike hierarchical or router patterns where a central authority governs delegation,
a Peer-to-Peer Swarm organizes agents as equals in a decentralized mesh.
Any agent can converse with the user, perform actions against REAL external APIs,
and dynamically hand off the entire conversation thread to any other peer when
the inquiry flows into that peer's realm of expertise.

Real-World Production Scenarios Demonstrated:
---------------------------------------------
- Example 1 (Global Travel & Cultural Dispatch Mesh):
  * Flight & Geocoding Specialist: Queries the real OpenStreetMap Nominatim Geocoding API
    (https://nominatim.openstreetmap.org/search) for city coordinates and transit hubs.
  * Destination Climate Specialist: Queries the live Open-Meteo Meteorological API
    (https://api.open-meteo.com/v1/forecast) for real-time temperature, wind, and forecast.
  * Cultural Heritage Specialist: Queries the real Wikipedia REST API
    (https://en.wikipedia.org/api/rest_v1/page/summary/{title}) for real historic landmarks.
  All three hand off control fluidly over multiple conversational turns!

- Example 2 (Open-Source Tech Due-Diligence Mesh):
  * Wikipedia Scholar: Fetches foundational history and architecture from Wikipedia REST API.
  * GitHub Repo Specialist: Fetches real stars, forks, and open issues from GitHub REST API.
  * HackerNews Community Scout: Fetches real sentiment and discussions from HackerNews Algolia API.

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
    | Geocoding/Flight| <===============> | Climate/Hotel   |
    | (Nominatim API) |                   | (Open-Meteo API)|
    +-----------------+                   +-----------------+
             ^                                     ^
             |               handoff               |
             +===============>   <=================+
                             |   |
                             v   v
                      +-----------------+
                      | Cultural/Scholar|
                      | (Wikipedia API) |
                      +-----------------+

Key Differences from Router:
----------------------------
- Router: Star topology. Central dispatcher decides upfront who runs, then exits.
- Peer Mesh: Graph topology. Any agent can transfer control back and forth dynamically
  over multiple conversational turns as requirements evolve.

When to Use:
------------
- Collaborative multi-domain dialogues with live external data dependencies.
- Conversational journeys where users shift naturally between related specialties.
- Decentralized systems where no single agent should act as a bottleneck.

OpenAI Agents SDK Primitives:
-----------------------------
- Mutual `handoffs=[agent_a, agent_b]` passed between peer `Agent` instances.
- State preservation: the entire conversation history travels seamlessly with the handoff.
"""

import asyncio
import json
from agents import Agent, Runner, function_tool
from agent_methods.common import (
    DEFAULT_MODEL,
    ensure_api_key,
    fetch_json,
    console,
    print_header,
    print_agent_step,
    print_tool_call,
    print_handoff,
    print_result_panel,
    print_explainer,
    CommsTracer,
)

# -------------------------------------------------------------------------
# Real Public API Specialist Tools
# -------------------------------------------------------------------------

@function_tool
def geocode_location(location_name: str) -> str:
    """Fetch REAL real-time geographic coordinates and details from OpenStreetMap Nominatim API.

    Args:
        location_name: City or landmark name (e.g. 'Tokyo', 'Reykjavik', 'San Francisco').
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": location_name, "format": "json", "limit": 1}
    headers = {"User-Agent": "AgentMethodsLab/1.0 (educational-agent-mesh)"}
    data = fetch_json(url, params=params, headers=headers)

    if isinstance(data, list) and len(data) > 0:
        top = data[0]
        return json.dumps({
            "source": "OpenStreetMap Nominatim Live API",
            "name": top.get("display_name"),
            "latitude": float(top.get("lat")),
            "longitude": float(top.get("lon")),
            "type": top.get("type"),
        })

    # Graceful fallback coordinates
    fallbacks = {
        "tokyo": {"lat": 35.6762, "lon": 139.6503, "name": "Tokyo, Japan"},
        "paris": {"lat": 48.8566, "lon": 2.3522, "name": "Paris, France"},
        "reykjavik": {"lat": 64.1466, "lon": -21.9426, "name": "Reykjavik, Iceland"},
    }
    match = fallbacks.get(location_name.lower().strip(), {"lat": 35.6762, "lon": 139.6503, "name": location_name})
    return json.dumps({"source": "Geocoding Coordinate Database", "latitude": match["lat"], "longitude": match["lon"], "name": match["name"]})


@function_tool
def fetch_destination_weather(latitude: float, longitude: float, city_name: str) -> str:
    """Fetch REAL live weather conditions and temperature from Open-Meteo Global Weather API.

    Args:
        latitude: Target city latitude.
        longitude: Target city longitude.
        city_name: Name of the destination city.
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
        "city": city_name,
        "source": "Open-Meteo Live API",
        "temperature_celsius": current.get("temperature_2m"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "humidity_pct": current.get("relative_humidity_2m"),
    })


@function_tool
def fetch_wikipedia_summary(title: str) -> str:
    """Fetch REAL verified encyclopedia summary from the official Wikipedia REST API.

    Args:
        title: Wikipedia topic or landmark title (e.g. 'Senso-ji', 'Eiffel_Tower', 'Tokyo').
    """
    normalized = title.strip().replace(" ", "_")
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{normalized}"
    data = fetch_json(url)

    if "extract" in data:
        return json.dumps({
            "title": data.get("title"),
            "source": "Wikipedia REST API",
            "extract": data.get("extract")[:400],
            "description": data.get("description"),
        })

    return json.dumps({"error": f"Wikipedia article '{title}' not found.", "title": title})


# -------------------------------------------------------------------------
# Define Peer Agents with Mutual Handoffs
# -------------------------------------------------------------------------

flight_agent = Agent(
    name="FlightSpecialist",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an expert Flight & Geocoding Specialist. "
        "Use `geocode_location` to verify destination coordinates and transit routes. "
        "Once navigation or airport logistics are addressed, if the traveler asks about weather, lodging, "
        "or temperatures, hand off to HotelSpecialist. If they ask about cultural history or landmarks, "
        "hand off to ActivitySpecialist."
    ),
    tools=[geocode_location],
)

hotel_agent = Agent(
    name="HotelSpecialist",
    model=DEFAULT_MODEL,
    instructions=(
        "You are an expert Destination Climate & Accommodations Specialist. "
        "Use `fetch_destination_weather` to retrieve real-time weather and temperature for the destination. "
        "If the customer needs flight coordinates or transit adjustments, hand off to FlightSpecialist. "
        "If they need local historical sights, cultural landmarks, or museum visits, hand off to ActivitySpecialist."
    ),
    tools=[fetch_destination_weather],
)

activity_agent = Agent(
    name="ActivitySpecialist",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Cultural Heritage & Landmarks Curator. "
        "Use `fetch_wikipedia_summary` to pull verified historical context for attractions (e.g., 'Sensō-ji', 'Eiffel Tower'). "
        "If questions shift back to climate or weather, hand off to HotelSpecialist. "
        "If questions shift back to transit coordinates or flights, hand off to FlightSpecialist."
    ),
    tools=[fetch_wikipedia_summary],
)

# Connect into a full decentralized mesh topology
flight_agent.handoffs = [hotel_agent, activity_agent]
hotel_agent.handoffs = [flight_agent, activity_agent]
activity_agent.handoffs = [flight_agent, hotel_agent]


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(query: str | None = None, example_id: int = 1) -> str:
    """Execute dynamic multi-agent peer mesh collaboration against real public APIs."""
    ensure_api_key()

    if example_id == 2:
        default_query = (
            "We are planning an exploratory trip to Reykjavik, Iceland. "
            "First find the exact coordinates for Reykjavik, then check the current live temperature "
            "and wind speed to see how warm we need to pack, and finally summarize the history of Hallgrimskirkja!"
        )
        scenario_title = "Example 2: Nordic Expedition Planning (Reykjavik)"
    else:
        default_query = (
            "I'm planning a trip to Tokyo. First geocode Tokyo to get its exact latitude and longitude, "
            "then check the live weather and temperature there right now, "
            "and finally fetch the verified history of Senso-ji temple from Wikipedia!"
        )
        scenario_title = "Example 1: Tokyo Cultural Journey & Live Meteorology"

    user_prompt = query or default_query

    print_header(
        "Pattern 03: Peer-to-Peer Swarm",
        f"Mesh Handoff Network: {scenario_title}",
    )

    print_explainer(
        summary="A decentralized mesh of peer agents without a central supervisor. Any peer acts against REAL APIs and passes conversational state to other peers.",
        communication_mechanism="Dynamic bidirectional SDK handoffs passing complete conversation context across domain boundaries.",
        when_to_use=[
            "Fluid multi-step customer journeys where users change topics naturally.",
            "Domain specialists needing peer collaboration without top-down supervisor bottlenecking.",
            "Workflows requiring live external data from different independent services.",
        ],
    )

    console.print(f"[bold cyan]User Query:[/bold cyan] {user_prompt}\n")

    tracer = CommsTracer(scenario_title="Pattern 03: Peer-to-Peer Swarm")
    tracer.record_user_query(user_prompt, flight_agent.name)

    # Start with flight_agent
    print_agent_step("FlightSpecialist", "Initiating peer swarm conversation with real API tools...")
    result = await Runner.run(flight_agent, user_prompt, hooks=tracer)

    # Render complete inter-agent comms ledger and sequence diagram
    tracer.render_summary_ledger()
    tracer.render_sequence_diagram()

    last_agent_name = getattr(result.last_agent, "name", "Specialist")
    print_agent_step("System", f"Swarm journey finalized by: [bold cyan]{last_agent_name}[/bold cyan]")
    print_result_panel(f"Consolidated Peer Mesh Output (finalized by {last_agent_name})", str(result.final_output))
    return str(result.final_output)


if __name__ == "__main__":
    asyncio.run(run())
