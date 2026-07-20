"""Transport tools for Safar - live multi-source.

  - search_flights        -> LIVE flights via data/live_flights.py (SearchApi
    Google Flights, with Aviationstack fallback for airlines/schedule).
  - search_local_transport -> LIVE local options via Google Places + RAG
    (data/live_rag.py): car rental, transit stations, etc. at the destination.
  - search_trains         -> honestly reports "unavailable": neither flights
    source covers rail. Wiring a rail API is the remaining follow-up.

Tool names are unchanged so the agent prompt and has_ever_searched trigger keep
working.
"""

from typing import List, Dict, Any

from data import live_rag, live_flights


_TRAINS_UNAVAILABLE = (
    "Verified train schedules and fares are not available from the current data sources "
    "(SearchApi Google Flights and Aviationstack cover flights, not rail). Tell the "
    "traveler plainly you can't provide verified train options right now and suggest the "
    "national rail site. Do NOT invent train numbers, times, or prices."
)


class SearchFlightsTool:
    name = "search_flights"
    description = (
        "Find real flights between two cities. Uses SearchApi Google Flights (priced "
        "options) with an Aviationstack fallback (airlines/schedule). Pass origin and "
        "destination cities, and the outbound date in YYYY-MM-DD if known."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "departure_city": {"type": "string", "description": "Origin city (e.g. Bangalore)"},
            "arrival_city": {"type": "string", "description": "Destination city (e.g. Singapore)"},
            "outbound_date": {
                "type": "string",
                "description": "Outbound date in YYYY-MM-DD, if known. Optional.",
            },
        },
        "required": ["departure_city", "arrival_city"],
    }

    @staticmethod
    def execute(departure_city: str = "", arrival_city: str = "", outbound_date: str = "", **_) -> Dict[str, Any]:
        result = live_flights.search_flights(departure_city, arrival_city, outbound_date or None)
        return {**result, "flights": result.get("results", [])}


class SearchTrainsTool:
    name = "search_trains"
    description = (
        "Attempt to find trains between two cities. NOTE: verified train inventory is not "
        "available from the current data source - this returns an honest 'unavailable' so "
        "you never fabricate train details."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "departure_city": {"type": "string", "description": "Origin city"},
            "arrival_city": {"type": "string", "description": "Destination city"},
        },
        "required": ["departure_city", "arrival_city"],
    }

    @staticmethod
    def execute(departure_city: str = "", arrival_city: str = "", **_) -> Dict[str, Any]:
        return {"success": False, "message": _TRAINS_UNAVAILABLE, "results": []}


class SearchLocalTransportTool:
    name = "search_local_transport"
    description = (
        "Search for real local transport options at a destination via Google Places - "
        "car rental, transit stations, and similar. Pass the destination and optionally "
        "what the traveler needs (e.g. 'airport transfer', 'self-drive car rental')."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "Destination city/place (required)"},
            "query": {"type": "string", "description": "What they need, e.g. 'car rental near the airport'. Optional."},
        },
        "required": ["city"],
    }

    @staticmethod
    def execute(city: str, query: str = "", **_) -> Dict[str, Any]:
        result = live_rag.search("transport", city, need=query or "")
        return {**result, "transport_options": result.get("results", [])}


TRANSPORT_TOOLS = {
    "search_flights": SearchFlightsTool,
    "search_trains": SearchTrainsTool,
    "search_local_transport": SearchLocalTransportTool,
}


def list_tools() -> List[str]:
    return list(TRANSPORT_TOOLS.keys())
