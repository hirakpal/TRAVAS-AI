"""Hotel tools for Atithi - now backed by LIVE Google Places (New) + RAG.

Replaces the old mock-hotel dataset. search_hotels fetches real hotels for the
destination from Google Places and vector-re-ranks them against the traveler's
stated preferences. Tool NAMES are unchanged so the agent prompt and the
has_ever_searched grounding trigger keep working.
"""

from typing import List, Dict, Any

from data import live_rag, live_places


class SearchHotelsTool:
    name = "search_hotels"
    description = (
        "Search for real, currently-listed hotels in a destination via Google Places. "
        "Pass the destination and (optionally) the traveler's preferences as free text "
        "(budget words, area, vibe, must-have amenities) - results are grounded in live "
        "verified data and ranked to match those preferences."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "Destination city/place (required)"},
            "query": {
                "type": "string",
                "description": "Traveler preferences as free text, e.g. 'mid-range near the beach with a pool'. Optional.",
            },
        },
        "required": ["city"],
    }

    @staticmethod
    def execute(city: str, query: str = "", **_) -> Dict[str, Any]:
        result = live_rag.search("hotels", city, need=query or "")
        return {**result, "hotels": result.get("results", [])}


class GetHotelDetailsTool:
    name = "get_hotel_details"
    description = "Get full details (hours, contact, reviews, rating) for one hotel by its Google Places id."
    input_schema = {
        "type": "object",
        "properties": {"place_id": {"type": "string", "description": "Google Places id from a prior search result"}},
        "required": ["place_id"],
    }

    @staticmethod
    def execute(place_id: str, **_) -> Dict[str, Any]:
        res = live_places.place_details(place_id)
        if not res.get("ok"):
            return {"success": False, "message": res.get("reason", "not found")}
        return {"success": True, "hotel": res.get("place")}


HOTEL_TOOLS = {
    "search_hotels": SearchHotelsTool,
    "get_hotel_details": GetHotelDetailsTool,
}


def list_tools() -> List[str]:
    return list(HOTEL_TOOLS.keys())
